"""Generator4 validation."""

from __future__ import annotations

import re

from ..constants import (
    BUILDING_TYP_BY_ID,
    STANDARD_BOMB_BLUEPRINTS,
    TECH_UPGRADE_BUILDING_TILESETS,
    TECH_UPGRADE_BUILDING_TYP_BY_ID,
    TILESET6_BOMB_BLUEPRINTS,
    TILESET6_BOMB_DIAGONAL_KEY_TYP_BY_OFFSET,
    TYP_BEAM_GATE_NO_ROAD,
    TYP_BEAM_GATE_WITH_ROAD,
    TYP_BOMB_STANDARD,
    TYP_BORDER_BOTTOM,
    TYP_BORDER_BOTTOM_LEFT,
    TYP_BORDER_BOTTOM_RIGHT,
    TYP_BORDER_LEFT,
    TYP_BORDER_RIGHT,
    TYP_BORDER_TOP,
    TYP_BORDER_TOP_LEFT,
    TYP_BORDER_TOP_RIGHT,
    TYP_GATE_CLOSED_1,
    TYP_GATE_CLOSED_2,
    TYP_TILESET6_BOMB,
)
from ..ldf import parse_maps
from ..models import MapRows
from ..gen3.validate import validate_level as validate_gen3_level
from .context import _Gen4Level
from .infrastructure import station_info_by_building
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
    problems.extend(_validate_gates(level))
    problems.extend(_validate_items(level))
    problems.extend(_validate_gems(level))
    problems.extend(_validate_infrastructure(level))
    problems.extend(_validate_functional_collisions(level))
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
    typ = level.maps.get("typ", [])
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
        expected_typ = _tech_upgrade_typ(level, building)
        if _tech_upgrade_tileset_invalid(level, building):
            problems.append("upgrade gem building 60 is only valid in tileset 5")
        elif expected_typ is not None and (not (0 <= y < len(typ) and 0 <= x < len(typ[y])) or typ[y][x] != expected_typ):
            problems.append("upgrade gem typ_map value is incompatible with building id")
    return problems


def _validate_gates(level: _Gen4Level) -> list[str]:
    problems: list[str] = []
    typ = level.maps.get("typ", [])
    blg = level.maps.get("blg", [])
    for gate in level.gates:
        x = int(gate.get("sec_x", -1))
        y = int(gate.get("sec_y", -1))
        expected_typ = _beam_gate_typ(gate)
        if not (0 <= y < len(typ) and 0 <= x < len(typ[y])) or typ[y][x] != expected_typ:
            problems.append("beam gate typ_map value is incompatible with closed/opened blueprints")
        if 0 <= y < len(blg) and 0 <= x < len(blg[y]) and blg[y][x] != 0:
            problems.append("beam gate blg_map cell must be empty")
    return problems


def _validate_items(level: _Gen4Level) -> list[str]:
    problems: list[str] = []
    typ = level.maps.get("typ", [])
    blg = level.maps.get("blg", [])
    for item in level.items:
        x = int(item.get("sec_x", -1))
        y = int(item.get("sec_y", -1))
        expected_typ = _item_typ(item)
        first_bp = _first_item_blueprint(item)
        if expected_typ is not None and (not (0 <= y < len(typ) and 0 <= x < len(typ[y])) or typ[y][x] != expected_typ):
            problems.append("bomb typ_map value is incompatible with item blueprints")
        if first_bp is not None and (not (0 <= y < len(blg) and 0 <= x < len(blg[y])) or blg[y][x] != first_bp):
            problems.append("bomb blueprint id not reflected in blg_map")
        blueprints = _item_blueprints(item)
        if blueprints == TILESET6_BOMB_BLUEPRINTS and int(getattr(level, "tileset", 0)) != 6:
            problems.append("tileset 6 bomb blueprints used outside tileset 6")
            continue
        for key in item.get("keysecs", []):
            key_x = int(key.get("x", -1))
            key_y = int(key.get("y", -1))
            if not (0 <= key_y < len(typ) and 0 <= key_x < len(typ[key_y])):
                problems.append("bomb keysec coordinates out of bounds")
                continue
            expected_key_typ = _item_key_typ(level, item, key_x, key_y)
            if isinstance(expected_key_typ, set):
                if typ[key_y][key_x] not in expected_key_typ:
                    problems.append("bomb keysec typ_map value is incompatible with item blueprints")
            elif typ[key_y][key_x] != expected_key_typ:
                problems.append("bomb keysec typ_map value is incompatible with item blueprints")
            if 0 <= key_y < len(blg) and 0 <= key_x < len(blg[key_y]) and blg[key_y][key_x] != 0:
                problems.append("bomb keysec blg_map cell must be empty")
    return problems


def _validate_infrastructure(level: _Gen4Level) -> list[str]:
    problems: list[str] = []
    blg = level.maps.get("blg", [])
    typ = level.maps.get("typ", [])
    own = level.maps.get("own", [])
    info_by_building = station_info_by_building()
    participating = {level.player_faction}
    participating.update(int(owner) for owner in level.legal_vehicles_by_owner)
    participating.update(int(robo.get("owner", 0)) for robo in level.robos)
    for station in level.infrastructure:
        x = int(station.get("x", -1))
        y = int(station.get("y", -1))
        building = int(station.get("building", 0))
        owner = int(station.get("owner", 0))
        category = str(station.get("category", ""))
        if not _interior(level, x, y):
            problems.append("infrastructure coordinates out of bounds")
            continue
        if not (0 <= y < len(blg) and 0 <= x < len(blg[y])) or int(blg[y][x]) != building:
            problems.append("infrastructure building id not reflected in blg_map")
        typ_id = BUILDING_TYP_BY_ID.get(building)
        if typ_id is not None and (not (0 <= y < len(typ) and 0 <= x < len(typ[y])) or int(typ[y][x]) != typ_id):
            problems.append("infrastructure typ_map value is incompatible with building id")
        info = info_by_building.get(building)
        if info is None or info.category != category:
            problems.append("infrastructure building category is unknown")
        if category in {"power", "flak", "radar"} and owner not in participating:
            if not (category == "power" and owner == 7 and station.get("source_owner_7")):
                problems.append("faction-owned infrastructure has no participating owner")
        if owner != 0 and (not (0 <= y < len(own) and 0 <= x < len(own[y])) or int(own[y][x]) != owner):
            problems.append("infrastructure owner not reflected in own_map")
    return problems


def _validate_functional_collisions(level: _Gen4Level) -> list[str]:
    occupied: dict[tuple[int, int], str] = {}
    problems: list[str] = []

    def add(cell: tuple[int, int], label: str) -> None:
        previous = occupied.setdefault(cell, label)
        if previous != label:
            problems.append(f"functional placements collide at {cell[0]},{cell[1]}")

    for robo in level.robos:
        cell = _world_cell(robo.get("pos_x"), robo.get("pos_z"))
        if cell is not None:
            add(cell, "host")
    for gate in level.gates:
        add((int(gate["sec_x"]), int(gate["sec_y"])), "gate")
        for key in gate.get("keysecs", []):
            add((int(key["x"]), int(key["y"])), "gate-key")
    for item in level.items:
        add((int(item["sec_x"]), int(item["sec_y"])), "item")
        for key in item.get("keysecs", []):
            add((int(key["x"]), int(key["y"])), "item-key")
    for gem in level.gems:
        x = y = None
        for line in gem:
            if match := _GEM_SEC_X_RE.match(line):
                x = int(match.group(1))
            elif match := _GEM_SEC_Y_RE.match(line):
                y = int(match.group(1))
        if x is not None and y is not None:
            add((x, y), "gem")
    for station in level.infrastructure:
        add((int(station["x"]), int(station["y"])), "infrastructure")
    return problems[:1]


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


def _beam_gate_typ(gate: dict[str, object]) -> int:
    closed_bp = int(gate.get("closed_bp", 5))
    opened_bp = int(gate.get("opened_bp", 6))
    if (closed_bp, opened_bp) == (25, 26):
        return TYP_BEAM_GATE_NO_ROAD
    if (closed_bp, opened_bp) == (5, 6):
        return TYP_BEAM_GATE_WITH_ROAD
    return TYP_BEAM_GATE_WITH_ROAD


def _item_typ(item: dict[str, object]) -> int | None:
    blueprints = _item_blueprints(item)
    if blueprints == STANDARD_BOMB_BLUEPRINTS:
        return TYP_BOMB_STANDARD
    if blueprints == TILESET6_BOMB_BLUEPRINTS:
        return TYP_TILESET6_BOMB
    first = _first_item_blueprint(item)
    return BUILDING_TYP_BY_ID.get(first) if first is not None else None


def _item_key_typ(level: _Gen4Level, item: dict[str, object], x: int, y: int) -> int | set[int]:
    blueprints = _item_blueprints(item)
    if blueprints == TILESET6_BOMB_BLUEPRINTS and int(getattr(level, "tileset", 0)) == 6:
        offset = (x - int(item["sec_x"]), y - int(item["sec_y"]))
        diagonal_typ = TILESET6_BOMB_DIAGONAL_KEY_TYP_BY_OFFSET.get(offset)
        if diagonal_typ is not None:
            return diagonal_typ
    return {TYP_GATE_CLOSED_1, TYP_GATE_CLOSED_2}


def _item_blueprints(item: dict[str, object]) -> tuple[int, int, int] | None:
    values: list[int] = []
    for key in ("inactive_bp", "active_bp", "trigger_bp"):
        value = item.get(key)
        if value is None:
            return None
        values.append(int(value))
    return values[0], values[1], values[2]


def _first_item_blueprint(item: dict[str, object]) -> int | None:
    for key in ("inactive_bp", "active_bp", "trigger_bp"):
        value = item.get(key)
        if value is not None:
            return int(value)
    return None


def _tech_upgrade_typ(level: _Gen4Level, building: int) -> int | None:
    if _tech_upgrade_tileset_invalid(level, building):
        return None
    return TECH_UPGRADE_BUILDING_TYP_BY_ID.get(building)


def _tech_upgrade_tileset_invalid(level: _Gen4Level, building: int) -> bool:
    allowed_tilesets = TECH_UPGRADE_BUILDING_TILESETS.get(building)
    return allowed_tilesets is not None and int(getattr(level, "tileset", 0)) not in allowed_tilesets
