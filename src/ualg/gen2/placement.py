"""Generator2 entity placement."""

from __future__ import annotations

from math import floor

from .context import _Level
from .map_builder import Generator2MapBuilder
from ..constants import GENERATOR2_SCOUT_VEHICLES


_MD_TAERKASTEN_SQUAD_EXCLUDED_FACTIONS = {"tae", "bla"}
_MD_TAERKASTEN_SQUAD_EXCLUDED_VEHICLE_IDS = {143, 144}


class Generator2PlacementPlanner:
    def __init__(self, map_builder: Generator2MapBuilder) -> None:
        self._map_builder = map_builder

    def _choose_map_size(self, level: _Level) -> None:
        while True:
            level.width = level.rng.rand_range(3, 32)
            level.height = level.rng.rand_range(3, 32)
            if (level.width - 2) * (level.height - 2) >= 80:
                return

    def _create_gate(self, level: _Level) -> None:
        coords = self._map_builder._random_xy(level, "gates")
        if coords:
            level.gates.append({"x": coords["x"], "y": coords["y"], "targets": level.targets_by_level[level.level_id]})

    def _create_player_station(self, level: _Level) -> None:
        level.hosts[level.player_faction] = [self._map_builder._random_xy(level)]

    def _create_enemy_stations(self, level: _Level) -> None:
        self._add_enemy_station(level, require_any_enemy=True)
        max_total_hosts = floor(level.width * level.height * 2 / 192)
        for _ in range(max_total_hosts):
            if self._map_builder._total_hosts(level) >= 6:
                break
            if level.rng.rand_range(0, 1):
                self._add_enemy_station(level, require_any_enemy=False)
        level.excluded.clear()

    def _add_enemy_station(self, level: _Level, require_any_enemy: bool) -> None:
        for _ in range(100):
            faction = level.rng.choice(self._map_builder._enemy_factions(level))
            if self._map_builder._total_hosts(level, faction) >= 2:
                if require_any_enemy and self._map_builder._total_hosts(level) == 0:
                    continue
                return
            station = self._map_builder._distribute_host(level)
            if not station:
                if require_any_enemy and self._map_builder._total_hosts(level) == 0:
                    continue
                return
            level.hosts.setdefault(faction, []).append(station)
            return

    def _create_bombs(self, level: _Level) -> None:
        for _ in range(2):
            if level.rng.rand_range(0, 3) != 0:
                continue
            coords = self._map_builder._random_xy(level, "hosts,gates")
            if not coords:
                continue
            bomb = {"x": coords["x"], "y": coords["y"], "timeout": level.rng.rand_range(360, 2100) * 1000, "keys": []}
            level.bombs.append(bomb)
            for _ in range(8):
                if level.rng.rand_range(0, 1):
                    key = self._map_builder._random_xy(level, "hosts,gates,bombs,bomb_keys")
                    if key:
                        bomb["keys"].append(key)

    def _create_squads(self, level: _Level) -> None:
        for _ in range(5 * (self._map_builder._total_hosts(level) + 1)):
            if level.rng.rand_range(0, 1):
                self._add_squad(level)

    def _add_squad(self, level: _Level) -> None:
        coords = self._map_builder._random_xy(level, "hosts,bombs,bomb_keys,squads,flaks")
        if not coords:
            return
        faction = level.rng.choice(self._map_builder._present_factions(level))
        vehicles = self._squad_vehicle_candidates(level, faction)
        if not vehicles:
            return
        vehicle = level.rng.choice(vehicles)
        if vehicle in GENERATOR2_SCOUT_VEHICLES:
            squad_size = 1
        else:
            squad_size = level.rng.rand_range(3, 8)
            if faction != level.player_faction and level.rng.rand_range(0, 5) == 0:
                squad_size *= 2
        level.rng.rand_range(0, 4)  # Legacy template consumes this but does not serialize squad mb_status.
        level.squads.append({
            "faction": faction,
            "vehicle": vehicle,
            "num": squad_size,
            "x": coords["x"],
            "y": coords["y"],
        })

    @staticmethod
    def _squad_vehicle_candidates(level: _Level, faction: str) -> list[int]:
        vehicles = list(level.vehicles_by_faction[faction])
        if level.campaign_profile == "md-taerkasten" and faction in _MD_TAERKASTEN_SQUAD_EXCLUDED_FACTIONS:
            return [vehicle for vehicle in vehicles if vehicle not in _MD_TAERKASTEN_SQUAD_EXCLUDED_VEHICLE_IDS]
        return vehicles
