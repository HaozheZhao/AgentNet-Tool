"""Action definitions and factory."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, Any, Optional, List
import time


class ActionType(Enum):
    """Types of user actions."""
    MOVE = auto()
    CLICK = auto()
    TYPE = auto()
    PRESS = auto()
    SCROLL = auto()
    DRAG = auto()
    WAIT = auto()
    SCREENSHOT = auto()


@dataclass
class ActionData:
    """Data container for action information."""
    action_type: ActionType
    timestamp: float
    element_info: Optional[Dict[str, Any]] = None
    coordinates: Optional[tuple[int, int]] = None
    text: Optional[str] = None
    key_info: Optional[Dict[str, Any]] = None
    scroll_info: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "action_type": self.action_type.name,
            "timestamp": self.timestamp,
            "element_info": self.element_info,
            "coordinates": self.coordinates,
            "text": self.text,
            "key_info": self.key_info,
            "scroll_info": self.scroll_info,
            "metadata": self.metadata,
        }


class Action(ABC):
    """Abstract base class for all actions."""
    
    def __init__(self, action_data: ActionData):
        self.data = action_data
        self.action_id = f"{action_data.action_type.name}_{int(time.time() * 1000000)}"
    
    @property
    def action_type(self) -> ActionType:
        """Get the action type."""
        return self.data.action_type
    
    @property
    def timestamp(self) -> float:
        """Get the timestamp."""
        return self.data.timestamp
    
    @abstractmethod
    def execute(self) -> bool:
        """Execute the action."""
        pass
    
    @abstractmethod
    def can_merge_with(self, other: 'Action') -> bool:
        """Check if this action can be merged with another."""
        pass
    
    @abstractmethod
    def merge_with(self, other: 'Action') -> 'Action':
        """Merge with another action."""
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert action to dictionary."""
        result = self.data.to_dict()
        result["action_id"] = self.action_id
        result["class_name"] = self.__class__.__name__
        return result


class MoveAction(Action):
    """Mouse movement action."""
    
    def __init__(self, action_data: ActionData):
        super().__init__(action_data)
        if action_data.action_type != ActionType.MOVE:
            raise ValueError("ActionData must be of type MOVE")
    
    def execute(self) -> bool:
        """Execute mouse movement."""
        if self.data.coordinates:
            try:
                import pyautogui
                x, y = self.data.coordinates
                pyautogui.moveTo(x, y)
                return True
            except ImportError:
                return False
        return False
    
    def can_merge_with(self, other: 'Action') -> bool:
        """Move actions can be merged if they're close in time."""
        if not isinstance(other, MoveAction):
            return False
        
        time_diff = abs(self.timestamp - other.timestamp)
        return time_diff < 0.1  # 100ms threshold
    
    def merge_with(self, other: 'Action') -> 'Action':
        """Merge with another move action (keep the latest position)."""
        if not self.can_merge_with(other):
            raise ValueError("Cannot merge these actions")
        
        # Use the latest timestamp and position
        if other.timestamp > self.timestamp:
            return other
        else:
            return self


class ClickAction(Action):
    """Mouse click action."""
    
    def __init__(self, action_data: ActionData):
        super().__init__(action_data)
        if action_data.action_type != ActionType.CLICK:
            raise ValueError("ActionData must be of type CLICK")
    
    def execute(self) -> bool:
        """Execute mouse click."""
        if self.data.coordinates:
            try:
                import pyautogui
                x, y = self.data.coordinates
                button = self.data.metadata.get("button", "left")
                pyautogui.click(x, y, button=button)
                return True
            except ImportError:
                return False
        return False
    
    def can_merge_with(self, other: 'Action') -> bool:
        """Click actions generally shouldn't be merged."""
        return False
    
    def merge_with(self, other: 'Action') -> 'Action':
        """Click actions don't merge."""
        raise ValueError("Click actions cannot be merged")


class TypeAction(Action):
    """Text typing action."""
    
    def __init__(self, action_data: ActionData):
        super().__init__(action_data)
        if action_data.action_type != ActionType.TYPE:
            raise ValueError("ActionData must be of type TYPE")
    
    def execute(self) -> bool:
        """Execute text typing."""
        if self.data.text:
            try:
                import pyautogui
                pyautogui.write(self.data.text)
                return True
            except ImportError:
                return False
        return False
    
    def can_merge_with(self, other: 'Action') -> bool:
        """Type actions can be merged if they're consecutive."""
        if not isinstance(other, TypeAction):
            return False
        
        time_diff = abs(self.timestamp - other.timestamp)
        return time_diff < 1.0  # 1 second threshold
    
    def merge_with(self, other: 'Action') -> 'Action':
        """Merge with another type action (concatenate text)."""
        if not self.can_merge_with(other):
            raise ValueError("Cannot merge these actions")
        
        # Create new action with concatenated text
        if other.timestamp > self.timestamp:
            new_text = (self.data.text or "") + (other.data.text or "")
            new_data = ActionData(
                action_type=ActionType.TYPE,
                timestamp=other.timestamp,
                text=new_text,
                element_info=other.data.element_info or self.data.element_info,
                metadata={**self.data.metadata, **other.data.metadata}
            )
        else:
            new_text = (other.data.text or "") + (self.data.text or "")
            new_data = ActionData(
                action_type=ActionType.TYPE,
                timestamp=self.timestamp,
                text=new_text,
                element_info=self.data.element_info or other.data.element_info,
                metadata={**other.data.metadata, **self.data.metadata}
            )
        
        return TypeAction(new_data)


class ScrollAction(Action):
    """Scroll action."""
    
    def __init__(self, action_data: ActionData):
        super().__init__(action_data)
        if action_data.action_type != ActionType.SCROLL:
            raise ValueError("ActionData must be of type SCROLL")
    
    def execute(self) -> bool:
        """Execute scroll."""
        if self.data.scroll_info:
            try:
                import pyautogui
                dx = self.data.scroll_info.get("dx", 0)
                dy = self.data.scroll_info.get("dy", 0)
                x, y = self.data.coordinates or pyautogui.position()
                pyautogui.scroll(dy, x=x, y=y)
                return True
            except ImportError:
                return False
        return False
    
    def can_merge_with(self, other: 'Action') -> bool:
        """Scroll actions can be merged if they're close in time and location."""
        if not isinstance(other, ScrollAction):
            return False
        
        time_diff = abs(self.timestamp - other.timestamp)
        if time_diff > 0.5:  # 500ms threshold
            return False
        
        # Check if coordinates are close
        if self.data.coordinates and other.data.coordinates:
            x1, y1 = self.data.coordinates
            x2, y2 = other.data.coordinates
            distance = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
            return distance < 50  # 50 pixel threshold
        
        return True
    
    def merge_with(self, other: 'Action') -> 'Action':
        """Merge with another scroll action (accumulate scroll values)."""
        if not self.can_merge_with(other):
            raise ValueError("Cannot merge these actions")
        
        # Accumulate scroll deltas
        my_scroll = self.data.scroll_info or {"dx": 0, "dy": 0}
        other_scroll = other.data.scroll_info or {"dx": 0, "dy": 0}
        
        new_scroll = {
            "dx": my_scroll.get("dx", 0) + other_scroll.get("dx", 0),
            "dy": my_scroll.get("dy", 0) + other_scroll.get("dy", 0),
        }
        
        # Use the latest timestamp and coordinates
        if other.timestamp > self.timestamp:
            coordinates = other.data.coordinates
            timestamp = other.timestamp
        else:
            coordinates = self.data.coordinates
            timestamp = self.timestamp
        
        new_data = ActionData(
            action_type=ActionType.SCROLL,
            timestamp=timestamp,
            coordinates=coordinates,
            scroll_info=new_scroll,
            element_info=other.data.element_info or self.data.element_info,
            metadata={**self.data.metadata, **other.data.metadata}
        )
        
        return ScrollAction(new_data)


class ActionFactory:
    """Factory for creating actions from action data."""
    
    _action_classes = {
        ActionType.MOVE: MoveAction,
        ActionType.CLICK: ClickAction,
        ActionType.TYPE: TypeAction,
        ActionType.SCROLL: ScrollAction,
        # Add other action types as needed
    }
    
    @classmethod
    def create_action(cls, action_data: ActionData) -> Action:
        """Create an action from action data."""
        action_class = cls._action_classes.get(action_data.action_type)
        
        if action_class is None:
            raise ValueError(f"Unknown action type: {action_data.action_type}")
        
        return action_class(action_data)
    
    @classmethod
    def register_action_class(cls, action_type: ActionType, action_class: type) -> None:
        """Register a new action class for an action type."""
        if not issubclass(action_class, Action):
            raise ValueError("Action class must inherit from Action")
        
        cls._action_classes[action_type] = action_class
    
    @classmethod
    def create_from_dict(cls, action_dict: Dict[str, Any]) -> Action:
        """Create an action from dictionary representation."""
        action_type_name = action_dict.get("action_type")
        if not action_type_name:
            raise ValueError("Missing action_type in action dictionary")
        
        try:
            action_type = ActionType[action_type_name]
        except KeyError:
            raise ValueError(f"Invalid action_type: {action_type_name}")
        
        action_data = ActionData(
            action_type=action_type,
            timestamp=action_dict.get("timestamp", time.time()),
            element_info=action_dict.get("element_info"),
            coordinates=tuple(action_dict["coordinates"]) if action_dict.get("coordinates") else None,
            text=action_dict.get("text"),
            key_info=action_dict.get("key_info"),
            scroll_info=action_dict.get("scroll_info"),
            metadata=action_dict.get("metadata", {})
        )
        
        return cls.create_action(action_data)