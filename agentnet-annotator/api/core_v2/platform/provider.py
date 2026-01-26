"""Platform provider interface and factory."""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import platform
import sys


class PlatformProvider(ABC):
    """Abstract interface for platform-specific functionality."""
    
    @abstractmethod
    def get_platform_name(self) -> str:
        """Get the platform name (darwin, windows, linux)."""
        pass
    
    @abstractmethod
    def get_accessibility_tree(self) -> Dict[str, Any]:
        """Get the accessibility tree for the current focused window."""
        pass
    
    @abstractmethod
    def get_window_info(self) -> Dict[str, Any]:
        """Get information about the current active window."""
        pass
    
    @abstractmethod
    def show_notification(self, title: str, message: str, duration: int = 3) -> None:
        """Show a system notification."""
        pass
    
    @abstractmethod
    def get_screen_size(self) -> tuple[int, int]:
        """Get the screen size as (width, height)."""
        pass
    
    @abstractmethod
    def get_mouse_position(self) -> tuple[int, int]:
        """Get the current mouse position as (x, y)."""
        pass
    
    @abstractmethod
    def is_accessibility_enabled(self) -> bool:
        """Check if accessibility permissions are enabled."""
        pass
    
    @abstractmethod
    def request_accessibility_permissions(self) -> bool:
        """Request accessibility permissions from the user."""
        pass
    
    @abstractmethod
    def get_running_applications(self) -> list[Dict[str, Any]]:
        """Get list of running applications."""
        pass
    
    @abstractmethod
    def get_system_info(self) -> Dict[str, Any]:
        """Get comprehensive system information."""
        pass


def detect_platform() -> str:
    """Detect the current platform."""
    system = platform.system().lower()
    
    if system == "darwin":
        return "darwin"
    elif system == "windows":
        return "windows"
    elif system == "linux":
        return "linux"
    else:
        raise RuntimeError(f"Unsupported platform: {system}")


def get_platform_provider(force_platform: Optional[str] = None) -> PlatformProvider:
    """Get the appropriate platform provider."""
    from .adapters import DarwinAdapter, WindowsAdapter, LinuxAdapter
    
    platform_name = force_platform or detect_platform()
    
    if platform_name == "darwin":
        return DarwinAdapter()
    elif platform_name == "windows":
        return WindowsAdapter()
    elif platform_name == "linux":
        return LinuxAdapter()
    else:
        raise RuntimeError(f"No provider available for platform: {platform_name}")