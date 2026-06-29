"""Infrastructure extraction and placement helpers for Generator4."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from functools import cache
from typing import Any

from ..constants import BUILDING_TYP_BY_ID
from ..data import ua_data
from ..models import MapRows
from .passability import required_cells_connected

_ICON_TO_CATEGORY = {
    "power_station": "power",
    "flak_station": "flak",
    "radar_station": "radar",
}
_CATEGORIES = ("power", "flak", "radar")
_FACTION_TUTOR = 7
_MIN_STATION_SPACING = {"power": 4, "flak": 4, "radar": 5}


@dataclass(frozen=True, slots=True)
class StationInfo:
    building: int
    category: str
    typ: int | None
    expected_owner: int


@cache
def station_info_by_building() -> dict[int, StationInfo]:
    """Return known power/flak/radar building ids from ``UAdata.json``."""

    result: dict[int, StationInfo] = {}
    for profile in ("original", "metropolisDawn"):
        data = ua_data().get(profile, {})
        for station in data.get("hoststations", {}).values():
            owner = int(station.get("owner", 0))
            for building in station.get("buildings", []):
                _add_station_info(result, building, expected_owner=owner)
        for building in data.get("other", {}).get("buildings", []):
            _add_station_info(result, building, expected_owner=0)
    return result


def station_category_by_building() -> dict[int, str]:
    return {building: info.category for building, info in station_info_by_building().items()}


def station_counts(placements: list[dict[str, Any]]) -> dict[str, int]:
    counts = {category: 0 for category in _CATEGORIES}
    counts.update(Counter(str(placement["category"]) for placement in placements))
    return counts


def synthesize_infrastructure(
    level: Any,
    hosts: list[dict[str, Any]],
    occupied: set[tuple[int, int]],
    typ: MapRows,
    blg: MapRows,
    hgt: MapRows,
) -> list[dict[str, Any]]:
    """Place v2 authored-style infrastructure and update ``typ``/``blg`` maps."""

    profile = level.archetype.record.get("infrastructure_profile", {})
    source_placements = list(level.archetype.record.get("infrastructure_placements", []))
    source_counts = {category: int(profile.get("counts", {}).get(category, 0) or 0) for category in _CATEGORIES}
    if not any(source_counts.values()):
        return []

    free = _free_cells(level.width, level.height, occupied, hgt, level.required_route_cells)
    if not free:
        return []

    interior = max(1, (level.width - 2) * (level.height - 2))
    density = float(profile.get("max_station_density", 0.0) or 0.0)
    density_limit = min(0.055, max(0.02 if any(source_counts.values()) else 0.0, density * 0.55))
    requested_categories = [category for category, count in source_counts.items() if count > 0]
    max_total = min(len(free), max(len(requested_categories), int(interior * density_limit)))

    placements: list[dict[str, Any]] = []
    participating = _participating_owners(level, hosts)
    by_category: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_owner_category: dict[tuple[int, str], list[dict[str, Any]]] = defaultdict(list)
    for placement in source_placements:
        category = str(placement.get("category", ""))
        owner = _runtime_owner(level, int(placement.get("owner", 0)))
        by_category[category].append(placement)
        by_owner_category[(owner, category)].append(placement)

    requests = _target_requests(level, profile, source_counts, participating, max_total)
    for request in requests:
        category = str(request["category"])
        owner = int(request["owner"])
        target = int(request["count"])
        while target > 0 and free:
            building = _building_for_category(level, category, owner, by_owner_category.get((owner, category), []))
            typ_id = BUILDING_TYP_BY_ID.get(building)
            seed = _best_station_cell(level, category, owner, hosts, free, hgt, placements)
            if seed is None:
                break
            x, y = seed
            typ[y][x] = typ_id if typ_id is not None else typ[y][x]
            blg[y][x] = building
            occupied.add((x, y))
            free.discard((x, y))
            placements.append(
                {
                    "category": category,
                    "building": building,
                    "typ": typ_id,
                    "owner": owner,
                    "x": x,
                    "y": y,
                    "source_owner_7": any(int(p.get("owner", -1)) == _FACTION_TUTOR for p in by_category.get(category, [])),
                }
            )
            target -= 1
    return placements


def _add_station_info(result: dict[int, StationInfo], building: dict[str, Any], *, expected_owner: int) -> None:
    category = _ICON_TO_CATEGORY.get(str(building.get("icon_type", "")))
    if category is None:
        return
    building_id = int(building["id"])
    typ = int(building["typ_map"]) if building.get("typ_map") is not None else BUILDING_TYP_BY_ID.get(building_id)
    result.setdefault(
        building_id,
        StationInfo(building=building_id, category=category, typ=typ, expected_owner=int(expected_owner)),
    )


def _free_cells(
    width: int,
    height: int,
    occupied: set[tuple[int, int]],
    hgt: MapRows,
    required_cells: list[tuple[int, int]],
) -> set[tuple[int, int]]:
    cells: set[tuple[int, int]] = set()
    for y in range(1, height - 1):
        for x in range(1, width - 1):
            cell = (x, y)
            if cell in occupied:
                continue
            if required_cells and not required_cells_connected(hgt, [required_cells[0], cell]):
                continue
            cells.add(cell)
    return cells


def _target_requests(
    level: Any,
    profile: dict[str, Any],
    source_counts: dict[str, int],
    participating: set[int],
    max_total: int,
) -> list[dict[str, int | str]]:
    counts_by_owner = profile.get("counts_by_owner", {})
    has_bomb = any(item.get("keysecs") for item in level.archetype.record.get("items", []))
    requests: list[dict[str, int | str]] = []
    seen: set[tuple[int, str]] = set()
    for owner_text, category_counts in counts_by_owner.items():
        owner = _runtime_owner(level, int(owner_text))
        if owner not in participating and owner != _FACTION_TUTOR:
            continue
        for category in _CATEGORIES:
            if owner == _FACTION_TUTOR and category != "power":
                continue
            source_count = int(category_counts.get(category, 0) or 0)
            count = _scaled_owner_target(level, category, owner, source_count, has_bomb)
            if count <= 0:
                continue
            requests.append({"owner": owner, "category": category, "count": count})
            seen.add((owner, category))

    player_owner = int(level.player_faction)
    interior = max(1, (level.width - 2) * (level.height - 2))
    if source_counts.get("power", 0) > 0 and interior >= 64 and (player_owner, "power") not in seen:
        requests.append({"owner": player_owner, "category": "power", "count": 1})
    if source_counts.get("flak", 0) >= 4 and interior >= 100 and (player_owner, "flak") not in seen:
        requests.append({"owner": player_owner, "category": "flak", "count": 2 if has_bomb else 1})

    requests.sort(key=lambda request: (0 if int(request["owner"]) == player_owner else 1, _CATEGORIES.index(str(request["category"])), int(request["owner"])))
    while sum(int(request["count"]) for request in requests) > max_total and requests:
        reducible = [request for request in requests if int(request["owner"]) != player_owner and int(request["count"]) > 1]
        if not reducible:
            reducible = [request for request in requests if int(request["count"]) > 1]
        if not reducible:
            break
        request = reducible[level.rng.rand_mod(len(reducible))]
        request["count"] = int(request["count"]) - 1
    return [request for request in requests if int(request["count"]) > 0]


def _scaled_owner_target(level: Any, category: str, owner: int, source_count: int, has_bomb: bool) -> int:
    if source_count <= 0:
        return 0
    is_player = owner == int(level.player_faction)
    interior = max(1, (level.width - 2) * (level.height - 2))
    large = interior >= 400
    huge = interior >= 900
    if category == "power":
        base = max(1, round((source_count ** 0.5) * 0.85))
        if owner == _FACTION_TUTOR:
            cap = 1
        elif is_player:
            cap = 3 if has_bomb and large else 2
        else:
            cap = 2 if source_count >= 5 else 1
        return min(base, cap)
    if category == "flak":
        if is_player and has_bomb:
            base = max(2, round(source_count * 0.65))
            cap = 6 if large else 4
        elif is_player:
            base = max(1, round(source_count * 0.5))
            cap = 3 if large else 2
        else:
            base = max(1, round(source_count * 0.28))
            cap = 5 if huge else 4 if large else 2
        return min(base, cap)
    if category == "radar":
        if source_count >= 5 and huge:
            return 2
        return 1
    return 0


def _participating_owners(level: Any, hosts: list[dict[str, Any]]) -> set[int]:
    owners = {int(host["faction"]) for host in hosts}
    owners.update(int(owner) for owner in level.legal_vehicles_by_owner)
    owners.add(int(level.player_faction))
    return {owner for owner in owners if owner not in {0, _FACTION_TUTOR}}


def _runtime_owner(level: Any, source_owner: int) -> int:
    if int(source_owner) == int(level.archetype.player_owner):
        return int(level.player_faction)
    return int(source_owner)


def _building_for_category(level: Any, category: str, owner: int, source_placements: list[dict[str, Any]]) -> int:
    info = station_info_by_building()
    source_buildings = [int(placement["building"]) for placement in source_placements if int(placement.get("building", 0)) in info]
    source_buildings = [building for building in source_buildings if info[building].category == category]
    roster_buildings = [
        int(building)
        for building in level.profile.roster.buildings_by_faction.get(owner, ())
        if info.get(int(building)) is not None and info[int(building)].category == category
    ]
    compatible_source = [building for building in source_buildings if owner == _FACTION_TUTOR or building in roster_buildings]
    if compatible_source:
        return compatible_source[level.rng.rand_mod(len(compatible_source))]
    if roster_buildings:
        return roster_buildings[level.rng.rand_mod(len(roster_buildings))]
    if source_buildings:
        return source_buildings[level.rng.rand_mod(len(source_buildings))]

    all_buildings = [building for building, station in info.items() if station.category == category]
    return all_buildings[level.rng.rand_mod(len(all_buildings))]


def _best_station_cell(
    level: Any,
    category: str,
    owner: int,
    hosts: list[dict[str, Any]],
    free: set[tuple[int, int]],
    hgt: MapRows,
    placements: list[dict[str, Any]],
) -> tuple[int, int] | None:
    if not free:
        return None
    scored: list[tuple[int, int, int]] = []
    map_span = max(level.width, level.height)
    radar_min = max(4, map_span // 6)
    power_target = max(3, min(6, map_span // 6))
    radar_target = max(radar_min + 1, map_span // 3)
    for x, y in free:
        if _too_close_to_category((x, y), category, placements):
            continue
        own_dist = _nearest_host_distance((x, y), hosts, owner=owner)
        any_dist = _nearest_host_distance((x, y), hosts)
        any_cheb = _nearest_host_chebyshev((x, y), hosts)
        if category == "power" and any_cheb < 3:
            continue
        enemy_dist = _nearest_enemy_host_distance((x, y), hosts, owner)
        local_delta = _local_height_delta(hgt, x, y)
        if category == "power":
            base_penalty = 16 if own_dist <= 1 and owner != level.player_faction else 0
            score = abs(own_dist - power_target) * 4 + max(0, 4 - enemy_dist) * 3 + base_penalty + level.rng.rand_mod(11)
        elif category == "flak":
            front_balance = abs(own_dist - enemy_dist) if enemy_dist < 999 else any_dist
            score = front_balance * 3 - local_delta * 2 + abs(any_dist - 5) + level.rng.rand_mod(13)
        else:
            near_base_penalty = max(0, radar_min - own_dist) * 20
            score = abs(own_dist - radar_target) * 3 + max(0, 3 - enemy_dist) * 4 + near_base_penalty + level.rng.rand_mod(13)
        scored.append((score, x, y))
    if not scored and category == "radar":
        for x, y in free:
            if _too_close_to_category((x, y), category, placements):
                continue
            own_dist = _nearest_host_distance((x, y), hosts, owner=owner)
            scored.append((abs(own_dist - radar_target), x, y))
    scored.sort()
    return scored[0][1], scored[0][2]


def _too_close_to_category(cell: tuple[int, int], category: str, placements: list[dict[str, Any]]) -> bool:
    spacing = _MIN_STATION_SPACING.get(category, 3)
    for placement in placements:
        if placement.get("category") != category:
            continue
        distance = max(abs(int(placement["x"]) - cell[0]), abs(int(placement["y"]) - cell[1]))
        if distance < spacing:
            return True
    return False


def _nearest_host_distance(cell: tuple[int, int], hosts: list[dict[str, Any]], owner: int | None = None) -> int:
    distances = [
        abs(int(host["x"]) - cell[0]) + abs(int(host["y"]) - cell[1])
        for host in hosts
        if owner is None or int(host["faction"]) == owner
    ]
    return min(distances) if distances else 999


def _nearest_host_chebyshev(cell: tuple[int, int], hosts: list[dict[str, Any]]) -> int:
    distances = [
        max(abs(int(host["x"]) - cell[0]), abs(int(host["y"]) - cell[1]))
        for host in hosts
    ]
    return min(distances) if distances else 999


def _nearest_enemy_host_distance(cell: tuple[int, int], hosts: list[dict[str, Any]], owner: int) -> int:
    distances = [
        abs(int(host["x"]) - cell[0]) + abs(int(host["y"]) - cell[1])
        for host in hosts
        if int(host["faction"]) not in {owner, _FACTION_TUTOR}
    ]
    return min(distances) if distances else 999


def _local_height_delta(rows: MapRows, x: int, y: int) -> int:
    if not rows:
        return 0
    here = int(rows[y][x])
    best = 0
    for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
        if 0 <= ny < len(rows) and 0 <= nx < len(rows[ny]):
            best = max(best, abs(here - int(rows[ny][nx])))
    return best
