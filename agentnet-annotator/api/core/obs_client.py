import os
import subprocess
import time
import threading
from platform import system

import obsws_python as obs
import psutil

from .logger import logger


def is_obs_running() -> bool:
    try:
        for process in psutil.process_iter(attrs=["pid", "name"]):
            if "obs" in process.info["name"].lower():
                return True
        return False
    except Exception:
        raise Exception("Could not check if OBS is running already. Please check manually.")


def close_obs(obs_process: subprocess.Popen):
    if obs_process:
        obs_process.terminate()
        try:
            obs_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            obs_process.kill()


def find_obs() -> str:
    common_paths = {
        "Windows": [
            "C:\\Program Files\\obs-studio\\bin\\64bit\\obs64.exe",
            "C:\\Program Files (x86)\\obs-studio\\bin\\32bit\\obs32.exe"
        ],
        "Darwin": [
            "/Applications/OBS.app/Contents/MacOS/OBS",
            "/opt/homebrew/bin/obs"
        ],
        "Linux": [
            "/usr/bin/obs",
            "/usr/local/bin/obs"
        ]
    }

    for path in common_paths.get(system(), []):
        if os.path.exists(path):
            return path
    
    try:
        if system() == "Windows":
            obs_path = subprocess.check_output("where obs", shell=True).decode().strip()
        else:
            obs_path = subprocess.check_output("which obs", shell=True).decode().strip()

        if os.path.exists(obs_path):
            return obs_path
    except subprocess.CalledProcessError:
        pass

    return "obs"

def open_obs() -> subprocess.Popen:
    try:
        obs_path = find_obs()
        if system() == "Windows":
            # you have to change the working directory first for OBS to find the correct locale on windows
            original_dir = os.getcwd()
            try:
                os.chdir(os.path.dirname(obs_path))
                obs_executable = os.path.basename(obs_path)
                subprocess.Popen([obs_executable, "--startreplaybuffer", "--minimize-to-tray"])
            finally:
                os.chdir(original_dir)
    except Exception:
        raise Exception("Failed to find OBS, please open OBS manually.")

class OBSAlreadyRecordingError(Exception):
    pass

def is_obs_recording(obs_client) -> bool:
    try:
        recording_status = obs_client.req_client.get_record_status()
        return recording_status.output_active
    except Exception as e:
        print(f"Error checking OBS recording status: {e}")
        return False
        
class OBSClient:
    """
    Controls the OBS client via the OBS websocket.
    Sets all the correct settings for recording.
    """
    
    def __init__(
        self,
        recording_path: str,
        metadata: dict,
        fps=30,
        output_filename: str = "video.mp4",
    ):
        self.metadata = metadata
        
        self.req_client = obs.ReqClient()
        self.event_client = obs.EventClient()
        
        self.record_state_events = {}
        self._record_stopped_event = threading.Event()

        def on_record_state_changed(data):
            output_state = data.output_state
            print("record state changed:", output_state)
            if output_state not in self.record_state_events:
                self.record_state_events[output_state] = []
            self.record_state_events[output_state].append(time.perf_counter())
            # Signal when OBS has fully stopped recording (file is finalized)
            if output_state == "OBS_WEBSOCKET_OUTPUT_STOPPED":
                self._record_stopped_event.set()

        self.event_client.callback.register(on_record_state_changed)

        self.old_profile = self.req_client.get_profile_list().current_profile_name

        profiles = self.req_client.get_profile_list().profiles
        logger.warning(profiles)
        if "computer_tracker" not in profiles:
            self.req_client.create_profile("computer_tracker")
        else:
            self.req_client.set_current_profile("computer_tracker")
            
        """if "computer_tracker" not in self.req_client.get_profile_list().profiles:
            self.req_client.create_profile("computer_tracker")
        else:
            self.req_client.set_current_profile("computer_tracker")
            self.req_client.create_profile("temp")
            self.req_client.remove_profile("temp")
            self.req_client.set_current_profile("computer_tracker")"""

        base_width = metadata["screen_width"]
        base_height = metadata["screen_height"]

        if metadata["system"] == "Darwin":
            # for retina displays
            # TODO: check if external displays are messed up by this
            base_width *= 2
            base_height *= 2

        # Set active video resolution directly (profile params alone don't update the live pipeline).
        # This fails if OBS has an active output (recording, replay buffer, virtual camera).
        # In that case, stop all outputs first, then retry.
        try:
            self.req_client.set_video_settings(
                numerator=fps,
                denominator=1,
                base_width=base_width,
                base_height=base_height,
                out_width=base_width,
                out_height=base_height,
            )
        except Exception:
            logger.warning("OBSClient: set_video_settings failed (output active), stopping outputs and retrying")
            self._stop_all_outputs()
            try:
                self.req_client.set_video_settings(
                    numerator=fps,
                    denominator=1,
                    base_width=base_width,
                    base_height=base_height,
                    out_width=base_width,
                    out_height=base_height,
                )
            except Exception as e:
                logger.warning(f"OBSClient: set_video_settings retry failed: {e}, continuing with profile params only")
        logger.info(f"OBSClient: set video settings to {base_width}x{base_height} @ {fps}fps")

        # Also persist to profile config for consistency
        self.req_client.set_profile_parameter("Video", "BaseCX", str(base_width))
        self.req_client.set_profile_parameter("Video", "BaseCY", str(base_height))
        self.req_client.set_profile_parameter("Video", "OutputCX", str(base_width))
        self.req_client.set_profile_parameter("Video", "OutputCY", str(base_height))

        self.req_client.set_profile_parameter("AdvOut", "RescaleRes", f"{base_width}x{base_height}")
        self.req_client.set_profile_parameter("AdvOut", "RecRescaleRes", f"{base_width}x{base_height}")
        self.req_client.set_profile_parameter("AdvOut", "FFRescaleRes", f"{base_width}x{base_height}")

        self.req_client.set_profile_parameter("Video", "FPSCommon", str(fps))
        self.req_client.set_profile_parameter("Video", "FPSInt", str(fps))
        self.req_client.set_profile_parameter("Video", "FPSNum", str(fps))
        self.req_client.set_profile_parameter("Video", "FPSDen", "1")

        self.req_client.set_profile_parameter("SimpleOutput", "RecFormat2", "mp4")
        self.req_client.set_profile_parameter("AdvOut", "RecFormat2", "mp4")

        bitrate = int(_get_bitrate_mbps(base_width, base_height, fps=fps) * 1000 / 50) * 50
        self.req_client.set_profile_parameter("SimpleOutput", "VBitrate", str(bitrate))
        
        # do this in order to get pause & resume
        self.req_client.set_profile_parameter("SimpleOutput", "RecQuality", "Small")


        self.req_client.set_profile_parameter("SimpleOutput", "FilePath", recording_path)
        self.req_client.set_profile_parameter("AdvOut", "RecFilePath", recording_path)


        if system() != "Linux":
            input_lists = [inp["inputName"] for inp in self.req_client.get_input_list().inputs]
            for inp_name in input_lists:
                try:
                    self.req_client.set_input_mute(inp_name, True)
                except Exception as e:
                    # In case there is no Mic/Aux input, this will throw an error
                    logger.warning(f"Could not mute {inp_name} input: {e}")

    def _stop_all_outputs(self):
        """Stop any active OBS outputs so video settings can be changed."""
        try:
            status = self.req_client.get_record_status()
            if status.output_active:
                self.req_client.stop_record()
                time.sleep(0.5)
        except Exception:
            pass
        try:
            status = self.req_client.get_replay_buffer_status()
            if status.output_active:
                self.req_client.stop_replay_buffer()
                time.sleep(0.3)
        except Exception:
            pass
        try:
            status = self.req_client.get_virtual_cam_status()
            if status.output_active:
                self.req_client.stop_virtual_cam()
        except Exception:
            pass

    def start_recording(self):
        self.req_client.start_record()

    def stop_recording(self):
        self._record_stopped_event.clear()
        self.req_client.stop_record()
        # Wait for OBS to fully finalize the MP4 file (flush buffers, write
        # moov atom, close file handle).  On Windows this can take several
        # seconds for large recordings.  Without this wait the file may be
        # incomplete, locked, or missing when the reducer / uploader runs.
        # Poll in 10-second intervals with progress logging so we can
        # distinguish "still writing" from "truly stuck".
        elapsed = 0
        while not self._record_stopped_event.wait(timeout=10):
            elapsed += 10
            logger.info(f"OBSClient: waiting for OBS to finalize video file... ({elapsed}s elapsed)")
        logger.info(f"OBSClient: OBS video file finalized after ~{elapsed}s")
        self.req_client.set_current_profile(self.old_profile) # restore old profile

    def pause_recording(self):
        self.req_client.pause_record()
    
    def resume_recording(self):
        self.req_client.resume_record()
   
def _get_bitrate_mbps(width: int, height: int, fps=30) -> float:
    """
    Gets the YouTube recommended bitrate in Mbps for a given resolution and framerate.
    Refer to https://support.google.com/youtube/answer/1722171?hl=en#zippy=%2Cbitrate
    """
    resolutions = {
        (7680, 4320): {30: 120, 60: 180},
        (3840, 2160): {30: 40,  60: 60.5},
        (2160, 1440): {30: 16,  60: 24},
        (1920, 1080): {30: 8,   60: 12},
        (1280, 720):  {30: 5,   60: 7.5},
        (640, 480):   {30: 2.5, 60: 4},
        (480, 360):   {30: 1,   60: 1.5}
    }

    if (width, height) in resolutions:
        return resolutions[(width, height)].get(fps)
    else:
        # approximate the bitrate using a simple linear model
        area = width * height
        multiplier = 3.5982188179592543e-06 if fps == 30 else 5.396175171097084e-06
        constant = 2.418399836285939 if fps == 30 else 3.742780056500365
        return multiplier * area + constant

