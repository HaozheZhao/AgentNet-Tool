import subprocess
import threading
from queue import Queue, Empty

import psutil

from .Element.LinuxElementDescriber import LinuxElementDescriber
from ..logger import logger

MAX_DEPTH = 30
MAX_WIDTH = 1024

# ── AT-SPI worker thread ─────────────────────────────────────────────
# GLib / AT-SPI objects have thread affinity: they must be created and
# accessed from the same thread.  We initialise AT-SPI inside a single
# long-lived daemon thread and dispatch every operation to it.  This
# eliminates segfaults caused by cross-thread GLib access.

_work_queue = Queue()       # items: (callable, args, result_queue)
_ready = threading.Event()  # set once Atspi.init() has finished
_Atspi = None               # populated by the worker thread


def _atspi_worker():
    """Dedicated thread that owns all AT-SPI / GLib state."""
    global _Atspi
    import gi
    gi.require_version("Atspi", "2.0")
    from gi.repository import Atspi
    Atspi.init()
    _Atspi = Atspi
    _ready.set()

    while True:
        func, args, result_q = _work_queue.get()
        try:
            result = func(*args)
            result_q.put(("ok", result))
        except Exception as e:
            result_q.put(("err", e))


_thread = threading.Thread(target=_atspi_worker, daemon=True)
_thread.start()
_ready.wait()


def _run(func, *args, timeout=15):
    """Run *func* on the AT-SPI worker thread and return the result."""
    rq = Queue(maxsize=1)
    _work_queue.put((func, args, rq))
    try:
        status, value = rq.get(timeout=timeout)
    except Empty:
        raise TimeoutError(f"AT-SPI call {func.__name__} timed out after {timeout}s")
    if status == "err":
        raise value
    return value


# ── helpers (run ONLY on the worker thread) ───────────────────────────

def _get_pid_from_xdotool():
    """Get active window PID via xdotool."""
    try:
        wid = subprocess.check_output(
            ["xdotool", "getactivewindow"], stderr=subprocess.DEVNULL
        ).decode().strip()
        pid_str = subprocess.check_output(
            ["xdotool", "getwindowpid", wid], stderr=subprocess.DEVNULL
        ).decode().strip()
        return int(pid_str)
    except Exception:
        return None


def _find_active_window():
    """Find the currently active/focused window via AT-SPI.

    Returns (app_accessible, window_accessible) or (None, None).
    """
    desktop = _Atspi.get_desktop(0)
    for i in range(desktop.get_child_count()):
        try:
            app = desktop.get_child_at_index(i)
            if app is None:
                continue
            for j in range(app.get_child_count()):
                win = app.get_child_at_index(j)
                if win is None:
                    continue
                state_set = win.get_state_set()
                if state_set.contains(_Atspi.StateType.ACTIVE) or state_set.contains(_Atspi.StateType.FOCUSED):
                    return app, win
        except Exception:
            continue

    # Fallback: xdotool PID
    pid = _get_pid_from_xdotool()
    if pid is not None:
        for i in range(desktop.get_child_count()):
            try:
                app = desktop.get_child_at_index(i)
                if app is None:
                    continue
                try:
                    app_pid = app.get_process_id()
                except Exception:
                    app_pid = -1
                if app_pid == pid:
                    if app.get_child_count() > 0:
                        win = app.get_child_at_index(0)
                        if win is not None:
                            return app, win
            except Exception:
                continue

    return None, None


def _get_extents(node):
    """Get bounding rectangle of an accessible node."""
    try:
        component = node.get_component_iface()
        if component is None:
            return None
        ext = component.get_extents(_Atspi.CoordType.SCREEN)
        if ext.width <= 0 and ext.height <= 0:
            return None
        return {
            "left": ext.x,
            "top": ext.y,
            "right": ext.x + ext.width,
            "bottom": ext.y + ext.height,
        }
    except Exception:
        return None


def _get_deepest_at_point(node, x, y):
    """Recursively drill to the deepest accessible element at (x, y)."""
    component = node.get_component_iface()
    if component is None:
        return node

    current = node
    for _ in range(MAX_DEPTH):
        comp = current.get_component_iface()
        if comp is None:
            break
        child = comp.get_accessible_at_point(x, y, _Atspi.CoordType.SCREEN)
        if child is None or child == current:
            break
        current = child

    return current


def _traverse_accessible(node, depth=0):
    """Recursively build an a11y tree dict matching the Windows format."""
    if node is None:
        return None

    try:
        name = node.get_name() or ""
    except Exception:
        name = ""

    try:
        role_name = node.get_role_name() or ""
    except Exception:
        role_name = ""

    try:
        description = node.get_description() or ""
    except Exception:
        description = ""

    value = ""
    try:
        text_iface = node.get_text_iface()
        if text_iface is not None:
            char_count = text_iface.get_character_count()
            if 0 < char_count <= 200:
                value = text_iface.get_text(0, char_count) or ""
    except Exception:
        pass

    ext = _get_extents(node)

    tree = {
        "Name": name,
        "ControlType": role_name,
        "Description": description,
        "Value": value,
        "BoundingRectangle": ext if ext else {"left": 0, "top": 0, "right": 0, "bottom": 0},
        "Depth": depth,
        "Children": [],
    }

    if depth < MAX_DEPTH:
        try:
            child_count = min(node.get_child_count(), MAX_WIDTH)
        except Exception:
            child_count = 0

        for i in range(child_count):
            try:
                child = node.get_child_at_index(i)
                if child is not None:
                    child_tree = _traverse_accessible(child, depth + 1)
                    if child_tree:
                        tree["Children"].append(child_tree)
            except Exception:
                continue

    return tree


# ── internal functions dispatched to worker thread ────────────────────

def _do_get_top_window_name():
    try:
        app, win = _find_active_window()
        if app is not None:
            name = app.get_name()
            if name:
                return name
    except Exception:
        pass

    # Fallback: xdotool + psutil (no AT-SPI)
    try:
        pid = _get_pid_from_xdotool()
        if pid:
            proc = psutil.Process(pid)
            return proc.name().split(".", 1)[0]
    except Exception:
        pass

    return None


def _do_get_top_window():
    app, win = _find_active_window()
    if win is None:
        return None
    ext = _get_extents(win)
    return {
        "title": win.get_name() or "",
        "app_name": app.get_name() if app else "",
        "bounds": ext,
    }


def _do_get_active_window_state():
    app, win = _find_active_window()
    if win is None:
        return None

    title_parts = []
    if app:
        app_name = app.get_name()
        if app_name:
            title_parts.append(app_name)
    win_name = win.get_name()
    if win_name:
        title_parts.append(win_name)
    title = " ".join(title_parts) if title_parts else ""

    ext = _get_extents(win)
    left = ext["left"] if ext else 0
    top = ext["top"] if ext else 0
    width = (ext["right"] - ext["left"]) if ext else 0
    height = (ext["bottom"] - ext["top"]) if ext else 0

    try:
        pid = app.get_process_id() if app else 0
    except Exception:
        pid = 0

    return {
        "title": title,
        "left": left,
        "top": top,
        "width": width,
        "height": height,
        "window_id": pid,
    }


def _do_get_accessibility_tree():
    tree = {}
    tree_status = {
        "complete": True,
        "switched": False,
        "closed": False,
    }

    try:
        state_before = _do_get_active_window_state()
        app, win = _find_active_window()
        if win is None:
            tree_status["complete"] = False
            tree_status["closed"] = True
            tree.update(tree_status)
            return tree

        tree = _traverse_accessible(win, depth=0)

        state_after = _do_get_active_window_state()
        if state_before != state_after:
            tree_status["complete"] = False
            tree_status["switched"] = True

    except Exception as e:
        tree_status["complete"] = False
        tree_status["closed"] = True
        logger.exception(f"get_accessibility_tree error: {str(e)}")

    tree.update(tree_status)
    return tree


def _do_get_active_element_state(x, y):
    try:
        app, win = _find_active_window()
        if win is None:
            logger.info(f"get_active_element_state: no active window found for ({x}, {y})")
            return {}

        deepest = _get_deepest_at_point(win, x, y)

        context_node = deepest
        for _ in range(3):
            try:
                parent = context_node.get_parent()
                if parent is None or parent.get_role() == _Atspi.Role.DESKTOP_FRAME:
                    break
                context_node = parent
            except Exception:
                break

        tree = _traverse_accessible(context_node)
        if tree and (tree.get("Name") or tree.get("Children")):
            logger.info(f"get_active_element_state: captured element at ({x},{y}): Name='{tree.get('Name')}', ControlType='{tree.get('ControlType')}'")
            return tree

        logger.info(f"get_active_element_state: falling back to window tree for ({x},{y})")
        return _traverse_accessible(win)

    except Exception as e:
        logger.warning(f"get_active_element_state error at ({x},{y}): {e}")
        return {}


# ── public API (matches _windows.py interface) ────────────────────────
# Every public function dispatches to the worker thread via _run().


def get_top_window_name() -> str:
    return _run(_do_get_top_window_name)


def get_top_window() -> dict:
    return _run(_do_get_top_window)


def get_active_window_state(read_window_data: bool = True) -> dict:
    return _run(_do_get_active_window_state)


def get_accessibility_tree():
    return _run(_do_get_accessibility_tree)


def get_active_element_state(x, y):
    return _run(_do_get_active_element_state, x, y)


def parse_element(element, x: float, y: float):
    """Score the element tree and find the best matching node.

    Pure Python dict operations — no AT-SPI calls, runs on caller thread.
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
