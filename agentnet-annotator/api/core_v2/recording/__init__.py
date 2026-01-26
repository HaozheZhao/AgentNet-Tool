"""Recording system with clean separation of concerns."""

from .session import RecordingSession, SessionState
from .capture import EventCapture, MouseCapture, KeyboardCapture
from .manager import RecordingManager
from .lifecycle import SessionLifecycle

__all__ = [
    'RecordingSession',
    'SessionState', 
    'EventCapture',
    'MouseCapture',
    'KeyboardCapture',
    'RecordingManager',
    'SessionLifecycle',
]