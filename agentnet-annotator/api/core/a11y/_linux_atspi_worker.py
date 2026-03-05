#!/usr/bin/env python3
"""
AT-SPI worker subprocess.

Runs in a separate process to isolate GLib/AT-SPI memory from the main
Flask process.  Communicates via JSON lines on stdin/stdout.

If this process crashes (segfault, malloc corruption), the main process
detects it via EOF on the pipe and spawns a new one automatically.
"""
import json
import subprocess
import sys

MAX_DEPTH = 30
MAX_WIDTH = 1024


# ── AT-SPI helpers ────────────────────────────────────────────────────

def _get_pid_from_xdotool():
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


def _find_active_window(Atspi):
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
                if state_set.contains(Atspi.StateType.ACTIVE) or \
                   state_set.contains(Atspi.StateType.FOCUSED):
                    return app, win
        except Exception:
            continue

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


def _get_extents(Atspi, node):
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


def _get_deepest_at_point(Atspi, node, x, y):
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


def _traverse_accessible(Atspi, node, depth=0):
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

    ext = _get_extents(Atspi, node)

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
                    child_tree = _traverse_accessible(Atspi, child, depth + 1)
                    if child_tree:
                        tree["Children"].append(child_tree)
            except Exception:
                continue

    return tree


# ── Command handlers ──────────────────────────────────────────────────

def cmd_get_top_window_name(Atspi):
    try:
        app, _win = _find_active_window(Atspi)
        if app is not None:
            name = app.get_name()
            if name:
                return name
    except Exception:
        pass

    try:
        import psutil
        pid = _get_pid_from_xdotool()
        if pid:
            proc = psutil.Process(pid)
            return proc.name().split(".", 1)[0]
    except Exception:
        pass

    return None


def cmd_get_top_window(Atspi):
    app, win = _find_active_window(Atspi)
    if win is None:
        return None
    ext = _get_extents(Atspi, win)
    return {
        "title": win.get_name() or "",
        "app_name": app.get_name() if app else "",
        "bounds": ext,
    }


def cmd_get_active_window_state(Atspi):
    app, win = _find_active_window(Atspi)
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

    ext = _get_extents(Atspi, win)
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


def cmd_get_accessibility_tree(Atspi):
    tree = {}
    tree_status = {"complete": True, "switched": False, "closed": False}

    try:
        state_before = cmd_get_active_window_state(Atspi)
        app, win = _find_active_window(Atspi)
        if win is None:
            tree_status["complete"] = False
            tree_status["closed"] = True
            tree.update(tree_status)
            return tree

        tree = _traverse_accessible(Atspi, win, depth=0)

        state_after = cmd_get_active_window_state(Atspi)
        if state_before != state_after:
            tree_status["complete"] = False
            tree_status["switched"] = True

    except Exception as e:
        tree_status["complete"] = False
        tree_status["closed"] = True
        print(f"get_accessibility_tree error: {e}", file=sys.stderr)

    tree.update(tree_status)
    return tree


def cmd_get_active_element_state(Atspi, x, y):
    try:
        app, win = _find_active_window(Atspi)
        if win is None:
            return {}

        deepest = _get_deepest_at_point(Atspi, win, x, y)

        context_node = deepest
        for _ in range(3):
            try:
                parent = context_node.get_parent()
                if parent is None or parent.get_role() == Atspi.Role.DESKTOP_FRAME:
                    break
                context_node = parent
            except Exception:
                break

        tree = _traverse_accessible(Atspi, context_node)
        if tree and (tree.get("Name") or tree.get("Children")):
            return tree

        return _traverse_accessible(Atspi, win)

    except Exception as e:
        print(f"get_active_element_state error at ({x},{y}): {e}", file=sys.stderr)
        return {}


# ── Main loop ─────────────────────────────────────────────────────────

def main():
    import gi
    gi.require_version("Atspi", "2.0")
    from gi.repository import Atspi
    Atspi.init()

    COMMANDS = {
        "get_top_window_name": lambda a: cmd_get_top_window_name(Atspi),
        "get_top_window": lambda a: cmd_get_top_window(Atspi),
        "get_active_window_state": lambda a: cmd_get_active_window_state(Atspi),
        "get_accessibility_tree": lambda a: cmd_get_accessibility_tree(Atspi),
        "get_active_element_state": lambda a: cmd_get_active_element_state(Atspi, a["x"], a["y"]),
    }

    # Signal readiness
    sys.stdout.write(json.dumps({"status": "ready"}) + "\n")
    sys.stdout.flush()

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
            cmd = request["cmd"]
            args = request.get("args", {})
            handler = COMMANDS.get(cmd)
            if handler is None:
                sys.stdout.write(json.dumps({"status": "error", "message": f"unknown: {cmd}"}) + "\n")
                sys.stdout.flush()
                continue
            result = handler(args)
            sys.stdout.write(json.dumps({"status": "ok", "result": result}) + "\n")
            sys.stdout.flush()
        except Exception as e:
            sys.stdout.write(json.dumps({"status": "error", "message": str(e)}) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
