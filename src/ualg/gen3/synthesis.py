"""Phase 2: Wave Function Collapse terrain synthesis.

Generator3 Remix copies an authored level's terrain. Synthesis instead *learns*
which terrain tiles sit next to which (4-neighbour adjacency) from the corpus
and collapses a fresh grid that obeys those local rules -- producing novel maps
with connected streets and plausible blocks. No tile legend is needed; the
rules are purely empirical.

The energy-wall border is fixed to the canonical frame tiles; only interior
cells are collapsed. WFC restarts on contradiction; a scanline-Markov fallback
guarantees completion if WFC cannot converge.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from functools import lru_cache

from ..constants import (
    TYP_BORDER_BOTTOM,
    TYP_BORDER_BOTTOM_LEFT,
    TYP_BORDER_BOTTOM_RIGHT,
    TYP_BORDER_LEFT,
    TYP_BORDER_RIGHT,
    TYP_BORDER_TOP,
    TYP_BORDER_TOP_LEFT,
    TYP_BORDER_TOP_RIGHT,
)
from ..models import MapRows
from ..rng import MSVCRTRandom
from .corpus import skeletons_for_source

_MAX_WFC_RESTARTS = 24


@dataclass
class AdjacencyModel:
    """Learned 4-neighbour tile adjacency for one tileset."""

    right: dict[int, set[int]] = field(default_factory=lambda: defaultdict(set))
    left: dict[int, set[int]] = field(default_factory=lambda: defaultdict(set))
    down: dict[int, set[int]] = field(default_factory=lambda: defaultdict(set))
    up: dict[int, set[int]] = field(default_factory=lambda: defaultdict(set))
    weights: dict[int, int] = field(default_factory=lambda: defaultdict(int))
    interior_tiles: set[int] = field(default_factory=set)

    def weighted_choice(self, rng: MSVCRTRandom, options: set[int]) -> int:
        ordered = sorted(options)
        total = sum(self.weights.get(tile, 1) for tile in ordered)
        pick = rng.rand_mod(total) if total > 0 else 0
        cursor = 0
        for tile in ordered:
            cursor += self.weights.get(tile, 1)
            if pick < cursor:
                return tile
        return ordered[-1]


def border_tile(x: int, y: int, width: int, height: int) -> int | None:
    """Return the fixed energy-wall tile for a border cell, else ``None``."""

    left, right = 0, width - 1
    top, bottom = 0, height - 1
    if y == top:
        if x == left:
            return TYP_BORDER_TOP_LEFT
        if x == right:
            return TYP_BORDER_TOP_RIGHT
        return TYP_BORDER_TOP
    if y == bottom:
        if x == left:
            return TYP_BORDER_BOTTOM_LEFT
        if x == right:
            return TYP_BORDER_BOTTOM_RIGHT
        return TYP_BORDER_BOTTOM
    if x == left:
        return TYP_BORDER_LEFT
    if x == right:
        return TYP_BORDER_RIGHT
    return None


@lru_cache(maxsize=None)
def adjacency_model_for(source: str, tileset: int) -> AdjacencyModel:
    """Build (and cache) the adjacency model for a corpus source + tileset."""

    model = AdjacencyModel()
    samples = 0
    for skeleton in skeletons_for_source(source):
        if skeleton.tileset != tileset:
            continue
        rows = skeleton.maps()["typ"]
        height = len(rows)
        samples += 1
        for y, row in enumerate(rows):
            width = len(row)
            for x, tile in enumerate(row):
                if 0 < x < width - 1 and 0 < y < height - 1:
                    model.interior_tiles.add(tile)
                    model.weights[tile] += 1
                if x + 1 < width:
                    model.right[tile].add(row[x + 1])
                    model.left[row[x + 1]].add(tile)
                if y + 1 < height:
                    model.down[tile].add(rows[y + 1][x])
                    model.up[rows[y + 1][x]].add(tile)
    if samples == 0:
        raise ValueError(f"no corpus samples for source {source!r} tileset {tileset}")
    return model


def _allowed_for_neighbor(model: AdjacencyModel, domain: set[int], direction: str) -> set[int]:
    table = getattr(model, direction)
    allowed: set[int] = set()
    for tile in domain:
        allowed |= table.get(tile, set())
    return allowed


def _propagate(grid: list[list[set[int]]], model: AdjacencyModel, start: tuple[int, int]) -> bool:
    width = len(grid[0])
    height = len(grid)
    stack = [start]
    # (dx, dy, direction used to constrain the neighbor from the current cell)
    neighbours = ((1, 0, "right"), (-1, 0, "left"), (0, 1, "down"), (0, -1, "up"))
    while stack:
        x, y = stack.pop()
        current = grid[y][x]
        for dx, dy, direction in neighbours:
            nx, ny = x + dx, y + dy
            if not (0 <= nx < width and 0 <= ny < height):
                continue
            neighbour = grid[ny][nx]
            if len(neighbour) <= 1:
                continue
            allowed = _allowed_for_neighbor(model, current, direction)
            new_domain = neighbour & allowed
            if not new_domain:
                return False
            if len(new_domain) < len(neighbour):
                grid[ny][nx] = new_domain
                stack.append((nx, ny))
    return True


def _observe(grid: list[list[set[int]]], rng: MSVCRTRandom) -> tuple[int, int] | None:
    best: tuple[int, int] | None = None
    best_entropy = None
    for y, row in enumerate(grid):
        for x, domain in enumerate(row):
            if len(domain) <= 1:
                continue
            entropy = len(domain)
            if best_entropy is None or entropy < best_entropy:
                best_entropy = entropy
                best = (x, y)
    return best


def _solve_wfc(width: int, height: int, model: AdjacencyModel, rng: MSVCRTRandom) -> MapRows | None:
    interior = model.interior_tiles
    if not interior:
        return None
    grid: list[list[set[int]]] = []
    for y in range(height):
        row: list[set[int]] = []
        for x in range(width):
            fixed = border_tile(x, y, width, height)
            row.append({fixed} if fixed is not None else set(interior))
        grid.append(row)

    # Seed propagation from every fixed border cell.
    for y in range(height):
        for x in range(width):
            if len(grid[y][x]) == 1:
                if not _propagate(grid, model, (x, y)):
                    return None

    while True:
        cell = _observe(grid, rng)
        if cell is None:
            break
        x, y = cell
        choice = model.weighted_choice(rng, grid[y][x])
        grid[y][x] = {choice}
        if not _propagate(grid, model, (x, y)):
            return None

    return [[next(iter(grid[y][x])) for x in range(width)] for y in range(height)]


def _scanline_fallback(width: int, height: int, model: AdjacencyModel, rng: MSVCRTRandom) -> MapRows:
    """Always-terminating generator used when WFC cannot converge."""

    interior = model.interior_tiles
    rows: MapRows = []
    for y in range(height):
        row: list[int] = []
        for x in range(width):
            fixed = border_tile(x, y, width, height)
            if fixed is not None:
                row.append(fixed)
                continue
            candidates = set(interior)
            left_options = model.right.get(row[x - 1]) if x > 0 else None
            if left_options:
                candidates &= left_options
            up_options = model.down.get(rows[y - 1][x]) if y > 0 else None
            if up_options and candidates & up_options:
                candidates &= up_options
            if not candidates:
                candidates = left_options or set(interior)
            row.append(model.weighted_choice(rng, candidates or interior))
        rows.append(row)
    return rows


def synthesize_typ_map(
    source: str,
    tileset: int,
    width: int,
    height: int,
    rng: MSVCRTRandom,
) -> tuple[MapRows, str]:
    """Synthesize a terrain map. Returns the rows and the method used."""

    model = adjacency_model_for(source, tileset)
    for _ in range(_MAX_WFC_RESTARTS):
        result = _solve_wfc(width, height, model, rng)
        if result is not None:
            return result, "wfc"
    return _scanline_fallback(width, height, model, rng), "scanline"
