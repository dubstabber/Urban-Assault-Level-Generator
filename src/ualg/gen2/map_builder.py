"""Generator2 map construction and coordinate helpers."""

from __future__ import annotations

from math import ceil, floor
from typing import Any

from .context import _Level
from ..core.maps import filled_rows, set_cell, set_cell_if_in_bounds
from ..constants import (
    BLG_PLAYER_BASE,
    BLG_SUPERITEM,
    BUILDING_TYP_BY_ID,
    GENERATOR2_FACTION_IDS,
    GENERATOR2_FACTIONS,
    GENERATOR2_SET_LIST,
    TYP_GATE_CLOSED_1,
    TYP_GATE_CLOSED_2,
    TYP_PLAYER_BASE,
    TYP_SUPERITEM,
)
from ..models import MapRows


class Generator2MapBuilderMixin:
    def _make_map(self, level: _Level, map_type: str) -> None:
        level.excluded = self._get_station_sectors(level)
        current = self._reset_map(level, map_type)
        if map_type == "typ":
            values = GENERATOR2_SET_LIST[level.tileset]
            for y in range(level.height):
                for x in range(level.width):
                    current[y][x] = level.rng.choice(values)
            for x in range(level.width):
                current[0][x] = 252
                current[level.height - 1][x] = 254
            for y in range(level.height):
                current[y][0] = 255
                current[y][level.width - 1] = 253
            current[0][0] = 248
            current[0][level.width - 1] = 249
            current[level.height - 1][0] = 251
            current[level.height - 1][level.width - 1] = 250
        elif map_type == "own":
            total = max(1, self._total_hosts(level))
            max_territory = ((level.width - 2) * (level.height - 2)) / total * 1.8
            for faction in self._present_factions(level):
                self._set_territory(level, current, faction, max_territory)
            for x in range(level.width):
                current[0][x] = 0
                current[level.height - 1][x] = 0
            for y in range(level.height):
                current[y][0] = 0
                current[y][level.width - 1] = 0
            for squad in level.squads:
                current[squad["y"]][squad["x"]] = GENERATOR2_FACTION_IDS[squad["faction"]]
        elif map_type == "hgt":
            height_deltas = [0, 0, 0, 0, 1, 1, 2, 2, 3]
            for _ in range(level.rng.rand_range(3, 8)):
                height = 128
                run_size = level.rng.rand_range(1, 5) * floor(level.width * level.height / 10)
                x = self._random_x(level)
                y = self._random_y(level)
                for _ in range(run_size):
                    x, y = self._set_height_around(level, current, height, x, y)
                    height += level.rng.choice(height_deltas) * (1 if level.rng.rand_range(0, 1) else -1)
                    height = max(116, min(140, height))
            for x in range(level.width):
                current[0][x] = current[1][x]
                current[level.height - 1][x] = current[level.height - 2][x]
            for y in range(level.height):
                current[y][0] = current[y][1]
                current[y][level.width - 1] = current[y][level.width - 2]
        elif map_type == "blg":
            for faction, stations in level.hosts.items():
                for station in stations:
                    building = self._host_power_building(faction)
                    if building:
                        current[station["y"]][station["x"]] = building
            for _ in range(ceil(level.width * level.height / 120)):
                if level.rng.rand_range(0, 2) != 0:
                    coords = self._random_xy(level, "hosts,gates,bombs,bomb_keys")
                    if coords:
                        current[coords["y"]][coords["x"]] = 63
        level.maps[map_type] = current

    def _apply_special_map_rules(self, level: _Level) -> None:
        typ = level.maps["typ"]
        blg = level.maps["blg"]

        for y in range(level.height):
            for x in range(level.width):
                typ_value = BUILDING_TYP_BY_ID.get(blg[y][x])
                if typ_value is not None:
                    typ[y][x] = typ_value

        for gate in level.gates:
            self._set_map_cell(level, "typ", gate["x"], gate["y"], TYP_PLAYER_BASE)
            self._set_map_cell(level, "blg", gate["x"], gate["y"], BLG_PLAYER_BASE)

        for bomb in level.bombs:
            self._set_map_cell(level, "typ", bomb["x"], bomb["y"], TYP_SUPERITEM)
            self._set_map_cell(level, "blg", bomb["x"], bomb["y"], BLG_SUPERITEM)
            for key in bomb["keys"]:
                key_typ = TYP_GATE_CLOSED_1 if level.rng.rand_range(0, 1) else TYP_GATE_CLOSED_2
                self._set_map_cell(level, "typ", key["x"], key["y"], key_typ)
                self._set_map_cell(level, "blg", key["x"], key["y"], 0)

    @staticmethod
    def _set_map_cell(level: _Level, map_name: str, x: int, y: int, value: int) -> None:
        set_cell_if_in_bounds(level.maps[map_name], level.width, level.height, x, y, value)

    @staticmethod
    def _reset_map(level: _Level, map_type: str) -> MapRows:
        value = 7 if map_type == "own" else 128 if map_type == "hgt" else 0
        return filled_rows(level.width, level.height, value)

    def _set_territory(self, level: _Level, current: MapRows, faction: str, max_territory: float) -> None:
        faction_id = GENERATOR2_FACTION_IDS[faction]
        iterations = ceil(max_territory)
        if faction == level.player_faction:
            iterations = floor(max_territory * 0.2)
        for station in level.hosts.get(faction, []):
            self._set_territory_around(level, current, faction_id, station["x"], station["y"])
            x, y = station["x"], station["y"]
            for _ in range(iterations):
                if level.rng.rand_range(0, 1):
                    x = max(1, min(level.width - 1, x + level.rng.rand_range(-1, 1)))
                    y = max(1, min(level.height - 1, y + level.rng.rand_range(-1, 1)))
                    self._set_territory_around(level, current, faction_id, x, y)

    def _set_territory_around(self, level: _Level, current: MapRows, faction_id: int, x: int, y: int) -> None:
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                self._set_sector(level, current, faction_id, x + dx, y + dy, validate=True)

    def _set_height_around(self, level: _Level, current: MapRows, height: int, x: int, y: int) -> tuple[int, int]:
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                next_height = height if dx == 0 and dy == 0 else self._new_height(level, height)
                self._set_sector(level, current, next_height, x + dx, y + dy)
        while True:
            step_x = level.rng.rand_range(-1, 1)
            step_y = level.rng.rand_range(-1, 1)
            if step_x or step_y:
                x += step_x
                y += step_y
                break
        return max(1, min(level.width - 1, x)), max(1, min(level.height - 1, y))

    def _set_sector(self, level: _Level, current: MapRows, value: int, x: int, y: int, validate: bool = False) -> None:
        if x < 0 or y < 0 or x >= level.width or y >= level.height:
            return
        if validate:
            for reserved in level.excluded:
                if reserved["x"] == x and reserved["y"] == y and GENERATOR2_FACTION_IDS[reserved["faction"]] != value:
                    return
        set_cell(current, x, y, value)

    def _new_height(self, level: _Level, height: int) -> int:
        if level.rng.rand_range(0, 2):
            height += level.rng.rand_range(-2, 2)
        return max(104, min(152, height))

    @staticmethod
    def _host_power_building(faction: str) -> int:
        return {"sul": 11, "myk": 10, "tae": 17, "bla": 11, "gho": 12}.get(faction, 0)

    def _distribute_host(self, level: _Level) -> dict[str, int]:
        min_distance_sq = (3 * 1200) ** 2
        while True:
            coords = self._random_xy(level, "hosts,excluded")
            if not coords:
                return {}
            valid = True
            for stations in level.hosts.values():
                for station in stations:
                    if self._distance_sq(station, coords) < min_distance_sq:
                        valid = False
                        level.excluded.append(coords)
                        break
                if not valid:
                    break
            if valid:
                level.excluded.clear()
                return coords

    def _available_map(self, level: _Level, without: str = "", faction: str = "") -> list[dict[str, int]]:
        blocked: set[tuple[int, int]] = set()
        for name in (part.strip() for part in without.split(",") if part.strip()):
            if name == "hosts":
                for stations in level.hosts.values():
                    blocked.update((station["x"], station["y"]) for station in stations)
            elif name == "excluded":
                blocked.update((coords["x"], coords["y"]) for coords in level.excluded)
            elif name in {"gates", "bombs", "squads", "flaks", "powers"}:
                blocked.update((coords["x"], coords["y"]) for coords in getattr(level, name))
            elif name == "bomb_keys":
                for bomb in level.bombs:
                    blocked.update((key["x"], key["y"]) for key in bomb["keys"])
        result = []
        for x in range(1, level.width - 1):
            for y in range(1, level.height - 1):
                if faction and "own" in level.maps and level.maps["own"][y][x] != GENERATOR2_FACTION_IDS[faction]:
                    continue
                if (x, y) not in blocked:
                    result.append({"x": x, "y": y})
        return result

    def _random_xy(self, level: _Level, without: str = "", faction: str = "") -> dict[str, int]:
        cells = self._available_map(level, without, faction)
        return level.rng.choice(cells) if cells else {}

    def _random_x(self, level: _Level) -> int:
        return level.rng.rand_range(1, level.width - 2)

    def _random_y(self, level: _Level) -> int:
        return level.rng.rand_range(1, level.height - 2)

    @staticmethod
    def _get_position(coordinate: int, vertical: bool = False) -> int:
        sign = -1 if vertical else 1
        return int((coordinate + 0.5) * 1200 * sign) + 1

    def _distance_sq(self, a: dict[str, int], b: dict[str, int]) -> int:
        dx = self._get_position(a["x"]) - self._get_position(b["x"])
        dy = self._get_position(a["y"]) - self._get_position(b["y"])
        return dx * dx + dy * dy

    @staticmethod
    def _total_hosts(level: _Level, faction: str = "") -> int:
        if faction:
            return len(level.hosts.get(faction, []))
        return sum(len(stations) for host_faction, stations in level.hosts.items() if host_faction != level.player_faction)

    @staticmethod
    def _present_factions(level: _Level) -> list[str]:
        return list(level.hosts.keys())

    @staticmethod
    def _enemy_factions(level: _Level) -> list[str]:
        if level.campaign_profile == "original":
            return list(GENERATOR2_FACTIONS)
        return [faction for faction in GENERATOR2_FACTION_IDS if faction != level.player_faction]

    @staticmethod
    def _get_station_sectors(level: _Level) -> list[dict[str, Any]]:
        result = []
        for faction, stations in level.hosts.items():
            for station in stations:
                result.append({"x": station["x"], "y": station["y"], "faction": faction})
        return result
