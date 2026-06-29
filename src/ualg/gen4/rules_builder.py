"""Build the Generator4 campaign-rule dataset from authored levels."""

from __future__ import annotations

import json
import re
from collections import deque
from pathlib import Path
from typing import Any

from ..models import MapRows
from ..constants import level_id_from_filename
from ..gen3.corpus_builder import original_levels_dir
from ..gen3.ldf_reader import ParsedLevel, parse_ldf
from ._profile_data import level_ids_for, targets_for

_PACKAGE_ROOT = Path(__file__).resolve().parent.parent
_REPO_ROOT = _PACKAGE_ROOT.parent.parent
RULES_FILENAME = "gen4_rules.json"
OUTPUT_PATH = _PACKAGE_ROOT / "data" / RULES_FILENAME

_CORPORA = {
    "vanilla": "LEVELS-vanilla",
    "metropolisDawn": "LEVELS-metropolis-dawn",
}

_PROFILE_SOURCE = {
    "original": "vanilla",
    "md-ghorkov": "metropolisDawn",
    "md-taerkasten": "metropolisDawn",
}


def build_rules(repo_root: Path | None = None) -> dict[str, Any]:
    """Parse original levels into deterministic Generator4 rules."""

    levels = _parsed_levels(repo_root)
    profiles: dict[str, dict[str, Any]] = {}
    for profile_id, source in _PROFILE_SOURCE.items():
        level_ids = level_ids_for(profile_id)
        records: list[dict[str, Any]] = []
        for level_id in level_ids:
            name = f"L{level_id:02d}{level_id:02d}"
            try:
                level = levels[(source, name)]
            except KeyError as exc:
                raise FileNotFoundError(f"missing source level {name} for Generator4 profile {profile_id}") from exc
            records.append(_level_record(level, profile_id))
        profiles[profile_id] = {"source": source, "levels": records}
    return {"version": 1, "profiles": profiles}


def write_rules(rules: dict[str, Any], output: Path | None = None) -> Path:
    target = output or OUTPUT_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(rules, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return target


def _parsed_levels(repo_root: Path | None) -> dict[tuple[str, str], ParsedLevel]:
    levels_dir = original_levels_dir(repo_root or _REPO_ROOT)
    if not levels_dir.is_dir():
        raise FileNotFoundError(
            f"original-levels directory not found at {levels_dir}. "
            f"Generator4 needs the raw levels to build {RULES_FILENAME}."
        )

    levels: dict[tuple[str, str], ParsedLevel] = {}
    for source, subdir in _CORPORA.items():
        directory = levels_dir / subdir
        if not directory.is_dir():
            continue
        for path in sorted(p for p in directory.iterdir() if p.is_file() and p.suffix.lower() == ".ldf"):
            text = path.read_text(encoding="latin-1").replace("\r\n", "\n").replace("\r", "\n")
            name = path.stem.upper()
            level = parse_ldf(text, name=name, source=source)
            if "typ" in level.maps:
                levels[(source, name)] = level
    if not levels:
        raise FileNotFoundError(f"no original levels parsed under {levels_dir}.")
    return levels


def _level_record(level: ParsedLevel, profile_id: str) -> dict[str, Any]:
    level_id = level_id_from_filename(level.name)
    player_owner = int(level.player_owner)
    enemy_owners = [owner for owner in level.present_owners if owner not in {0, 7, player_owner}]
    enemy_enables = {
        str(enable["owner"]): {
            "vehicles": list(enable.get("vehicles", [])),
            "buildings": list(enable.get("buildings", [])),
        }
        for enable in level.enables
        if int(enable["owner"]) in enemy_owners
    }
    player_enables = [
        {
            "owner": int(enable["owner"]),
            "vehicles": list(enable.get("vehicles", [])),
            "buildings": list(enable.get("buildings", [])),
        }
        for enable in level.enables
        if int(enable["owner"]) == player_owner
    ]
    upgrade_gems = [_gem_record(gem) for gem in level.gems]
    return {
        "level_id": level_id,
        "name": level.name,
        "source_name": level.name,
        "source": level.source,
        "tileset": level.tileset,
        "width": level.width,
        "height": level.height,
        "header": level.header,
        "mbmap": level.mbmap,
        "dbmap": level.dbmap,
        "mission_targets": list(targets_for(profile_id, level_id)),
        "player_owner": player_owner,
        "present_owners": level.present_owners,
        "enemy_owners": enemy_owners,
        "enemy_enables": enemy_enables,
        "player_enables": player_enables,
        "player_baseline": {
            "include": _first_include(level.prototype),
            "prototype": level.prototype,
            "structured": _prototype_records(level.prototype),
        },
        "upgrade_gems": upgrade_gems,
        "new_unlocks": _new_unlocks(upgrade_gems, player_owner),
        "placement_stats": _placement_stats(level),
        "height_stats": _height_stats(level.maps.get("hgt", []), _placement_cells(level)),
        "gates": level.gates,
        "items": level.items,
        "robos": level.robos,
        "squads": level.squads,
    }


def _first_include(lines: list[str]) -> str:
    for line in lines:
        if line.strip().lower().startswith("include"):
            return line.strip()
    return ""


def _gem_record(gem: dict[str, Any]) -> dict[str, Any]:
    raw = list(gem["raw"])
    return {
        "raw": raw,
        "sec_x": _int_or_none(gem.get("sec_x")),
        "sec_y": _int_or_none(gem.get("sec_y")),
        "building": _int_or_none(gem.get("building")),
        "type": _int_or_none(gem.get("type")),
        "mb_status": _first_raw_value(raw, "mb_status"),
        "actions": _modification_records(raw),
    }


def _prototype_records(lines: list[str]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    block: list[str] = []
    for line in lines:
        stripped = line.strip()
        lower = stripped.lower()
        if lower.startswith("modify_"):
            block = [stripped]
            continue
        if block:
            block.append(stripped)
            if lower == "end":
                records.extend(_modification_records(block))
                block = []
    return records


_MODIFY_RE = re.compile(r"^(modify_vehicle|modify_weapon|modify_building)\s+(-?\d+)", re.IGNORECASE)
_KV_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*(?:;.*)?$")


def _modification_records(lines: list[str]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    stack: list[dict[str, Any]] = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith(";"):
            continue
        match = _MODIFY_RE.match(stripped)
        if match:
            record = {
                "kind": match.group(1).split("_", 1)[1].lower(),
                "id": int(match.group(2)),
                "properties": {},
                "enable_owners": [],
            }
            stack.append(record)
            continue
        if stripped.lower() == "end" and stack:
            records.append(stack.pop())
            continue
        kv = _KV_RE.match(stripped)
        if kv and stack:
            key = kv.group(1).lower()
            value = _coerce(kv.group(2))
            stack[-1]["properties"][key] = value
            if key == "enable":
                stack[-1]["enable_owners"].append(int(value))
    records.extend(reversed(stack))
    return records


def _new_unlocks(gems: list[dict[str, Any]], player_owner: int) -> list[dict[str, Any]]:
    unlocks: list[dict[str, Any]] = []
    for gem in gems:
        for action in gem.get("actions", []):
            if player_owner not in action.get("enable_owners", []):
                continue
            unlocks.append({
                "kind": action["kind"],
                "id": int(action["id"]),
                "owner": player_owner,
                "building": gem.get("building"),
            })
    return unlocks


def _placement_stats(level: ParsedLevel) -> dict[str, Any]:
    return {
        "robos": [_entity_cell(robo) for robo in level.robos],
        "squads": [_entity_cell(squad) for squad in level.squads],
        "gates": [{"x": gate.get("sec_x"), "y": gate.get("sec_y")} for gate in level.gates],
        "items": [{"x": item.get("sec_x"), "y": item.get("sec_y")} for item in level.items],
        "gems": [{"x": gem.get("sec_x"), "y": gem.get("sec_y")} for gem in level.gems],
    }


def _placement_cells(level: ParsedLevel) -> dict[str, list[dict[str, int]]]:
    cells: dict[str, list[dict[str, int]]] = {"robos": [], "squads": [], "gates": [], "items": [], "gems": []}
    for robo in level.robos:
        cell = _entity_cell(robo)
        if cell:
            cells["robos"].append(cell)
    for squad in level.squads:
        cell = _entity_cell(squad)
        if cell:
            cells["squads"].append(cell)
    for gate in level.gates:
        cells["gates"].append({"x": int(gate.get("sec_x", 0)), "y": int(gate.get("sec_y", 0))})
        for key in gate.get("keysecs", []):
            cells["gates"].append({"x": int(key["x"]), "y": int(key["y"])})
    for item in level.items:
        cells["items"].append({"x": int(item.get("sec_x", 0)), "y": int(item.get("sec_y", 0))})
        for key in item.get("keysecs", []):
            cells["items"].append({"x": int(key["x"]), "y": int(key["y"])})
    for gem in level.gems:
        if gem.get("sec_x") is not None and gem.get("sec_y") is not None:
            cells["gems"].append({"x": int(gem["sec_x"]), "y": int(gem["sec_y"])})
    return cells


def _entity_cell(entity: dict[str, Any]) -> dict[str, int]:
    if entity.get("pos_x") is None or entity.get("pos_z") is None:
        return {}
    x = max(0, int(round((int(entity["pos_x"]) - 1) / 1200 - 0.5)))
    y = max(0, int(round((-(int(entity["pos_z"]) - 1)) / 1200 - 0.5)))
    return {"x": x, "y": y}


def _height_stats(rows: MapRows, assignments: dict[str, list[dict[str, int]]]) -> dict[str, Any]:
    if not rows:
        return {
            "blocked_edge_ratio": 0.0,
            "component_sizes": [],
            "assignments": assignments,
            "max_adjacent_delta": 0,
            "median": 0x7F,
        }
    height = len(rows)
    width = len(rows[0])
    total_edges = 0
    blocked_edges = 0
    max_delta = 0
    values: list[int] = []
    for y, row in enumerate(rows):
        values.extend(int(value) for value in row)
        for x, value in enumerate(row):
            for nx, ny in ((x + 1, y), (x, y + 1)):
                if nx >= width or ny >= height:
                    continue
                total_edges += 1
                delta = abs(int(value) - int(rows[ny][nx]))
                max_delta = max(max_delta, delta)
                if delta > 4:
                    blocked_edges += 1
    component_ids, sizes = _height_components(rows)
    assigned = {
        key: [
            {**cell, "component": component_ids.get((cell["x"], cell["y"]), -1)}
            for cell in cells
            if "x" in cell and "y" in cell
        ]
        for key, cells in assignments.items()
    }
    values.sort()
    median = values[len(values) // 2] if values else 0x7F
    return {
        "blocked_edge_ratio": (blocked_edges / total_edges) if total_edges else 0.0,
        "component_sizes": sizes,
        "assignments": assigned,
        "max_adjacent_delta": max_delta,
        "median": median,
    }


def _height_components(rows: MapRows) -> tuple[dict[tuple[int, int], int], list[int]]:
    if not rows:
        return {}, []
    height = len(rows)
    width = len(rows[0])
    component_ids: dict[tuple[int, int], int] = {}
    sizes: list[int] = []
    for y in range(height):
        for x in range(width):
            if (x, y) in component_ids:
                continue
            component = len(sizes)
            size = 0
            queue: deque[tuple[int, int]] = deque([(x, y)])
            component_ids[(x, y)] = component
            while queue:
                cx, cy = queue.popleft()
                size += 1
                for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                    if not (0 <= nx < width and 0 <= ny < height) or (nx, ny) in component_ids:
                        continue
                    if abs(int(rows[cy][cx]) - int(rows[ny][nx])) > 4:
                        continue
                    component_ids[(nx, ny)] = component
                    queue.append((nx, ny))
            sizes.append(size)
    return component_ids, sizes


def _first_raw_value(lines: list[str], key: str) -> Any:
    target = key.lower()
    for line in lines:
        match = _KV_RE.match(line.strip())
        if match and match.group(1).lower() == target:
            return _coerce(match.group(2))
    return None


def _coerce(value: str) -> Any:
    text = value.split(";", 1)[0].strip()
    digits = text[1:] if text.startswith("-") else text
    if digits.isdigit():
        return int(text)
    return text


def _int_or_none(value: Any) -> int | None:
    return None if value is None else int(value)
