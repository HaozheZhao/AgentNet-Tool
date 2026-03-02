"""OBS service for handling OBS integration."""

import time
from typing import List, Tuple

from core.logger import logger
from core.obs_client import close_obs, is_obs_running, open_obs
from core.constants import SUCCEED, FAILED
from scripts.obs_config import enable_obs_websocket

REQUIRED_WIDTH = 1920
REQUIRED_HEIGHT = 1080


class ObsService:
    """Service for handling OBS operations."""

    def __init__(self):
        self.obs_process = None
        self._initialize_obs()

    def _initialize_obs(self) -> None:
        """Initialize OBS if not already running."""
        if not is_obs_running():
            self.obs_process = open_obs()

    def ensure_obs_running(self, max_attempts: int = 10) -> Tuple[str, str]:
        """Ensure OBS is running and ready."""
        attempt = 0
        time.sleep(1)

        while attempt < max_attempts:
            if not is_obs_running():
                time.sleep(0.5)
                attempt += 1
            else:
                return SUCCEED, "OBS is running"

        logger.warning("ObsService: Failed to start OBS")
        return FAILED, "Failed to start OBS"

    def check_recording_prerequisites(self) -> Tuple[str, str, List[str]]:
        """Check resolution and OBS connection before recording.

        Returns:
            Tuple of (status, message, warnings_list)
        """
        warnings = []

        # 1. Check screen resolution
        try:
            from screeninfo import get_monitors
            monitors = get_monitors()
            if monitors:
                monitor = monitors[0]
                screen_w, screen_h = monitor.width, monitor.height
                if screen_w != REQUIRED_WIDTH or screen_h != REQUIRED_HEIGHT:
                    warnings.append(
                        f"Screen resolution is {screen_w}x{screen_h}, but annotation "
                        f"requires {REQUIRED_WIDTH}x{REQUIRED_HEIGHT}. Please change "
                        f"your display resolution before recording."
                    )
            else:
                warnings.append("Could not detect any monitors.")
        except Exception as e:
            warnings.append(f"Could not detect screen resolution: {str(e)}")

        # 2. Check OBS WebSocket connection and output resolution
        try:
            import obsws_python as obs_ws
            test_client = obs_ws.ReqClient()
            test_client.get_version()

            # Check OBS video output resolution
            try:
                video_settings = test_client.get_video_settings()
                obs_out_w = video_settings.output_width
                obs_out_h = video_settings.output_height
                if obs_out_w != REQUIRED_WIDTH or obs_out_h != REQUIRED_HEIGHT:
                    warnings.append(
                        f"OBS output resolution is {obs_out_w}x{obs_out_h}, but annotation "
                        f"requires {REQUIRED_WIDTH}x{REQUIRED_HEIGHT}. Please change "
                        f"OBS output resolution in Settings > Video > Output (Scaled) Resolution."
                    )
            except Exception as e:
                warnings.append(f"Could not check OBS output resolution: {str(e)}")

            try:
                test_client.base_client.ws.close()
            except Exception:
                pass
        except Exception as e:
            return FAILED, f"Cannot connect to OBS WebSocket: {str(e)}", warnings

        return SUCCEED, "Prerequisites check passed", warnings

    def enable_websocket(self) -> Tuple[str, str]:
        """Enable OBS WebSocket."""
        try:
            enable_obs_websocket()
            logger.info("ObsService: OBS WebSocket enabled successfully")
            return SUCCEED, "OBS WebSocket enabled successfully"

        except Exception as e:
            logger.exception(f"ObsService: Failed to enable OBS WebSocket: {e}")
            return FAILED, f"Failed to enable OBS WebSocket: {str(e)}"

    def shutdown(self) -> None:
        """Shutdown OBS process if managed by this service."""
        try:
            if hasattr(self, "obs_process") and self.obs_process:
                close_obs(self.obs_process)
                logger.info("ObsService: OBS process closed")
        except Exception as e:
            logger.exception(f"ObsService: Error closing OBS: {e}")

    def is_running(self) -> bool:
        """Check if OBS is currently running."""
        return is_obs_running()
