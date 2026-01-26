"""Core v2 - Refactored modular architecture for AgentNet."""

from .config import CoreConfig, RecordingConfig, AccessibilityConfig
from .events import EventBus, Event, EventType
from .platform import PlatformProvider, get_platform_provider

__all__ = [
    'CoreConfig',
    'RecordingConfig', 
    'AccessibilityConfig',
    'EventBus',
    'Event',
    'EventType',
    'PlatformProvider',
    'get_platform_provider',
]