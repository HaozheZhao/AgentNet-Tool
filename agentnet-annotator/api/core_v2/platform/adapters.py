"""Platform-specific adapter implementations."""

from typing import Dict, Any, Optional
import platform
import subprocess
import sys
from .provider import PlatformProvider


class DarwinAdapter(PlatformProvider):
    """macOS-specific implementation."""
    
    def get_platform_name(self) -> str:
        return "darwin"
    
    def get_accessibility_tree(self) -> Dict[str, Any]:
        """Get accessibility tree using macOS APIs."""
        try:
            # Import here to avoid issues on non-macOS platforms
            from core.a11y import get_accessibility_tree
            return get_accessibility_tree()
        except ImportError:
            return {"error": "Accessibility APIs not available"}
    
    def get_window_info(self) -> Dict[str, Any]:
        """Get active window info on macOS."""
        try:
            # Use AppleScript to get window info
            script = '''
            tell application "System Events"
                set frontApp to first application process whose frontmost is true
                set frontWindow to first window of frontApp
                return {name of frontApp, name of frontWindow, position of frontWindow, size of frontWindow}
            end tell
            '''
            result = subprocess.run(['osascript', '-e', script], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                # Parse the result (simplified)
                return {"raw_output": result.stdout.strip()}
            else:
                return {"error": "Failed to get window info"}
        except Exception as e:
            return {"error": str(e)}
    
    def show_notification(self, title: str, message: str, duration: int = 3) -> None:
        """Show macOS notification."""
        try:
            script = f'''
            display notification "{message}" with title "{title}"
            '''
            subprocess.run(['osascript', '-e', script], check=False)
        except Exception:
            print(f"{title}: {message}")  # Fallback to print
    
    def get_screen_size(self) -> tuple[int, int]:
        """Get screen size on macOS."""
        try:
            import pyautogui
            return pyautogui.size()
        except ImportError:
            return (1920, 1080)  # Default fallback
    
    def get_mouse_position(self) -> tuple[int, int]:
        """Get mouse position on macOS."""
        try:
            import pyautogui
            return pyautogui.position()
        except ImportError:
            return (0, 0)  # Default fallback
    
    def is_accessibility_enabled(self) -> bool:
        """Check if accessibility is enabled on macOS."""
        try:
            # This is a simplified check
            script = '''
            tell application "System Events"
                return true
            end tell
            '''
            result = subprocess.run(['osascript', '-e', script], 
                                  capture_output=True, text=True)
            return result.returncode == 0
        except Exception:
            return False
    
    def request_accessibility_permissions(self) -> bool:
        """Request accessibility permissions on macOS."""
        try:
            # Open System Preferences to Privacy & Security
            subprocess.run(['open', 'x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility'], 
                          check=False)
            return True
        except Exception:
            return False
    
    def get_running_applications(self) -> list[Dict[str, Any]]:
        """Get running applications on macOS."""
        try:
            script = '''
            tell application "System Events"
                set appList to {}
                repeat with proc in application processes
                    if background only of proc is false then
                        set end of appList to {name of proc, bundle identifier of proc}
                    end if
                end repeat
                return appList
            end tell
            '''
            result = subprocess.run(['osascript', '-e', script], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                return [{"raw_data": result.stdout.strip()}]
            else:
                return []
        except Exception:
            return []
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get macOS system information."""
        return {
            "platform": "darwin",
            "version": platform.mac_ver()[0],
            "architecture": platform.machine(),
            "python_version": sys.version,
        }


class WindowsAdapter(PlatformProvider):
    """Windows-specific implementation."""
    
    def get_platform_name(self) -> str:
        return "windows"
    
    def get_accessibility_tree(self) -> Dict[str, Any]:
        """Get accessibility tree using Windows APIs."""
        try:
            # Import here to avoid issues on non-Windows platforms
            from core.a11y import get_accessibility_tree
            return get_accessibility_tree()
        except ImportError:
            return {"error": "Accessibility APIs not available"}
    
    def get_window_info(self) -> Dict[str, Any]:
        """Get active window info on Windows."""
        try:
            import win32gui
            import win32process
            
            hwnd = win32gui.GetForegroundWindow()
            window_text = win32gui.GetWindowText(hwnd)
            class_name = win32gui.GetClassName(hwnd)
            rect = win32gui.GetWindowRect(hwnd)
            
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            
            return {
                "handle": hwnd,
                "title": window_text,
                "class_name": class_name,
                "rect": rect,
                "pid": pid,
            }
        except ImportError:
            return {"error": "Windows APIs not available"}
        except Exception as e:
            return {"error": str(e)}
    
    def show_notification(self, title: str, message: str, duration: int = 3) -> None:
        """Show Windows notification."""
        try:
            import win10toast
            toaster = win10toast.ToastNotifier()
            toaster.show_toast(title, message, duration=duration)
        except ImportError:
            print(f"{title}: {message}")  # Fallback to print
    
    def get_screen_size(self) -> tuple[int, int]:
        """Get screen size on Windows."""
        try:
            import pyautogui
            return pyautogui.size()
        except ImportError:
            return (1920, 1080)  # Default fallback
    
    def get_mouse_position(self) -> tuple[int, int]:
        """Get mouse position on Windows."""
        try:
            import pyautogui
            return pyautogui.position()
        except ImportError:
            return (0, 0)  # Default fallback
    
    def is_accessibility_enabled(self) -> bool:
        """Check if accessibility is enabled on Windows."""
        # Windows doesn't have the same accessibility permission model
        return True
    
    def request_accessibility_permissions(self) -> bool:
        """Request accessibility permissions on Windows."""
        # Not applicable on Windows
        return True
    
    def get_running_applications(self) -> list[Dict[str, Any]]:
        """Get running applications on Windows."""
        try:
            import psutil
            apps = []
            for proc in psutil.process_iter(['pid', 'name', 'exe']):
                try:
                    apps.append({
                        "pid": proc.info['pid'],
                        "name": proc.info['name'],
                        "exe": proc.info['exe'],
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            return apps
        except ImportError:
            return []
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get Windows system information."""
        return {
            "platform": "windows",
            "version": platform.version(),
            "release": platform.release(),
            "architecture": platform.machine(),
            "python_version": sys.version,
        }


class LinuxAdapter(PlatformProvider):
    """Linux-specific implementation."""
    
    def get_platform_name(self) -> str:
        return "linux"
    
    def get_accessibility_tree(self) -> Dict[str, Any]:
        """Get accessibility tree on Linux."""
        try:
            # Linux accessibility would use AT-SPI or similar
            return {"error": "Linux accessibility not implemented"}
        except Exception as e:
            return {"error": str(e)}
    
    def get_window_info(self) -> Dict[str, Any]:
        """Get active window info on Linux."""
        try:
            # Use xprop or similar X11 tools
            result = subprocess.run(['xprop', '-root', '_NET_ACTIVE_WINDOW'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                return {"raw_output": result.stdout.strip()}
            else:
                return {"error": "Failed to get window info"}
        except Exception as e:
            return {"error": str(e)}
    
    def show_notification(self, title: str, message: str, duration: int = 3) -> None:
        """Show Linux notification."""
        try:
            subprocess.run(['notify-send', title, message], check=False)
        except Exception:
            print(f"{title}: {message}")  # Fallback to print
    
    def get_screen_size(self) -> tuple[int, int]:
        """Get screen size on Linux."""
        try:
            import pyautogui
            return pyautogui.size()
        except ImportError:
            return (1920, 1080)  # Default fallback
    
    def get_mouse_position(self) -> tuple[int, int]:
        """Get mouse position on Linux."""
        try:
            import pyautogui
            return pyautogui.position()
        except ImportError:
            return (0, 0)  # Default fallback
    
    def is_accessibility_enabled(self) -> bool:
        """Check if accessibility is enabled on Linux."""
        # Linux accessibility varies by desktop environment
        return True  # Assume it's available for now
    
    def request_accessibility_permissions(self) -> bool:
        """Request accessibility permissions on Linux."""
        # Linux doesn't typically require explicit permission
        return True
    
    def get_running_applications(self) -> list[Dict[str, Any]]:
        """Get running applications on Linux."""
        try:
            import psutil
            apps = []
            for proc in psutil.process_iter(['pid', 'name', 'exe', 'cmdline']):
                try:
                    apps.append({
                        "pid": proc.info['pid'],
                        "name": proc.info['name'],
                        "exe": proc.info['exe'],
                        "cmdline": proc.info['cmdline'],
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            return apps
        except ImportError:
            return []
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get Linux system information."""
        return {
            "platform": "linux",
            "distribution": platform.linux_distribution() if hasattr(platform, 'linux_distribution') else "unknown",
            "version": platform.version(),
            "release": platform.release(),
            "architecture": platform.machine(),
            "python_version": sys.version,
        }