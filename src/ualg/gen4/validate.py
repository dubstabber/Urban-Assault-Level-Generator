"""Generator4 validation."""

from __future__ import annotations

import re

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
from ..ldf import parse_maps
from ..models import MapRows
from ..gen3.validate import validate_level as validate_gen3_level
from .context import _Gen4Level
from .passability import route_blockers

_MAX_SQUAD_UNITS = 32
_MAP_KEYS = ("typ", "own", "hgt", "blg")
_GEM_BUILDING_RE = re.compile(r"^\s*building\s*=\s*(-?\d+)", re.IGNORECASE)
_GEM_SEC_X_RE = re.compile(r"^\s*sec_x\s*=\s*(-?\d+)", re.IGNORECASE)
_GEM_SEC_Y_RE = re.compile(r"^\s*sec_y\s*=\s*(-?\d+)", re.IGNORECASE)


def validate_level(level: _Gen4Level, text: str | None = None) -> list[str]:
    problems = list(validate_gen3_level(level))
    problems.extend(_validate_dimensions(level))
    problems.extend(_validate_energy_wall(level.maps.get("typ", [])))
    problems.extend(_validate_entities(level))
    problems.extend(_validate_enables(level))
    problems.extend(_validate_squads(level))
    problems.extend(route_blockers(level.maps.get("hgt", []), level.required_route_cells))
    problems.extend(_validate_gems(level))
    if text is not None:
        problems.extend(_validate_rendered_blocks(text))
    return list(dict.fromkeys(problems))


def _validate_dimensions(level: _Gen4Level) -> list[str]:
    problems: list[str] = []
    for key in _MAP_KEYS:
        rows = level.maps.get(key)
        if not rows:
            problems.append(f"{key}_map missing")
            continue
        if len(rows) != level.height or any(len(row) != level.width for row in rows):
            problems.append(f"{key}_map dimensions do not match {level.width}x{level.height}")
    return problems


def _validate_energy_wall(rows: MapRows) -> list[str]:
    if not rows:
        return []
    width = len(rows[0])
    height = len(rows)
    expected = {
        (0, 0): TYP_BORDER_TOP_LEFT,
        (width - 1, 0): TYP_BORDER_TOP_RIGHT,
        (0, height - 1): TYP_BORDER_BOTTOM_LEFT,
        (width - 1, height - 1): TYP_BORDER_BOTTOM_RIGHT,
    }
    problems: list[str] = []
    for (x, y), value in expected.items():
        if rows[y][x] != value:
            problems.append("typ_map energy-wall corner altered")
            break
    if any(rows[0][x] != TYP_BORDER_TOP for x in range(1, width - 1)):
        problems.append("typ_map top energy-wall border altered")
    if any(rows[height - 1][x] != TYP_BORDER_BOTTOM for x in range(1, width - 1)):
        problems.append("typ_map bottom energy-wall border altered")
    if any(rows[y][0] != TYP_BORDER_LEFT for y in range(1, height - 1)):
        problems.append("typ_map left energy-wall border altered")
    if any(rows[y][width - 1] != TYP_BORDER_RIGHT for y in range(1, height - 1)):
        problems.append("typ_map right energy-wall border altered")
    return problems


def _validate_entities(level: _Gen4Level) -> list[str]:
    problems: list[str] = []
    for robo in level.robos:
        cell = _world_cell(robo.get("pos_x"), robo.get("pos_z"))
        if cell is None or not _interior(level, *cell):
            problems.append("host station coordinates out of bounds")
            break
    for squad in level.squads:
        cell = _world_cell(squad.get("pos_x"), squad.get("pos_z"))
        if cell is None or not _interior(level, *cell):
            problems.append("squad coordinates out of bounds")
            break
        if int(squad.get("num", 0)) > _MAX_SQUAD_UNITS:
            problems.append("squad exceeds 32 units")
            break
    return problems


def _validate_enables(level: _Gen4Level) -> list[str]:
    problems: list[str] = []
    source = level.archetype.record
    source_enables = {
        int(owner): {
            "vehicles": set(int(vehicle) for vehicle in data.get("vehicles", [])),
            "buildings": set(int(building) for building in data.get("buildings", [])),
        }
        for owner, data in source.get("enemy_enables", {}).items()
    }
    for enable in level.enables:
        owner = int(enable["owner"])
        if owner == level.player_faction:
            continue
        if owner not in source_enables:
            problems.append(f"begin_enable owner {owner} is not legal for archetype")
            continue
        illegal_vehicles = set(int(v) for v in enable.get("vehicles", [])) - source_enables[owner]["vehicles"]
        illegal_buildings = set(int(b) for b in enable.get("buildings", [])) - source_enables[owner]["buildings"]
        if illegal_vehicles:
            problems.append(f"begin_enable owner {owner} has illegal vehicles")
        if illegal_buildings:
            problems.append(f"begin_enable owner {owner} has illegal buildings")
    return problems


def _validate_squads(level: _Gen4Level) -> list[str]:
    problems: list[str] = []
    for squad in level.squads:
        owner = int(squad["owner"])
        if owner in {0, 7, level.player_faction}:
            continue
        if int(squad["vehicle"]) not in level.legal_vehicles_by_owner.get(owner, set()):
            problems.append(f"squad owner {owner} uses vehicle outside level enable pool")
            break
    return problems


def _validate_gems(level: _Gen4Level) -> list[str]:
    problems: list[str] = []
    blg = level.maps.get("blg", [])
    for gem in level.gems:
        x = y = building = None
        for line in gem:
            if match := _GEM_SEC_X_RE.match(line):
                x = int(match.group(1))
            elif match := _GEM_SEC_Y_RE.match(line):
                y = int(match.group(1))
            elif match := _GEM_BUILDING_RE.match(line):
                building = int(match.group(1))
        if x is None or y is None or building is None:
            problems.append("upgrade gem missing sec_x/sec_y/building")
            continue
        if not (0 <= y < len(blg) and 0 <= x < len(blg[y])) or blg[y][x] != building:
            problems.append("upgrade gem building id not reflected in blg_map")
    return problems


def _validate_rendered_blocks(text: str) -> list[str]:
    problems: list[str] = []
    if set(parse_maps(text)) != {"typ_map", "own_map", "hgt_map", "blg_map"}:
        problems.append("rendered maps do not round-trip")
    depth = 0
    action_depth = 0
    for line in text.replace("\r\n", "\n").split("\n"):
        stripped = line.strip().lower()
        head = stripped.split(None, 1)[0] if stripped else ""
        if head == "begin_action":
            action_depth += 1
        elif head == "end_action":
            action_depth -= 1
        elif head.startswith("begin_") and head != "begin_maps":
            depth += 1
        elif head.startswith("modify_"):
            depth += 1
        elif head == "end" and depth:
            depth -= 1
    if action_depth != 0:
        problems.append("gem action blocks are unbalanced")
    if depth != 0:
        problems.append("rendered LDF blocks are unbalanced")
    return problems


def _world_cell(pos_x: object, pos_z: object) -> tuple[int, int] | None:
    if pos_x is None or pos_z is None:
        return None
    x = int(round((int(pos_x) - 1) / 1200 - 0.5))
    y = int(round((-(int(pos_z) - 1)) / 1200 - 0.5))
    return x, y


def _interior(level: _Gen4Level, x: int, y: int) -> bool:
    return 0 < x < level.width - 1 and 0 < y < level.height - 1
