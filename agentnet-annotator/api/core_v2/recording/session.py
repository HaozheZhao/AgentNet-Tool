"""Recording session management."""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from pathlib import Path
import time
import uuid


class SessionState(Enum):
    """Recording session states."""
    IDLE = auto()
    PREPARING = auto()
    RECORDING = auto()
    PAUSED = auto()
    STOPPING = auto()
    STOPPED = auto()
    ERROR = auto()


@dataclass
class SessionMetadata:
    """Metadata for a recording session."""
    session_id: str
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    task_name: Optional[str] = None
    task_description: Optional[str] = None
    user_id: Optional[str] = None
    screen_resolution: Optional[tuple[int, int]] = None
    platform: Optional[str] = None
    version: str = "2.0"
    tags: List[str] = field(default_factory=list)
    custom_data: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration(self) -> Optional[float]:
        """Calculate session duration."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None


class RecordingSession:
    """Manages a single recording session."""
    
    def __init__(self, session_id: Optional[str] = None, 
                 recording_path: Optional[Path] = None):
        self.session_id = session_id or str(uuid.uuid4())
        self.recording_path = recording_path or Path(f"recording_{self.session_id}")
        self.state = SessionState.IDLE
        self.metadata = SessionMetadata(session_id=self.session_id)
        self._state_history: List[tuple[SessionState, float]] = []
        self._event_count = 0
        
        # Configuration
        self.natural_scrolling = True
        self.generate_window_a11y = False
        self.generate_element_a11y = True
        
        # Observers for state changes
        self._observers: List[callable] = []
    
    def add_observer(self, observer: callable) -> None:
        """Add an observer for state changes."""
        self._observers.append(observer)
    
    def remove_observer(self, observer: callable) -> None:
        """Remove an observer."""
        if observer in self._observers:
            self._observers.remove(observer)
    
    def _notify_state_change(self, old_state: SessionState, new_state: SessionState) -> None:
        """Notify observers of state changes."""
        for observer in self._observers:
            try:
                observer(self, old_state, new_state)
            except Exception:
                pass  # Don't let observer errors crash the session
    
    def set_state(self, new_state: SessionState) -> None:
        """Change session state."""
        old_state = self.state
        self.state = new_state
        timestamp = time.time()
        
        self._state_history.append((new_state, timestamp))
        
        # Update metadata based on state changes
        if new_state == SessionState.RECORDING and old_state != SessionState.PAUSED:
            self.metadata.start_time = timestamp
        elif new_state == SessionState.STOPPED and self.metadata.end_time is None:
            self.metadata.end_time = timestamp
        
        self._notify_state_change(old_state, new_state)
    
    def can_transition_to(self, new_state: SessionState) -> bool:
        """Check if transition to new state is valid."""
        valid_transitions = {
            SessionState.IDLE: [SessionState.PREPARING],
            SessionState.PREPARING: [SessionState.RECORDING, SessionState.ERROR],
            SessionState.RECORDING: [SessionState.PAUSED, SessionState.STOPPING],
            SessionState.PAUSED: [SessionState.RECORDING, SessionState.STOPPING],
            SessionState.STOPPING: [SessionState.STOPPED, SessionState.ERROR],
            SessionState.STOPPED: [SessionState.IDLE],  # Allow restart
            SessionState.ERROR: [SessionState.IDLE, SessionState.STOPPED],
        }
        
        return new_state in valid_transitions.get(self.state, [])
    
    def prepare(self) -> bool:
        """Prepare session for recording."""
        if not self.can_transition_to(SessionState.PREPARING):
            return False
        
        try:
            # Ensure recording directory exists
            self.recording_path.mkdir(parents=True, exist_ok=True)
            
            # Initialize metadata
            from ..platform import get_platform_provider
            platform_provider = get_platform_provider()
            
            self.metadata.platform = platform_provider.get_platform_name()
            self.metadata.screen_resolution = platform_provider.get_screen_size()
            
            self.set_state(SessionState.PREPARING)
            return True
        except Exception:
            self.set_state(SessionState.ERROR)
            return False
    
    def start(self) -> bool:
        """Start recording."""
        if not self.can_transition_to(SessionState.RECORDING):
            return False
        
        self.set_state(SessionState.RECORDING)
        return True
    
    def pause(self) -> bool:
        """Pause recording."""
        if not self.can_transition_to(SessionState.PAUSED):
            return False
        
        self.set_state(SessionState.PAUSED)
        return True
    
    def resume(self) -> bool:
        """Resume recording."""
        if not self.can_transition_to(SessionState.RECORDING):
            return False
        
        self.set_state(SessionState.RECORDING)
        return True
    
    def stop(self) -> bool:
        """Stop recording."""
        if not self.can_transition_to(SessionState.STOPPING):
            return False
        
        self.set_state(SessionState.STOPPING)
        # The actual stopping logic will be handled by the manager
        return True
    
    def complete(self) -> bool:
        """Mark session as completed."""
        if not self.can_transition_to(SessionState.STOPPED):
            return False
        
        self.set_state(SessionState.STOPPED)
        return True
    
    def error(self, error_message: str = "") -> None:
        """Mark session as errored."""
        self.metadata.custom_data["error_message"] = error_message
        self.set_state(SessionState.ERROR)
    
    def reset(self) -> bool:
        """Reset session to idle state."""
        if not self.can_transition_to(SessionState.IDLE):
            return False
        
        # Reset metadata
        self.metadata = SessionMetadata(session_id=self.session_id)
        self._state_history.clear()
        self._event_count = 0
        
        self.set_state(SessionState.IDLE)
        return True
    
    def increment_event_count(self) -> None:
        """Increment the event counter."""
        self._event_count += 1
    
    @property
    def event_count(self) -> int:
        """Get the current event count."""
        return self._event_count
    
    @property
    def is_active(self) -> bool:
        """Check if session is actively recording."""
        return self.state == SessionState.RECORDING
    
    @property
    def is_finished(self) -> bool:
        """Check if session is finished."""
        return self.state in [SessionState.STOPPED, SessionState.ERROR]
    
    def get_state_history(self) -> List[tuple[SessionState, float]]:
        """Get the state change history."""
        return self._state_history.copy()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary representation."""
        return {
            "session_id": self.session_id,
            "recording_path": str(self.recording_path),
            "state": self.state.name,
            "event_count": self._event_count,
            "metadata": {
                "session_id": self.metadata.session_id,
                "start_time": self.metadata.start_time,
                "end_time": self.metadata.end_time,
                "duration": self.metadata.duration,
                "task_name": self.metadata.task_name,
                "task_description": self.metadata.task_description,
                "user_id": self.metadata.user_id,
                "screen_resolution": self.metadata.screen_resolution,
                "platform": self.metadata.platform,
                "version": self.metadata.version,
                "tags": self.metadata.tags,
                "custom_data": self.metadata.custom_data,
            },
            "configuration": {
                "natural_scrolling": self.natural_scrolling,
                "generate_window_a11y": self.generate_window_a11y,
                "generate_element_a11y": self.generate_element_a11y,
            }
        }