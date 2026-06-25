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
