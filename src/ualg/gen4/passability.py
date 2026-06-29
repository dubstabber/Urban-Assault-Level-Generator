"""Height generation and route checks for Generator4."""

from __future__ import annotations

from collections import deque

from ..core.maps import filled_rows
from ..models import MapRows
from ..rng import MSVCRTRandom

_DEFAULT_HEIGHT = 0x7F
_CLIFF_DELTA = 8


def synthesize_hgt_map(
    width: int,
    height: int,
    rng: MSVCRTRandom,
    *,
    median: int = _DEFAULT_HEIGHT,
    required_cells: list[tuple[int, int]] | None = None,
    target_blocked_ratio: float = 0.0,
) -> MapRows:
    """Generate a height map with required cells on one passable component."""

    base = max(0, min(0xFF, int(median or _DEFAULT_HEIGHT)))
    rows = filled_rows(width, height, base)
    required = {
        (x, y)
        for x, y in (required_cells or [])
        if 0 < x < width - 1 and 0 < y < height - 1
    }
    if target_blocked_ratio <= 0:
        return rows

    # Decorative cliff cells are isolated one-offs, kept away from required cells.
    # This gives Generator4 a bit of authored-style vertical contrast without
    # risking broken campaign routes.
    candidate_count = max(0, int(width * height * min(target_blocked_ratio, 0.12) / 2))
    placed = 0
    attempts = max(16, candidate_count * 12)
    protected = set(required)
    for x, y in list(required):
        protected.update(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
    for _ in range(attempts):
        if placed >= candidate_count:
            break
        x = rng.rand_range(1, width - 2)
        y = rng.rand_range(1, height - 2)
        if (x, y) in protected:
            continue
        rows[y][x] = max(0, min(0xFF, base + _CLIFF_DELTA))
        placed += 1
    if required and not required_cells_connected(rows, list(required)):
        return filled_rows(width, height, base)
    return rows


def required_cells_connected(rows: MapRows, required_cells: list[tuple[int, int]]) -> bool:
    required = [(x, y) for x, y in required_cells if _in_bounds(rows, x, y)]
    if len(required) <= 1:
        return True
    start = required[0]
    seen = _component(rows, start)
    return all(cell in seen for cell in required)


def route_blockers(rows: MapRows, required_cells: list[tuple[int, int]]) -> list[str]:
    required = [(x, y) for x, y in required_cells if _in_bounds(rows, x, y)]
    if len(required) <= 1:
        return []
    seen = _component(rows, required[0])
    missing = [cell for cell in required if cell not in seen]
    if not missing:
        return []
    return [f"required route cell {x},{y} is disconnected by height barriers" for x, y in missing]


def _component(rows: MapRows, start: tuple[int, int]) -> set[tuple[int, int]]:
    queue: deque[tuple[int, int]] = deque([start])
    seen = {start}
    while queue:
        x, y = queue.popleft()
        here = int(rows[y][x])
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if not _in_bounds(rows, nx, ny) or (nx, ny) in seen:
                continue
            if abs(here - int(rows[ny][nx])) > 4:
                continue
            seen.add((nx, ny))
            queue.append((nx, ny))
    return seen


def _in_bounds(rows: MapRows, x: int, y: int) -> bool:
    return 0 <= y < len(rows) and 0 <= x < len(rows[y])
