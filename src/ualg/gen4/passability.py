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
    terrain_profile: dict | None = None,
) -> MapRows:
    """Generate a height map with required cells on one passable component."""

    profile = terrain_profile or {}
    base = _clamp_height(int(profile.get("median", median or _DEFAULT_HEIGHT) or _DEFAULT_HEIGHT))
    required = {
        (x, y)
        for x, y in (required_cells or [])
        if 0 < x < width - 1 and 0 < y < height - 1
    }
    source_range = int(profile.get("range", 0) or 0)
    source_unique = int(profile.get("unique_count", 1) or 1)
    blocked_ratio = float(profile.get("blocked_edge_ratio", target_blocked_ratio) or target_blocked_ratio or 0.0)
    if source_range < 3 and source_unique <= 3 and blocked_ratio <= 0.01:
        return filled_rows(width, height, base)

    target_range = max(4, source_range // 2 if source_range >= 6 else min(6, max(2, source_range)))
    if source_unique >= 6:
        target_range = max(target_range, 6)

    rows = _smooth_field(width, height, rng, base, target_range, profile)
    _stretch_range(rows, base, target_range)
    _add_cliff_bands(rows, rng, blocked_ratio, target_range, required)
    _carve_required_routes(rows, list(required), base)
    _soften_singletons(rows, required)
    if blocked_ratio > 0.02:
        _raise_blocked_ratio(rows, rng, blocked_ratio * 0.65, target_range, required)
        _carve_required_routes(rows, list(required), base)
    target_unique = max(4 if source_range >= 6 else 1, source_unique // 2)
    _ensure_unique_values(rows, base, target_range, target_unique, _protected_route_cells(list(required)))
    if required and not required_cells_connected(rows, list(required)):
        rows = _connected_varied_field(width, height, base, target_range)
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


def terrain_metrics(rows: MapRows) -> dict[str, int | float]:
    if not rows:
        return {"unique_count": 0, "range": 0, "blocked_edge_ratio": 0.0}
    values = [int(value) for row in rows for value in row]
    total_edges = 0
    blocked_edges = 0
    for y, row in enumerate(rows):
        for x, value in enumerate(row):
            for nx, ny in ((x + 1, y), (x, y + 1)):
                if ny >= len(rows) or nx >= len(row):
                    continue
                total_edges += 1
                if abs(int(value) - int(rows[ny][nx])) > 4:
                    blocked_edges += 1
    return {
        "unique_count": len(set(values)),
        "range": max(values) - min(values),
        "blocked_edge_ratio": (blocked_edges / total_edges) if total_edges else 0.0,
    }


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


def _smooth_field(
    width: int,
    height: int,
    rng: MSVCRTRandom,
    base: int,
    target_range: int,
    profile: dict,
) -> MapRows:
    rows = filled_rows(width, height, base)
    center_count = max(2, min(7, int(profile.get("feature_counts", {}).get("plateaus", 3) or 3)))
    centers: list[tuple[int, int, int]] = []
    for index in range(center_count):
        x = rng.rand_range(1, max(1, width - 2))
        y = rng.rand_range(1, max(1, height - 2))
        span = max(2, target_range // 2)
        delta = rng.rand_range(-span, span)
        if index == 0:
            delta = -span
        elif index == 1:
            delta = span
        centers.append((x, y, delta))

    max_distance = max(1, width + height)
    for y in range(height):
        for x in range(width):
            weighted = 0.0
            total_weight = 0.0
            for cx, cy, delta in centers:
                distance = abs(cx - x) + abs(cy - y)
                weight = (max_distance - min(max_distance - 1, distance)) / max_distance
                weighted += delta * weight
                total_weight += weight
            noise = rng.rand_range(-2, 2)
            rows[y][x] = _clamp_height(base + round(weighted / max(0.001, total_weight)) + noise)

    for _ in range(2):
        rows = _smooth_pass(rows)
    return rows


def _add_cliff_bands(
    rows: MapRows,
    rng: MSVCRTRandom,
    blocked_ratio: float,
    target_range: int,
    required: set[tuple[int, int]],
) -> None:
    if not rows or blocked_ratio <= 0.02:
        return
    height = len(rows)
    width = len(rows[0])
    protected = set(required)
    for x, y in list(required):
        protected.update(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
    band_count = max(1, min(14, int(blocked_ratio * width * height / 6) + 1))
    delta = max(_CLIFF_DELTA, min(14, target_range))
    for _ in range(band_count):
        vertical = bool(rng.rand_mod(2))
        length = rng.rand_range(3, max(3, min(width, height) // 2))
        x = rng.rand_range(1, max(1, width - 2))
        y = rng.rand_range(1, max(1, height - 2))
        sign = 1 if rng.rand_mod(2) else -1
        for offset in range(length):
            cx = x + (0 if vertical else offset)
            cy = y + (offset if vertical else 0)
            if not (1 <= cx < width - 1 and 1 <= cy < height - 1):
                break
            if (cx, cy) in protected:
                continue
            rows[cy][cx] = _clamp_height(rows[cy][cx] + sign * delta)


def _raise_blocked_ratio(
    rows: MapRows,
    rng: MSVCRTRandom,
    target_ratio: float,
    target_range: int,
    required: set[tuple[int, int]],
) -> None:
    if not rows:
        return
    height = len(rows)
    width = len(rows[0])
    protected = set(required)
    for x, y in list(required):
        protected.update(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
    attempts = max(16, int(width * height * target_ratio))
    delta = max(_CLIFF_DELTA, min(18, target_range + 2))
    for _ in range(attempts):
        if _blocked_ratio(rows) >= target_ratio:
            return
        vertical = bool(rng.rand_mod(2))
        length = rng.rand_range(4, max(4, min(width, height) - 2))
        x = rng.rand_range(1, max(1, width - 2))
        y = rng.rand_range(1, max(1, height - 2))
        sign = 1 if rng.rand_mod(2) else -1
        for offset in range(length):
            cx = x + (0 if vertical else offset)
            cy = y + (offset if vertical else 0)
            if not (1 <= cx < width - 1 and 1 <= cy < height - 1):
                break
            if (cx, cy) in protected:
                continue
            rows[cy][cx] = _clamp_height(rows[cy][cx] + sign * delta)


def _carve_required_routes(rows: MapRows, required_cells: list[tuple[int, int]], base: int) -> None:
    if len(required_cells) <= 1:
        return
    current = required_cells[0]
    for target in required_cells[1:]:
        for x, y in _manhattan_path(current, target):
            for nx, ny in ((x, y), (x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if _in_bounds(rows, nx, ny):
                    rows[ny][nx] = _clamp_height(base + ((nx + ny) % 3) - 1)
        current = target


def _manhattan_path(start: tuple[int, int], end: tuple[int, int]) -> list[tuple[int, int]]:
    x, y = start
    ex, ey = end
    cells = [(x, y)]
    step_x = 1 if ex >= x else -1
    while x != ex:
        x += step_x
        cells.append((x, y))
    step_y = 1 if ey >= y else -1
    while y != ey:
        y += step_y
        cells.append((x, y))
    return cells


def _protected_route_cells(required_cells: list[tuple[int, int]]) -> set[tuple[int, int]]:
    protected: set[tuple[int, int]] = set(required_cells)
    if len(required_cells) <= 1:
        return protected
    current = required_cells[0]
    for target in required_cells[1:]:
        for x, y in _manhattan_path(current, target):
            protected.update(((x, y), (x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
        current = target
    return protected


def _ensure_unique_values(
    rows: MapRows,
    base: int,
    target_range: int,
    target_unique: int,
    protected: set[tuple[int, int]],
) -> None:
    if not rows or target_unique <= 1:
        return
    current = {int(value) for row in rows for value in row}
    if len(current) >= target_unique:
        return
    low = _clamp_height(base - target_range // 2)
    desired = [_clamp_height(low + offset) for offset in range(max(target_range + 1, target_unique))]
    candidates = [
        (x, y)
        for y in range(1, len(rows) - 1)
        for x in range(1, len(rows[y]) - 1)
        if (x, y) not in protected
    ]
    index = 0
    for value in desired:
        if len(current) >= target_unique or index >= len(candidates):
            break
        if value in current:
            continue
        x, y = candidates[index]
        rows[y][x] = value
        current.add(value)
        index += 1


def _soften_singletons(rows: MapRows, protected: set[tuple[int, int]]) -> None:
    if not rows:
        return
    changes: list[tuple[int, int, int]] = []
    for y in range(1, len(rows) - 1):
        for x in range(1, len(rows[y]) - 1):
            if (x, y) in protected:
                continue
            here = int(rows[y][x])
            neighbors = [int(rows[ny][nx]) for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))]
            if all(abs(here - other) > 4 for other in neighbors):
                changes.append((x, y, round(sum(neighbors) / len(neighbors))))
    for x, y, value in changes:
        rows[y][x] = _clamp_height(value)


def _connected_varied_field(width: int, height: int, base: int, target_range: int) -> MapRows:
    step = max(1, min(2, target_range // 4))
    rows = filled_rows(width, height, base)
    for y in range(height):
        for x in range(width):
            rows[y][x] = _clamp_height(base + (((x + y) % 5) - 2) * step)
    return rows


def _blocked_ratio(rows: MapRows) -> float:
    total = 0
    blocked = 0
    for y, row in enumerate(rows):
        for x, value in enumerate(row):
            for nx, ny in ((x + 1, y), (x, y + 1)):
                if ny >= len(rows) or nx >= len(row):
                    continue
                total += 1
                if abs(int(value) - int(rows[ny][nx])) > 4:
                    blocked += 1
    return (blocked / total) if total else 0.0


def _stretch_range(rows: MapRows, base: int, target_range: int) -> None:
    values = [int(value) for row in rows for value in row]
    if not values:
        return
    current_min = min(values)
    current_max = max(values)
    current_range = current_max - current_min
    if current_range >= target_range:
        return
    low = _clamp_height(base - target_range // 2)
    high = _clamp_height(low + target_range)
    if current_range <= 0:
        for y, row in enumerate(rows):
            for x, _value in enumerate(row):
                row[x] = _clamp_height(low + ((x + y) % max(1, target_range + 1)))
        return
    for y, row in enumerate(rows):
        for x, value in enumerate(row):
            ratio = (int(value) - current_min) / current_range
            row[x] = _clamp_height(low + round((high - low) * ratio))


def _smooth_pass(rows: MapRows) -> MapRows:
    height = len(rows)
    width = len(rows[0]) if rows else 0
    out = filled_rows(width, height, 0)
    for y in range(height):
        for x in range(width):
            values = [int(rows[y][x])]
            for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if 0 <= nx < width and 0 <= ny < height:
                    values.append(int(rows[ny][nx]))
            out[y][x] = _clamp_height(round(sum(values) / len(values)))
    return out


def _clamp_height(value: int) -> int:
    return max(0, min(0xFF, int(value)))
