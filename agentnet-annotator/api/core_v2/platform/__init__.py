"""Platform abstraction layer."""

from .provider import PlatformProvider, get_platform_provider
from .adapters import DarwinAdapter, WindowsAdapter, LinuxAdapter

__all__ = [
    'PlatformProvider',
    'get_platform_provider', 
    'DarwinAdapter',
    'WindowsAdapter',
    'LinuxAdapter',
]