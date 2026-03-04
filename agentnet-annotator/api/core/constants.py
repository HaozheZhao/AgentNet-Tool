from enum import Enum

SERVER_URL = "https://agentnet.xlang.ai"


class RecordingStatus(Enum):
    verifying = "verifying"
    editing = "editing"
    edited = "edited"
    accepted = "accepted"
    rejected = "rejected"
    final_accept = "final_accept"
    final_reject = "final_reject"
    archived = "archived"
    file_missing = "file_missing"
    file_broken = "file_broken"
    # local status
    local = "local"
    processing = "processing"


REVIEW_RECORDING_STATUSES = ["verifying"]

VERIFY_LIST_SIZE = 0

SUCCEED = "succeed"
FAILED = "failed"

RECORDING_STATUS_TO_VIS_STATUS = {
    "verifying": "Pending",
    "accepted": "Accepted",
    "rejected": "Rejected",
    "archived": "Archived",
}

EXCLUDE_LIST = ["recording_status.json", "hub_task_id.txt"]
INCLUDE_LIST = ["video_clips", "reduced_events_vis.jsonl"]
COMPLETE_DATA_LIST = [
    "events.jsonl",
    "event_buffer.jsonl",
    "element.jsonl",
    "html.jsonl",
    "html_element.jsonl",
    "a11y.jsonl",
    "reduced_events_complete.jsonl",
    "reduced_events_vis.jsonl",
    "top_window.jsonl",
]


VK_CODE = {
    8: "Backspace",
    9: "Tab",
    13: "Enter",
    16: "Shift",
    17: "Ctrl",
    18: "Alt",
    19: "Pause",
    20: "Caps Lock",
    27: "Esc",
    32: "Space",
    33: "Page Up",
    34: "Page Down",
    35: "End",
    36: "Home",
    37: "Left",
    38: "Up",
    39: "Right",
    40: "Down",
    44: "Print Screen",
    45: "Insert",
    46: "Delete",
    # Number andealphabat
    48: "0",
    49: "1",
    50: "2",
    51: "3",
    52: "4",
    53: "5",
    54: "6",
    55: "7",
    56: "8",
    57: "9",
    65: "A",
    66: "B",
    67: "C",
    68: "D",
    69: "E",
    70: "F",
    71: "G",
    72: "H",
    73: "I",
    74: "J",
    75: "K",
    76: "L",
    77: "M",
    78: "N",
    79: "O",
    80: "P",
    81: "Q",
    82: "R",
    83: "S",
    84: "T",
    85: "U",
    86: "V",
    87: "W",
    88: "X",
    89: "Y",
    90: "Z",
    # Numpad (Windows VK codes)
    96: "0",
    97: "1",
    98: "2",
    99: "3",
    100: "4",
    101: "5",
    102: "6",
    103: "7",
    104: "8",
    105: "9",
    110: ".",
    12: "$Unknown$",
    # ── X11 keysyms (Linux) ──────────────────────────────────────
    # Numpad (XK_KP_*)
    65456: "0",   # XK_KP_0
    65457: "1",   # XK_KP_1
    65458: "2",   # XK_KP_2
    65459: "3",   # XK_KP_3
    65460: "4",   # XK_KP_4
    65461: "5",   # XK_KP_5
    65462: "6",   # XK_KP_6
    65463: "7",   # XK_KP_7
    65464: "8",   # XK_KP_8
    65465: "9",   # XK_KP_9
    65454: ".",   # XK_KP_Decimal
    65453: "-",   # XK_KP_Subtract
    65451: "+",   # XK_KP_Add
    65450: "*",   # XK_KP_Multiply
    65455: "/",   # XK_KP_Divide
    65421: "Enter",  # XK_KP_Enter
    # Numpad with NumLock off (navigation keysyms)
    65429: "Home",       # XK_KP_Home
    65430: "Left",       # XK_KP_Left
    65431: "Up",         # XK_KP_Up
    65432: "Right",      # XK_KP_Right
    65433: "Down",       # XK_KP_Down
    65434: "Page Up",    # XK_KP_Page_Up
    65435: "Page Down",  # XK_KP_Page_Down
    65436: "End",        # XK_KP_End
    65437: "5",          # XK_KP_Begin (numpad 5 with NumLock off)
    65438: "Insert",     # XK_KP_Insert
    65439: "Delete",     # XK_KP_Delete
    # Modifier keys
    65505: "Shift",      # XK_Shift_L
    65506: "Shift",      # XK_Shift_R
    65507: "Ctrl",       # XK_Control_L
    65508: "Ctrl",       # XK_Control_R
    65513: "Alt",        # XK_Alt_L
    65514: "Alt",        # XK_Alt_R
    65515: "Super",      # XK_Super_L
    65516: "Super",      # XK_Super_R
    65509: "Caps Lock",  # XK_Caps_Lock
    65407: "Num Lock",   # XK_Num_Lock
    65300: "Scroll Lock", # XK_Scroll_Lock
    # Navigation / editing
    65360: "Home",       # XK_Home
    65367: "End",        # XK_End
    65365: "Page Up",    # XK_Page_Up
    65366: "Page Down",  # XK_Page_Down
    65379: "Insert",     # XK_Insert
    65535: "Delete",     # XK_Delete
    65307: "Esc",        # XK_Escape
    65293: "Enter",      # XK_Return
    65289: "Tab",        # XK_Tab
    65288: "Backspace",  # XK_BackSpace
    65377: "Print Screen", # XK_Print
    65299: "Pause",      # XK_Pause
    # Arrow keys
    65361: "Left",       # XK_Left
    65362: "Up",         # XK_Up
    65363: "Right",      # XK_Right
    65364: "Down",       # XK_Down
    # Function keys
    65470: "F1",
    65471: "F2",
    65472: "F3",
    65473: "F4",
    65474: "F5",
    65475: "F6",
    65476: "F7",
    65477: "F8",
    65478: "F9",
    65479: "F10",
    65480: "F11",
    65481: "F12",
}
