"""Build the Generator4 campaign-rule dataset from authored levels."""

from __future__ import annotations

import json
import math
import re
from collections import Counter, defaultdict, deque
from pathlib import Path
from typing import Any

from ..models import MapRows
from ..constants import BUILDING_TYP_BY_ID, level_id_from_filename
from ..gen3.corpus_builder import original_levels_dir
from ..gen3.ldf_reader import ParsedLevel, parse_ldf
from ._profile_data import level_ids_for, targets_for
from .infrastructure import station_info_by_building

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
    return {"version": 2, "profiles": profiles}


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
    placement_cells = _placement_cells(level)
    infrastructure_placements = _infrastructure_placements(level, placement_cells)
    terrain_assignments = {
        **placement_cells,
        "infrastructure": [{"x": int(item["x"]), "y": int(item["y"])} for item in infrastructure_placements],
    }
    terrain_profile = _terrain_profile(level.maps.get("hgt", []), terrain_assignments)
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
        "height_stats": terrain_profile,
        "terrain_profile": terrain_profile,
        "infrastructure_placements": infrastructure_placements,
        "infrastructure_profile": _infrastructure_profile(level, infrastructure_placements),
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


def _infrastructure_placements(level: ParsedLevel, assignments: dict[str, list[dict[str, int]]]) -> list[dict[str, Any]]:
    blg = level.maps.get("blg", [])
    if not blg:
        return []
    info_by_building = station_info_by_building()
    own = level.maps.get("own", [])
    typ = level.maps.get("typ", [])
    hgt = level.maps.get("hgt", [])
    component_ids, _sizes = _height_components(hgt)
    raw: list[dict[str, Any]] = []
    for y, row in enumerate(blg):
        for x, value in enumerate(row):
            building = int(value)
            info = info_by_building.get(building)
            if info is None:
                continue
            owner = int(own[y][x]) if y < len(own) and x < len(own[y]) else 0
            entry = {
                "category": info.category,
                "building": building,
                "typ": int(info.typ if info.typ is not None else _map_value(typ, x, y, BUILDING_TYP_BY_ID.get(building, 0))),
                "owner": owner,
                "expected_owner": int(info.expected_owner),
                "x": x,
                "y": y,
                "component": component_ids.get((x, y), -1),
                "cluster": -1,
                "near_host_owner": _near_host_owner(level, x, y),
                "distance_to_nearest_host": _distance_to_cells(x, y, assignments.get("robos", [])),
                "distance_to_gate": _distance_to_cells(x, y, assignments.get("gates", [])),
                "distance_to_required_object": _distance_to_cells(
                    x,
                    y,
                    assignments.get("robos", [])
                    + assignments.get("gates", [])
                    + assignments.get("items", [])
                    + assignments.get("gems", []),
                ),
                "height": _map_value(hgt, x, y, 0x7F),
                "local_height_delta_max": _local_height_delta(hgt, x, y),
                "edge_role": "decorative",
            }
            entry["edge_role"] = _edge_role(entry, level)
            raw.append(entry)
    _assign_infrastructure_clusters(raw)
    return raw


def _infrastructure_profile(level: ParsedLevel, placements: list[dict[str, Any]]) -> dict[str, Any]:
    counts = {category: 0 for category in ("power", "flak", "radar")}
    counts.update(Counter(str(item["category"]) for item in placements))
    counts_by_owner: dict[str, dict[str, int]] = {}
    for item in placements:
        owner_counts = counts_by_owner.setdefault(str(int(item["owner"])), {"power": 0, "flak": 0, "radar": 0})
        owner_counts[str(item["category"])] += 1

    clusters: dict[str, Counter[int]] = {category: Counter() for category in ("power", "flak", "radar")}
    for item in placements:
        clusters[str(item["category"])][int(item["cluster"])] += 1
    cluster_sizes = {
        category: sorted(size for cluster, size in category_clusters.items() if cluster >= 0)
        for category, category_clusters in clusters.items()
    }
    interior = max(1, (level.width - 2) * (level.height - 2))
    return {
        "counts": counts,
        "counts_by_owner": counts_by_owner,
        "cluster_sizes": cluster_sizes,
        "neutral_or_tutor_power_count": sum(
            1
            for item in placements
            if item["category"] == "power" and int(item["owner"]) in {0, 7}
        ),
        "has_radar": counts["radar"] > 0,
        "has_flak": counts["flak"] > 0,
        "max_station_density": len(placements) / interior,
    }


def _terrain_profile(rows: MapRows, assignments: dict[str, list[dict[str, int]]]) -> dict[str, Any]:
    if not rows:
        return {
            "blocked_edge_ratio": 0.0,
            "component_sizes": [],
            "assignments": assignments,
            "max_adjacent_delta": 0,
            "median": 0x7F,
            "min": 0x7F,
            "max": 0x7F,
            "range": 0,
            "unique_count": 1,
            "stdev": 0.0,
            "histogram": {"127": 1},
            "quantiles": {"p10": 0x7F, "p25": 0x7F, "p50": 0x7F, "p75": 0x7F, "p90": 0x7F},
            "feature_counts": {"plateaus": 0, "ramps": 0, "cliff_bands": 0, "isolated_peaks": 0, "basins": 0},
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
    median = _quantile(values, 0.5) if values else 0x7F
    histogram = Counter(values)
    mean = sum(values) / len(values) if values else float(0x7F)
    stdev = math.sqrt(sum((value - mean) ** 2 for value in values) / len(values)) if values else 0.0
    return {
        "median": median,
        "min": min(values) if values else 0x7F,
        "max": max(values) if values else 0x7F,
        "range": (max(values) - min(values)) if values else 0,
        "unique_count": len(histogram),
        "stdev": round(stdev, 4),
        "histogram": {str(value): count for value, count in sorted(histogram.items())},
        "quantiles": {
            "p10": _quantile(values, 0.10),
            "p25": _quantile(values, 0.25),
            "p50": median,
            "p75": _quantile(values, 0.75),
            "p90": _quantile(values, 0.90),
        },
        "blocked_edge_ratio": (blocked_edges / total_edges) if total_edges else 0.0,
        "max_adjacent_delta": max_delta,
        "component_sizes": sizes,
        "assignments": assigned,
        "feature_counts": _terrain_feature_counts(rows),
    }


def _map_value(rows: MapRows, x: int, y: int, default: int) -> int:
    if 0 <= y < len(rows) and 0 <= x < len(rows[y]):
        return int(rows[y][x])
    return int(default)


def _near_host_owner(level: ParsedLevel, x: int, y: int) -> int:
    best_owner = 0
    best_distance = 999999
    for robo in level.robos:
        cell = _entity_cell(robo)
        if not cell:
            continue
        distance = abs(x - int(cell["x"])) + abs(y - int(cell["y"]))
        if distance < best_distance:
            best_owner = int(robo.get("owner", 0))
            best_distance = distance
    return best_owner


def _distance_to_cells(x: int, y: int, cells: list[dict[str, int]]) -> int:
    distances = [
        abs(x - int(cell["x"])) + abs(y - int(cell["y"]))
        for cell in cells
        if "x" in cell and "y" in cell
    ]
    return min(distances) if distances else -1


def _local_height_delta(rows: MapRows, x: int, y: int) -> int:
    if not rows:
        return 0
    here = _map_value(rows, x, y, 0x7F)
    best = 0
    for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
        if 0 <= ny < len(rows) and 0 <= nx < len(rows[ny]):
            best = max(best, abs(here - int(rows[ny][nx])))
    return best


def _edge_role(entry: dict[str, Any], level: ParsedLevel) -> str:
    if int(entry["owner"]) == 0:
        return "decorative"
    if int(entry["distance_to_nearest_host"]) >= 0 and int(entry["distance_to_nearest_host"]) <= 3:
        return "base"
    if int(entry["local_height_delta_max"]) > 4:
        return "choke"
    if int(entry["owner"]) != int(entry["near_host_owner"]):
        return "front"
    far_threshold = max(6, (level.width + level.height) // 4)
    if int(entry["distance_to_nearest_host"]) > far_threshold:
        return "remote"
    return "front"


def _assign_infrastructure_clusters(placements: list[dict[str, Any]]) -> None:
    next_cluster = 0
    remaining = set(range(len(placements)))
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        category = placements[start]["category"]
        queue: deque[int] = deque([start])
        placements[start]["cluster"] = next_cluster
        while queue:
            index = queue.popleft()
            here = placements[index]
            linked = [
                other
                for other in remaining
                if placements[other]["category"] == category
                and max(abs(int(placements[other]["x"]) - int(here["x"])), abs(int(placements[other]["y"]) - int(here["y"]))) <= 2
            ]
            for other in linked:
                remaining.remove(other)
                placements[other]["cluster"] = next_cluster
                queue.append(other)
        next_cluster += 1


def _quantile(values: list[int], fraction: float) -> int:
    if not values:
        return 0x7F
    index = round((len(values) - 1) * fraction)
    return int(values[max(0, min(len(values) - 1, index))])


def _terrain_feature_counts(rows: MapRows) -> dict[str, int]:
    plateau_regions = _smooth_region_count(rows, max_delta=2, min_size=6)
    ramps = 0
    blocked_edges: set[tuple[tuple[int, int], tuple[int, int]]] = set()
    isolated_peaks = 0
    basins = 0
    height = len(rows)
    width = len(rows[0]) if rows else 0
    for y, row in enumerate(rows):
        for x, value in enumerate(row):
            neighbors: list[int] = []
            for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if not (0 <= nx < width and 0 <= ny < height):
                    continue
                delta = abs(int(value) - int(rows[ny][nx]))
                neighbors.append(int(rows[ny][nx]))
                if 0 < delta <= 4:
                    ramps += 1
                elif delta > 4:
                    blocked_edges.add(tuple(sorted(((x, y), (nx, ny)))))
            if neighbors and all(int(value) - other > 4 for other in neighbors):
                isolated_peaks += 1
            if neighbors and all(other - int(value) > 4 for other in neighbors):
                basins += 1
    return {
        "plateaus": plateau_regions,
        "ramps": ramps // 2,
        "cliff_bands": _blocked_edge_band_count(blocked_edges),
        "isolated_peaks": isolated_peaks,
        "basins": basins,
    }


def _smooth_region_count(rows: MapRows, *, max_delta: int, min_size: int) -> int:
    if not rows:
        return 0
    height = len(rows)
    width = len(rows[0])
    seen: set[tuple[int, int]] = set()
    count = 0
    for y in range(height):
        for x in range(width):
            if (x, y) in seen:
                continue
            queue: deque[tuple[int, int]] = deque([(x, y)])
            seen.add((x, y))
            size = 0
            while queue:
                cx, cy = queue.popleft()
                size += 1
                here = int(rows[cy][cx])
                for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                    if not (0 <= nx < width and 0 <= ny < height) or (nx, ny) in seen:
                        continue
                    if abs(here - int(rows[ny][nx])) > max_delta:
                        continue
                    seen.add((nx, ny))
                    queue.append((nx, ny))
            if size >= min_size:
                count += 1
    return count


def _blocked_edge_band_count(edges: set[tuple[tuple[int, int], tuple[int, int]]]) -> int:
    remaining = set(edges)
    count = 0
    while remaining:
        start = remaining.pop()
        queue = deque([start])
        count += 1
        while queue:
            edge = queue.popleft()
            points = set(edge)
            linked = [candidate for candidate in remaining if points & set(candidate)]
            for candidate in linked:
                remaining.remove(candidate)
                queue.append(candidate)
    return count


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
