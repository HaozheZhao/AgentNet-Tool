"""Event capture system for recording user interactions."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Callable, Any, Dict, List
from enum import Enum, auto
import time
import threading


class EventType(Enum):
    """Types of user input events."""
    MOUSE_MOVE = auto()
    MOUSE_CLICK = auto()
    MOUSE_SCROLL = auto()
    MOUSE_DRAG = auto()
    KEY_PRESS = auto()
    KEY_RELEASE = auto()
    KEY_TYPE = auto()
    WINDOW_FOCUS = auto()
    APP_SWITCH = auto()


@dataclass
class InputEvent:
    """Represents a user input event."""
    event_type: EventType
    timestamp: float
    data: Dict[str, Any]
    event_id: Optional[str] = None
    
    def __post_init__(self):
        if self.event_id is None:
            self.event_id = f"{self.event_type.name}_{int(self.timestamp * 1000000)}"


class EventCapture(ABC):
    """Abstract base class for event capture."""
    
    def __init__(self):
        self._active = False
        self._handlers: List[Callable[[InputEvent], None]] = []
        self._lock = threading.Lock()
    
    def add_handler(self, handler: Callable[[InputEvent], None]) -> None:
        """Add an event handler."""
        with self._lock:
            self._handlers.append(handler)
    
    def remove_handler(self, handler: Callable[[InputEvent], None]) -> None:
        """Remove an event handler."""
        with self._lock:
            if handler in self._handlers:
                self._handlers.remove(handler)
    
    def _emit_event(self, event: InputEvent) -> None:
        """Emit an event to all handlers."""
        with self._lock:
            handlers = self._handlers.copy()
        
        for handler in handlers:
            try:
                handler(event)
            except Exception:
                pass  # Don't let handler errors crash capture
    
    @abstractmethod
    def start_capture(self) -> bool:
        """Start capturing events."""
        pass
    
    @abstractmethod
    def stop_capture(self) -> bool:
        """Stop capturing events."""
        pass
    
    @property
    def is_active(self) -> bool:
        """Check if capture is active."""
        return self._active


class MouseCapture(EventCapture):
    """Captures mouse events."""
    
    def __init__(self, track_movement: bool = True):
        super().__init__()
        self.track_movement = track_movement
        self._mouse_listener = None
        self._last_position = None
    
    def start_capture(self) -> bool:
        """Start capturing mouse events."""
        if self._active:
            return True
        
        try:
            from pynput import mouse
            
            def on_move(x, y):
                if self.track_movement and self._active:
                    self._emit_event(InputEvent(
                        event_type=EventType.MOUSE_MOVE,
                        timestamp=time.time(),
                        data={"x": x, "y": y, "previous": self._last_position}
                    ))
                    self._last_position = (x, y)
            
            def on_click(x, y, button, pressed):
                if self._active:
                    self._emit_event(InputEvent(
                        event_type=EventType.MOUSE_CLICK,
                        timestamp=time.time(),
                        data={
                            "x": x, "y": y,
                            "button": button.name if hasattr(button, 'name') else str(button),
                            "pressed": pressed
                        }
                    ))
            
            def on_scroll(x, y, dx, dy):
                if self._active:
                    self._emit_event(InputEvent(
                        event_type=EventType.MOUSE_SCROLL,
                        timestamp=time.time(),
                        data={"x": x, "y": y, "dx": dx, "dy": dy}
                    ))
            
            self._mouse_listener = mouse.Listener(
                on_move=on_move if self.track_movement else None,
                on_click=on_click,
                on_scroll=on_scroll
            )
            
            self._mouse_listener.start()
            self._active = True
            return True
            
        except ImportError:
            return False
        except Exception:
            return False
    
    def stop_capture(self) -> bool:
        """Stop capturing mouse events."""
        if not self._active:
            return True
        
        try:
            if self._mouse_listener:
                self._mouse_listener.stop()
                self._mouse_listener = None
            
            self._active = False
            return True
        except Exception:
            return False


class KeyboardCapture(EventCapture):
    """Captures keyboard events."""
    
    def __init__(self, track_releases: bool = False):
        super().__init__()
        self.track_releases = track_releases
        self._keyboard_listener = None
    
    def start_capture(self) -> bool:
        """Start capturing keyboard events."""
        if self._active:
            return True
        
        try:
            from pynput import keyboard
            
            def on_press(key):
                if self._active:
                    key_data = self._format_key(key)
                    self._emit_event(InputEvent(
                        event_type=EventType.KEY_PRESS,
                        timestamp=time.time(),
                        data={"key": key_data, "pressed": True}
                    ))
            
            def on_release(key):
                if self._active and self.track_releases:
                    key_data = self._format_key(key)
                    self._emit_event(InputEvent(
                        event_type=EventType.KEY_RELEASE,
                        timestamp=time.time(),
                        data={"key": key_data, "pressed": False}
                    ))
            
            self._keyboard_listener = keyboard.Listener(
                on_press=on_press,
                on_release=on_release if self.track_releases else None
            )
            
            self._keyboard_listener.start()
            self._active = True
            return True
            
        except ImportError:
            return False
        except Exception:
            return False
    
    def stop_capture(self) -> bool:
        """Stop capturing keyboard events."""
        if not self._active:
            return True
        
        try:
            if self._keyboard_listener:
                self._keyboard_listener.stop()
                self._keyboard_listener = None
            
            self._active = False
            return True
        except Exception:
            return False
    
    def _format_key(self, key) -> Dict[str, Any]:
        """Format key data for storage."""
        try:
            from pynput import keyboard
            
            if hasattr(key, 'char') and key.char is not None:
                return {
                    "type": "char",
                    "value": key.char,
                    "name": key.char
                }
            else:
                return {
                    "type": "special",
                    "value": key.name if hasattr(key, 'name') else str(key),
                    "name": key.name if hasattr(key, 'name') else str(key)
                }
        except Exception:
            return {
                "type": "unknown",
                "value": str(key),
                "name": str(key)
            }


class WindowCapture(EventCapture):
    """Captures window focus and application switch events."""
    
    def __init__(self, poll_interval: float = 0.5):
        super().__init__()
        self.poll_interval = poll_interval
        self._polling_thread = None
        self._last_window = None
    
    def start_capture(self) -> bool:
        """Start capturing window events."""
        if self._active:
            return True
        
        self._active = True
        self._polling_thread = threading.Thread(target=self._poll_windows, daemon=True)
        self._polling_thread.start()
        return True
    
    def stop_capture(self) -> bool:
        """Stop capturing window events."""
        self._active = False
        if self._polling_thread:
            self._polling_thread.join(timeout=1.0)
        return True
    
    def _poll_windows(self) -> None:
        """Poll for window changes."""
        from ..platform import get_platform_provider
        
        platform_provider = get_platform_provider()
        
        while self._active:
            try:
                current_window = platform_provider.get_window_info()
                
                if current_window != self._last_window:
                    if self._last_window is not None:  # Not the first poll
                        self._emit_event(InputEvent(
                            event_type=EventType.WINDOW_FOCUS,
                            timestamp=time.time(),
                            data={
                                "previous_window": self._last_window,
                                "current_window": current_window
                            }
                        ))
                    
                    self._last_window = current_window
                
                time.sleep(self.poll_interval)
                
            except Exception:
                time.sleep(self.poll_interval)
                continue


class CompositeCapture(EventCapture):
    """Combines multiple event capture sources."""
    
    def __init__(self, captures: List[EventCapture]):
        super().__init__()
        self.captures = captures
        self._setup_forwarding()
    
    def _setup_forwarding(self) -> None:
        """Setup event forwarding from child captures."""
        for capture in self.captures:
            capture.add_handler(self._forward_event)
    
    def _forward_event(self, event: InputEvent) -> None:
        """Forward event from child capture."""
        self._emit_event(event)
    
    def start_capture(self) -> bool:
        """Start all child captures."""
        success = True
        for capture in self.captures:
            if not capture.start_capture():
                success = False
        
        self._active = success
        return success
    
    def stop_capture(self) -> bool:
        """Stop all child captures."""
        success = True
        for capture in self.captures:
            if not capture.stop_capture():
                success = False
        
        self._active = False
        return success


def create_default_capture() -> CompositeCapture:
    """Create a default composite capture with mouse, keyboard, and window capture."""
    return CompositeCapture([
        MouseCapture(track_movement=True),
        KeyboardCapture(track_releases=False),
        WindowCapture(poll_interval=0.5)
    ])