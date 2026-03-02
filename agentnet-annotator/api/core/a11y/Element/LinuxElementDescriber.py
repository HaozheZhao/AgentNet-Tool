import re
import math
import statistics

from numpy import mean

from .UIElementDescriber import UIElementDescriber

MAX_AREA = 1920 * 1020 / 2
MIN_AREA = 1000
POSITION_HIT_B = math.exp(math.log(MAX_AREA / MIN_AREA) / 1)

# Regex to detect meaningful text (letters, digits, CJK characters)
_HAS_TEXT_RE = re.compile(r"[\u4e00-\u9fffA-Za-z0-9]")


class LinuxElementDescriber(UIElementDescriber):
    def __init__(self, x, y):
        self.control_type = None
        self.role_description = None
        self.value = None
        self.depth = None
        self.similarity_cache = {}
        self.x = x
        self.y = y

    def to_dict(self):
        # Return all semantic attributes that the UI can use for display
        output_keys = ("title", "control_type", "description", "value", "role_description")
        return {
            k: getattr(self, k) for k in output_keys
            if hasattr(self, k) and getattr(self, k) not in (None, "")
        }

    def build_from_json(self, data):
        super().build_from_json(
            {
                "title": data.get("Name", None),
                "description": data.get("Description", None),
                "rect": data.get("BoundingRectangle", None),
            }
        )
        self.control_type = data.get("ControlType", None)
        # Map AT-SPI role name to role_description for UI compatibility
        self.role_description = data.get("ControlType", None)
        self.value = data.get("Value", None) or None  # convert "" to None
        self.depth = data.get("Depth", None)
        self.attrs = [attr for attr in vars(self) if getattr(self, attr) not in (None, "")]
        if "Children" in data:
            self.build_children(children_json=data.get("Children"), rule="bounding")
        return self

    def _has_semantic_text(self):
        """Check if this element has any meaningful text in any field."""
        for field in (self.title, self.description, self.value):
            if field and _HAS_TEXT_RE.search(str(field)):
                return True
        return False

    def get_nearest_ancestor_rect(self):
        if self.rect != None:
            return self.rect

    def build_children(self, children_json, rule="bounding"):
        all_children = []
        for index, child_json in enumerate(children_json):
            if isinstance(child_json, str):
                continue
            if "children" in child_json:
                tmp = LinuxElementDescriber(self.x, self.y)
                tmp.parent = self
                tmp.index = index
                tmp.build_from_json(child_json)
                if tmp.children:
                    all_children.append(tmp)
            else:
                tmp = LinuxElementDescriber(self.x, self.y)
                tmp.parent = self
                tmp.index = index
                tmp.build_from_json(child_json)
                all_children.append(tmp)

        self.children = all_children

    def print_element(self, indent=0):
        indent_space = " " * (indent * 2)
        rect = self.get_nearest_ancestor_rect()
        print(
            f"{indent_space}Title: {self.title}, x: {rect['left']}, y: {rect['top']}, w: {rect['right'] - rect['left']}, h: {rect['bottom'] - rect['top']}".encode(
                "utf-8", errors="replace"
            ).decode(
                "utf-8"
            )
        )
        for child in self.children:
            child.print_element(indent + 1)

    def calculate_score(self):
        self.vote_by_heuristic_rules(
            [(self.semantic_info_score, 1), (self.position_hit, 1)]
        )
        for child in self.children:
            child.calculate_score()

    def semantic_info_score(self):
        # Check title first
        if self.title and _HAS_TEXT_RE.search(self.title):
            return (
                1 if (len(self.title) < 40) else (1 - ((len(self.title) - 40) / 60))
            )
        # Fall back to description or value
        if self._has_semantic_text():
            return 0.5
        # Role name alone is mildly useful (e.g. "push button", "menu item")
        if self.control_type and self.control_type not in ("", "panel", "filler", "section"):
            return -2
        return -10

    def position_hit(self):
        if not self.rect:
            return -10

        rect_x, rect_y, rect_w, rect_h = (
            self.rect["left"],
            self.rect["top"],
            (self.rect["right"] - self.rect["left"]),
            (self.rect["bottom"] - self.rect["top"]),
        )
        area = rect_w * rect_h
        score = 0
        if rect_x <= self.x <= rect_x + rect_w and rect_y <= self.y <= rect_y + rect_h:
            if area < MIN_AREA:
                score = 1
            else:
                score = 1 * math.log(MAX_AREA / area, POSITION_HIT_B)
        else:
            score = -10

        return min(max(score, -10), 1)
