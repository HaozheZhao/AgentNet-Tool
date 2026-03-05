"""
Linux AT-SPI accessibility module.

All AT-SPI / GLib work runs in a **separate subprocess** to isolate its
memory from the main Flask process.  GLib's C layer can corrupt the heap
(malloc errors, segfaults) — with process isolation, only the worker
subprocess dies; the main process and all recording data survive.

The subprocess auto-restarts on the next call if it crashes.
"""
import json
import os
import select
import subprocess
import sys
import threading

from .Element.LinuxElementDescriber import LinuxElementDescriber
from ..logger import logger

_WORKER_SCRIPT = os.path.join(os.path.dirname(__file__), "_linux_atspi_worker.py")


class _AtspiProxy:
    """Proxy that runs AT-SPI operations in a separate subprocess."""

    def __init__(self):
        self._proc = None
        self._lock = threading.Lock()
        self._start()

    def _start(self):
        """Start (or restart) the AT-SPI worker subprocess."""
        if self._proc is not None:
            try:
                self._proc.kill()
                self._proc.wait(timeout=2)
            except Exception:
                pass

        try:
            self._proc = subprocess.Popen(
                [sys.executable, _WORKER_SCRIPT],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            # Wait for the "ready" signal (up to 10s)
            ready_fds, _, _ = select.select([self._proc.stdout], [], [], 10)
            if ready_fds:
                line = self._proc.stdout.readline()
                if line:
                    msg = json.loads(line.decode().strip())
                    if msg.get("status") == "ready":
                        logger.info(f"AT-SPI worker subprocess started (PID {self._proc.pid})")
                        return
            logger.warning("AT-SPI worker subprocess did not signal readiness")
        except Exception as e:
            logger.warning(f"AT-SPI worker failed to start: {e}")
            self._proc = None

    def _is_alive(self):
        return self._proc is not None and self._proc.poll() is None

    def call(self, cmd, timeout=15, **kwargs):
        """Send a command to the worker and return the result."""
        with self._lock:
            if not self._is_alive():
                logger.warning("AT-SPI worker not running, restarting...")
                self._start()
                if not self._is_alive():
                    logger.error("AT-SPI worker failed to restart")
                    return None

            request = json.dumps({"cmd": cmd, "args": kwargs}) + "\n"
            try:
                self._proc.stdin.write(request.encode())
                self._proc.stdin.flush()

                # Wait for response with timeout
                ready_fds, _, _ = select.select([self._proc.stdout], [], [], timeout)
                if not ready_fds:
                    logger.warning(f"AT-SPI worker timed out for {cmd}, killing...")
                    self._proc.kill()
                    self._proc = None
                    return None

                line = self._proc.stdout.readline()
                if not line:
                    # EOF — subprocess crashed
                    logger.warning(f"AT-SPI worker crashed during {cmd}")
                    self._proc = None
                    return None

                response = json.loads(line.decode().strip())
                if response["status"] == "ok":
                    return response["result"]
                else:
                    logger.warning(f"AT-SPI worker error for {cmd}: {response.get('message')}")
                    return None

            except (BrokenPipeError, OSError) as e:
                logger.warning(f"AT-SPI worker pipe error for {cmd}: {e}")
                self._proc = None
                return None
            except Exception as e:
                logger.warning(f"AT-SPI proxy error for {cmd}: {e}")
                try:
                    self._proc.kill()
                except Exception:
                    pass
                self._proc = None
                return None

    def shutdown(self):
        """Clean up the subprocess."""
        if self._proc is not None:
            try:
                self._proc.stdin.close()
                self._proc.wait(timeout=3)
            except Exception:
                try:
                    self._proc.kill()
                except Exception:
                    pass
            self._proc = None


_proxy = _AtspiProxy()


# ── public API (matches _windows.py interface) ────────────────────────
# Every call dispatches to the subprocess.  If the subprocess crashes,
# it returns None/{} and auto-restarts on the next call.


def get_top_window_name() -> str:
    return _proxy.call("get_top_window_name")


def get_top_window() -> dict:
    return _proxy.call("get_top_window")


def get_active_window_state(read_window_data: bool = True) -> dict:
    return _proxy.call("get_active_window_state")


def get_accessibility_tree():
    return _proxy.call("get_accessibility_tree") or {}


def get_active_element_state(x, y):
    return _proxy.call("get_active_element_state", x=x, y=y) or {}


def parse_element(element, x: float, y: float):
    """Score the element tree and find the best matching node.

    Pure Python dict operations — no AT-SPI calls, runs in main process.
    """
    try:
        if not element or not isinstance(element, dict):
            return None
        describer = LinuxElementDescriber(x, y)
        describer = describer.build_from_json(element)
        describer.calculate_score()
        target = describer.find_most_score_node()
        if target.score < 0:
            return None
        return target.to_dict()
    except Exception as e:
        logger.info(f"parse_element error: {e}")
        return None
