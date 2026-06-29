"""LDF text writer and parsing helpers."""

from __future__ import annotations

from .models import MapRows


class LDFWriter:
    """Small CRLF-oriented writer for Urban Assault LDF files."""

    def __init__(self, property_style: str = "tabs") -> None:
        self._parts: list[str] = []
        self.property_style = property_style

    def line(self, text: str = "") -> None:
        self._parts.append(text + "\r\n")

    def text(self, text: str) -> None:
        self._parts.append(text)

    def property(self, key: str, value: object) -> None:
        if self.property_style == "php":
            padded = key
            while len(padded) < 14:
                padded += " "
            self.line(f"  {padded}= {value}")
        else:
            self.line(f"\t{key}\t=\t{value}")

    def begin_block(self, name: str) -> None:
        self.line(name)

    def end_block(self) -> None:
        self.line("end")

    def section(self, title: str) -> None:
        self.line(";------------------------------------------------------------")
        self.line(f";--- {title:<52}---")
        self.line(";------------------------------------------------------------")

    def none(self) -> None:
        self.line(";none")

    def maps_end_comment(self) -> None:
        self.line("; ------------------------ ")
        self.line(";--- map dumps end here ---")
        self.line("; ------------------------ ")

    def end_file_comment(self) -> None:
        self.section("End Of File")

    def map_block(self, map_name: str, rows: MapRows, width: int, height: int, php_style: bool = False) -> None:
        if php_style:
            self.line(f"  {map_name} =")
            self.line(f"    {width} {height}")
            indent = "    "
        else:
            self.line(f"{map_name}\t=")
            self.line(f"\t{width} {height}")
            indent = "\t"
        for row in rows:
            values = " ".join(f"{value & 0xFF:02x}" for value in row[:width])
            self.line(f"{indent}{values} ")
        self.line("")

    def getvalue(self) -> str:
        return "".join(self._parts)


def _head_without_comment(line: str) -> str:
    stripped = line.split(";", 1)[0].strip().lower()
    return stripped.split(None, 1)[0] if stripped else ""


def canonicalize_gem_block(lines: list[str]) -> list[str]:
    """Fix authored gem blocks where the gem-closing ``end`` precedes ``end_action``."""

    result: list[str] = []
    stack: list[str] = []
    deferred_gem_ends: list[str] = []

    for line in lines:
        head = _head_without_comment(line)
        if head == "begin_gem":
            stack.append("gem")
            result.append(line)
        elif head == "begin_action":
            stack.append("action")
            result.append(line)
        elif head.startswith("modify_"):
            if stack and stack[-1] == "modify":
                stack.pop()
            stack.append("modify")
            result.append(line)
        elif head == "end":
            if stack and stack[-1] == "modify":
                stack.pop()
                result.append(line)
            elif stack and stack[-1] == "action":
                deferred_gem_ends.append(line)
            else:
                if stack and stack[-1] == "gem":
                    stack.pop()
                result.append(line)
                if deferred_gem_ends:
                    deferred_gem_ends.pop(0)
        elif head == "end_action":
            if stack and stack[-1] == "action":
                stack.pop()
            result.append(line)
        else:
            result.append(line)

    while deferred_gem_ends and stack and stack[-1] == "gem":
        stack.pop()
        result.append(deferred_gem_ends.pop(0))

    return result


def format_gem_block(lines: list[str]) -> list[str]:
    """Return a readable, consistently indented gem block."""

    result: list[str] = []
    stack: list[str] = []
    for line in canonicalize_gem_block(lines):
        stripped = line.strip()
        head = _head_without_comment(stripped)
        if not stripped:
            result.append("")
        elif head == "begin_gem":
            stack.append("gem")
            result.append(stripped)
        elif head == "begin_action":
            stack.append("action")
            result.append(f"\t{stripped}")
        elif head.startswith("modify_"):
            if stack and stack[-1] == "modify":
                stack.pop()
            stack.append("modify")
            result.append(f"\t\t{stripped}")
        elif head == "end":
            if stack and stack[-1] == "modify":
                stack.pop()
                result.append(f"\t\t{stripped}")
            else:
                if stack and stack[-1] == "gem":
                    stack.pop()
                result.append(stripped)
        elif head == "end_action":
            if stack and stack[-1] == "action":
                stack.pop()
            result.append(f"\t{stripped}")
        elif stack and stack[-1] == "modify":
            result.append(f"\t\t\t{stripped}")
        elif stack:
            result.append(f"\t{stripped}")
        else:
            result.append(stripped)
    return result


def parse_maps(text: str) -> dict[str, tuple[int, int, MapRows]]:
    """Parse typ/own/hgt/blg map blocks from generated LDF text."""

    lines = [line.rstrip("\r") for line in text.split("\n")]
    result: dict[str, tuple[int, int, MapRows]] = {}
    for i, line in enumerate(lines):
        stripped = line.strip()
        for name in ("typ_map", "own_map", "hgt_map", "blg_map"):
            if not stripped.startswith(name):
                continue
            if i + 1 >= len(lines):
                continue
            dims = lines[i + 1].strip().split()
            if len(dims) < 2:
                continue
            width, height = int(dims[0]), int(dims[1])
            rows: MapRows = []
            cursor = i + 2
            while len(rows) < height and cursor < len(lines):
                row_text = lines[cursor].strip()
                cursor += 1
                if not row_text:
                    continue
                tokens = row_text.split()
                if len(tokens) < width:
                    continue
                rows.append([int(token, 16) for token in tokens[:width]])
            if len(rows) == height:
                result[name] = (width, height, rows)
    return result
