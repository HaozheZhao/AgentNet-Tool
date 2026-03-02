import subprocess

import gi
gi.require_version("Atspi", "2.0")
from gi.repository import Atspi
Atspi.init()

import psutil

from .Element.LinuxElementDescriber import LinuxElementDescriber
from ..logger import logger

MAX_DEPTH = 30
MAX_WIDTH = 1024


# ── helpers ────────────────────────────────────────────────────────────

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
    # Strategy 1: Check STATE_ACTIVE / STATE_FOCUSED on windows
    desktop = Atspi.get_desktop(0)
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
                if state_set.contains(Atspi.StateType.ACTIVE) or state_set.contains(Atspi.StateType.FOCUSED):
                    return app, win
        except Exception:
            continue

    # Strategy 2: Use xdotool to get PID, then find app by PID
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
                    # Return first window of matching app
                    if app.get_child_count() > 0:
                        win = app.get_child_at_index(0)
                        if win is not None:
                            return app, win
            except Exception:
                continue

    return None, None


def _get_extents(node):
    """Get bounding rectangle of an accessible node.

    Returns dict with left/top/right/bottom or None.
    """
    try:
        component = node.get_component_iface()
        if component is None:
            return None
        ext = component.get_extents(Atspi.CoordType.SCREEN)
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
    """Recursively find the deepest accessible element at (x, y).

    AT-SPI's get_accessible_at_point only returns a direct child,
    so we must drill down repeatedly to find the leaf element.
    """
    component = node.get_component_iface()
    if component is None:
        return node

    current = node
    for _ in range(MAX_DEPTH):
        comp = current.get_component_iface()
        if comp is None:
            break
        child = comp.get_accessible_at_point(x, y, Atspi.CoordType.SCREEN)
        if child is None or child == current:
            break
        current = child

    return current


# ── public API (matches _windows.py interface) ────────────────────────


def get_top_window_name() -> str:
    """Get the process name of the active window."""
    try:
        app, win = _find_active_window()
        if app is not None:
            name = app.get_name()
            if name:
                return name
    except Exception:
        pass

    # Fallback: xdotool + psutil
    try:
        pid = _get_pid_from_xdotool()
        if pid:
            proc = psutil.Process(pid)
            return proc.name().split(".", 1)[0]
    except Exception:
        pass

    return None


def get_top_window() -> dict:
    """Get info dict for the active window."""
    app, win = _find_active_window()
    if win is None:
        return None
    ext = _get_extents(win)
    return {
        "title": win.get_name() or "",
        "app_name": app.get_name() if app else "",
        "bounds": ext,
    }


def get_active_window_state(read_window_data: bool = True) -> dict:
    """Get the state of the active window.

    Returns dict matching the format expected by __init__.py for
    sys.platform == "linux" (returned directly, same as win32 path).
    """
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


def traverse_accessible(node, depth=0):
    """Recursively build an a11y tree dict matching the Windows format.

    Keys: Name, ControlType, BoundingRectangle, Depth, Children
    """
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

    ext = _get_extents(node)

    tree = {
        "Name": name,
        "ControlType": role_name,
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
                    child_tree = traverse_accessible(child, depth + 1)
                    if child_tree:
                        tree["Children"].append(child_tree)
            except Exception:
                continue

    return tree


def get_accessibility_tree():
    """Get the full a11y tree of the active window."""
    tree = {}
    tree_status = {
        "complete": True,
        "switched": False,
        "closed": False,
    }

    try:
        state_before = get_active_window_state()
        app, win = _find_active_window()
        if win is None:
            tree_status["complete"] = False
            tree_status["closed"] = True
            tree.update(tree_status)
            return tree

        tree = traverse_accessible(win, depth=0)

        state_after = get_active_window_state()
        if state_before != state_after:
            tree_status["complete"] = False
            tree_status["switched"] = True

    except Exception as e:
        tree_status["complete"] = False
        tree_status["closed"] = True
        logger.exception(f"get_accessibility_tree error: {str(e)}")

    tree.update(tree_status)
    return tree


def get_active_element_state(x, y):
    """Get the a11y tree of the element at the given coordinates.

    Finds the deepest element at (x,y) by recursively drilling down,
    then builds a subtree from that element to provide context for scoring.
    Also traverses upward to include the parent chain for better matching.
    """
    try:
        app, win = _find_active_window()
        if win is None:
            return {}

        # Find the deepest element at (x, y)
        deepest = _get_deepest_at_point(win, x, y)

        # Build a subtree: walk up a few levels to get context,
        # then traverse down from there
        context_node = deepest
        for _ in range(3):
            try:
                parent = context_node.get_parent()
                if parent is None or parent.get_role() == Atspi.Role.DESKTOP_FRAME:
                    break
                context_node = parent
            except Exception:
                break

        tree = traverse_accessible(context_node)
        if tree and (tree.get("Name") or tree.get("Children")):
            return tree

        # Fallback: return the whole window tree
        return traverse_accessible(win)

    except Exception as e:
        logger.info(f"get_active_element_state error: {e}")
        return {}


def parse_element(element, x: float, y: float):
    """Score the element tree and find the best matching node."""
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
