"""Event system for decoupling core components."""

from abc import ABC, abstractmethod
from enum import Enum, auto
from dataclasses import dataclass
from typing import Any, Dict, List, Callable, Optional, Type
import time
import threading
from collections import defaultdict


class EventType(Enum):
    """Types of events in the system."""
    # Recording events
    RECORDING_STARTED = auto()
    RECORDING_STOPPED = auto()
    RECORDING_PAUSED = auto()
    RECORDING_RESUMED = auto()
    
    # Input events
    MOUSE_MOVED = auto()
    MOUSE_CLICKED = auto()
    KEY_PRESSED = auto()
    SCROLL_EVENT = auto()
    
    # System events
    WINDOW_CHANGED = auto()
    APP_SWITCHED = auto()
    SCREEN_CHANGED = auto()
    
    # Processing events
    EVENT_PROCESSED = auto()
    BATCH_COMPLETED = auto()
    ERROR_OCCURRED = auto()
    
    # File events
    FILE_CREATED = auto()
    FILE_SAVED = auto()
    FILE_DELETED = auto()
    
    # A11y events
    A11Y_TREE_UPDATED = auto()
    ELEMENT_FOCUSED = auto()


@dataclass
class Event:
    """Base event class."""
    event_type: EventType
    timestamp: float
    source: str
    data: Dict[str, Any]
    event_id: Optional[str] = None
    
    def __post_init__(self):
        if self.event_id is None:
            self.event_id = f"{self.event_type.name}_{int(time.time() * 1000000)}"


class EventHandler(ABC):
    """Abstract base class for event handlers."""
    
    @abstractmethod
    def handle_event(self, event: Event) -> None:
        """Handle an event."""
        pass
    
    @abstractmethod
    def can_handle(self, event_type: EventType) -> bool:
        """Check if this handler can handle the given event type."""
        pass


class FunctionEventHandler(EventHandler):
    """Event handler that wraps a function."""
    
    def __init__(self, handler_func: Callable[[Event], None], 
                 event_types: List[EventType]):
        self.handler_func = handler_func
        self.event_types = set(event_types)
    
    def handle_event(self, event: Event) -> None:
        """Handle an event by calling the wrapped function."""
        self.handler_func(event)
    
    def can_handle(self, event_type: EventType) -> bool:
        """Check if this handler can handle the given event type."""
        return event_type in self.event_types


class EventBus:
    """Central event bus for publishing and subscribing to events."""
    
    def __init__(self):
        self._handlers: Dict[EventType, List[EventHandler]] = defaultdict(list)
        self._global_handlers: List[EventHandler] = []
        self._lock = threading.RLock()
        self._event_history: List[Event] = []
        self._max_history = 1000
    
    def subscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """Subscribe a handler to a specific event type."""
        with self._lock:
            self._handlers[event_type].append(handler)
    
    def subscribe_function(self, event_types: List[EventType], 
                          handler_func: Callable[[Event], None]) -> None:
        """Subscribe a function to handle specific event types."""
        handler = FunctionEventHandler(handler_func, event_types)
        for event_type in event_types:
            self.subscribe(event_type, handler)
    
    def subscribe_global(self, handler: EventHandler) -> None:
        """Subscribe a handler to all events."""
        with self._lock:
            self._global_handlers.append(handler)
    
    def unsubscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """Unsubscribe a handler from a specific event type."""
        with self._lock:
            if event_type in self._handlers:
                try:
                    self._handlers[event_type].remove(handler)
                except ValueError:
                    pass  # Handler not found
    
    def unsubscribe_global(self, handler: EventHandler) -> None:
        """Unsubscribe a handler from global events."""
        with self._lock:
            try:
                self._global_handlers.remove(handler)
            except ValueError:
                pass  # Handler not found
    
    def publish(self, event: Event) -> None:
        """Publish an event to all registered handlers."""
        with self._lock:
            # Add to history
            self._event_history.append(event)
            if len(self._event_history) > self._max_history:
                self._event_history.pop(0)
            
            # Get handlers for this event type
            handlers = self._handlers.get(event.event_type, [])
            
            # Add global handlers
            handlers.extend(self._global_handlers)
            
            # Handle event (outside lock to avoid blocking)
            for handler in handlers:
                try:
                    if handler.can_handle(event.event_type):
                        handler.handle_event(event)
                except Exception as e:
                    # Publish error event
                    error_event = Event(
                        event_type=EventType.ERROR_OCCURRED,
                        timestamp=time.time(),
                        source="EventBus",
                        data={
                            "original_event": event,
                            "handler": handler.__class__.__name__,
                            "error": str(e)
                        }
                    )
                    # Avoid infinite recursion by not publishing error events for error handlers
                    if event.event_type != EventType.ERROR_OCCURRED:
                        self._publish_error_event(error_event)
    
    def _publish_error_event(self, error_event: Event) -> None:
        """Publish error event without triggering more errors."""
        try:
            error_handlers = self._handlers.get(EventType.ERROR_OCCURRED, [])
            for handler in error_handlers:
                if handler.can_handle(EventType.ERROR_OCCURRED):
                    handler.handle_event(error_event)
        except Exception:
            pass  # Ignore errors in error handlers
    
    def create_event(self, event_type: EventType, source: str, 
                    data: Optional[Dict[str, Any]] = None) -> Event:
        """Create and publish a new event."""
        event = Event(
            event_type=event_type,
            timestamp=time.time(),
            source=source,
            data=data or {}
        )
        self.publish(event)
        return event
    
    def get_event_history(self, event_type: Optional[EventType] = None, 
                         limit: int = 100) -> List[Event]:
        """Get recent event history."""
        with self._lock:
            events = self._event_history[-limit:]
            if event_type:
                events = [e for e in events if e.event_type == event_type]
            return events
    
    def clear_history(self) -> None:
        """Clear event history."""
        with self._lock:
            self._event_history.clear()
    
    def get_handler_count(self, event_type: Optional[EventType] = None) -> int:
        """Get number of handlers for a specific event type or all."""
        with self._lock:
            if event_type:
                return len(self._handlers.get(event_type, []))
            else:
                total = sum(len(handlers) for handlers in self._handlers.values())
                total += len(self._global_handlers)
                return total


# Global event bus instance
_global_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """Get the global event bus instance."""
    global _global_event_bus
    if _global_event_bus is None:
        _global_event_bus = EventBus()
    return _global_event_bus


def set_event_bus(event_bus: EventBus) -> None:
    """Set the global event bus instance."""
    global _global_event_bus
    _global_event_bus = event_bus


def reset_event_bus() -> None:
    """Reset the global event bus."""
    global _global_event_bus
    _global_event_bus = None