"""Map-row helpers shared by generator implementations."""

from __future__ import annotations

from ..models import MapRows


def filled_rows(width: int, height: int, value: int = 0) -> MapRows:
    return [[value & 0xFF for _ in range(width)] for _ in range(height)]


def set_cell(rows: MapRows, x: int, y: int, value: int) -> None:
    rows[y][x] = value & 0xFF


def set_cell_if_in_bounds(rows: MapRows, width: int, height: int, x: int, y: int, value: int) -> bool:
    if 0 <= x < width and 0 <= y < height:
        set_cell(rows, x, y, value)
        return True
    return False
