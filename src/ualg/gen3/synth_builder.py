"""Build a complete synthesized level around WFC-generated terrain."""

from __future__ import annotations

from math import floor
from typing import Any

from ..constants import (
    BUILDING_TYP_BY_ID,
    SKY_OPTIONS,
    sector_to_world_x,
    sector_to_world_z,
)
from ..core.maps import filled_rows
from ..models import MapRows
from ..rng import MSVCRTRandom
from ..startup_scripts import startup_include_for_level
from .context import _Gen3Level
from .placement import build_enables, choose_squad_vehicle
from .synthesis import synthesize_typ_map

_HGT_BASELINE = 0x7F
_HGT_MIN, _HGT_MAX = 0x78, 0x86
_SCOUT_VEHICLES = {9, 74, 67, 35, 29}

_BUDGET_RANGES = {
    "con_budget": (80, 90),
    "def_budget": (70, 100),
    "rec_budget": (50, 80),
    "rob_budget": (50, 90),
    "pow_budget": (40, 70),
    "saf_budget": (50, 100),
    "cpl_budget": (30, 50),
}


class Generator3SynthBuilder:
    def build(self, level: _Gen3Level, source: str, enemy_pool: list[int]) -> None:
        rng = level.rng
        profile = level.profile
        roster = profile.roster

        level.mode = "synthesis"
        level.source = source
        level.title = "SYNTHESIZED"
        level.tileset = self._choose_tileset(level, source)
        level.width, level.height = self._choose_size(rng)

        typ, method = synthesize_typ_map(source, level.tileset, level.width, level.height, rng)
        level.synth_method = method

        hosts = self._place_hosts(level, enemy_pool)
        own = self._voronoi_own_map(level, hosts)
        hgt = self._synth_height(level)
        blg = filled_rows(level.width, level.height, 0)
        self._place_host_buildings(level, hosts, typ, blg)

        level.maps = {"typ": typ, "own": own, "hgt": hgt, "blg": blg}
        level.robos = [self._host_robo(level, host) for host in hosts]
        level.squads = self._place_squads(level, hosts)
        level.gates = [self._place_gate(level, hosts)]
        level.enables = build_enables(roster, [host["faction"] for host in hosts])
        level.prototype = [startup_include_for_level(level.profile_id, level.level_id)]
        level.sky = f"objects/{rng.choice(SKY_OPTIONS)}"
        level.mission_briefing_map = profile.mission_briefing_map_for_level(level.level_id)
        level.mission_debriefing_map = profile.mission_debriefing_map_for_level(level.level_id)

    # -- terrain framing ----------------------------------------------------

    def _choose_tileset(self, level: _Gen3Level, source: str) -> int:
        from .corpus import skeletons_for_source

        tilesets = sorted({skeleton.tileset for skeleton in skeletons_for_source(source)})
        return level.rng.choice(tilesets)

    def _choose_size(self, rng: MSVCRTRandom) -> tuple[int, int]:
        width = rng.rand_range(12, 18)
        height = rng.rand_range(10, 15)
        return width, height

    # -- host stations ------------------------------------------------------

    def _place_hosts(self, level: _Gen3Level, enemy_pool: list[int]) -> list[dict[str, Any]]:
        rng = level.rng
        pool = [faction for faction in enemy_pool if faction != level.player_faction]
        enemy_count = min(len(pool), rng.rand_range(1, min(4, len(pool)) or 1)) if pool else 0

        bag = list(pool)
        enemy_factions: list[int] = []
        for _ in range(enemy_count):
            if not bag:
                break
            enemy_factions.append(bag.pop(rng.rand_mod(len(bag))))

        factions = [level.player_faction, *enemy_factions]
        occupied: list[tuple[int, int]] = []
        hosts: list[dict[str, Any]] = []
        for index, faction in enumerate(factions):
            cell = self._find_spaced_cell(level, occupied, min_distance=2)
            occupied.append(cell)
            hosts.append(
                {
                    "faction": faction,
                    "x": cell[0],
                    "y": cell[1],
                    "is_player": index == 0,
                }
            )
        return hosts

    def _find_spaced_cell(
        self,
        level: _Gen3Level,
        occupied: list[tuple[int, int]],
        min_distance: int,
    ) -> tuple[int, int]:
        rng = level.rng
        best: tuple[int, int] | None = None
        for _ in range(64):
            cell = self._random_interior_cell(level)
            if all(max(abs(cell[0] - ox), abs(cell[1] - oy)) >= min_distance for ox, oy in occupied):
                return cell
            best = cell
        return best or self._random_interior_cell(level)

    def _random_interior_cell(self, level: _Gen3Level) -> tuple[int, int]:
        x = level.rng.rand_range(1, level.width - 2)
        y = level.rng.rand_range(1, level.height - 2)
        return x, y

    # -- maps ---------------------------------------------------------------

    def _voronoi_own_map(self, level: _Gen3Level, hosts: list[dict[str, Any]]) -> MapRows:
        rows = filled_rows(level.width, level.height, 0)
        for y in range(1, level.height - 1):
            for x in range(1, level.width - 1):
                nearest = min(hosts, key=lambda h: (h["x"] - x) ** 2 + (h["y"] - y) ** 2)
                rows[y][x] = nearest["faction"]
        return rows

    def _synth_height(self, level: _Gen3Level) -> MapRows:
        rng = level.rng
        rows = filled_rows(level.width, level.height, _HGT_BASELINE)
        walks = rng.rand_range(2, 5)
        for _ in range(walks):
            x, y = self._random_interior_cell(level)
            steps = max(4, (level.width * level.height) // 8)
            height = _HGT_BASELINE
            for _ in range(steps):
                height = max(_HGT_MIN, min(_HGT_MAX, height + rng.rand_range(-1, 1)))
                rows[y][x] = height
                x = max(1, min(level.width - 2, x + rng.rand_range(-1, 1)))
                y = max(1, min(level.height - 2, y + rng.rand_range(-1, 1)))
        return rows

    def _place_host_buildings(
        self,
        level: _Gen3Level,
        hosts: list[dict[str, Any]],
        typ: MapRows,
        blg: MapRows,
    ) -> None:
        roster = level.profile.roster
        for host in hosts:
            buildings = roster.buildings_by_faction.get(host["faction"], ())
            if not buildings:
                continue
            building = buildings[0]
            blg[host["y"]][host["x"]] = building
            typ[host["y"]][host["x"]] = BUILDING_TYP_BY_ID.get(building, typ[host["y"]][host["x"]])

    # -- entities -----------------------------------------------------------

    def _host_robo(self, level: _Gen3Level, host: dict[str, Any]) -> dict[str, Any]:
        rng = level.rng
        roster = level.profile.roster
        faction = host["faction"]
        is_player = host["is_player"]

        out: dict[str, Any] = {"owner": faction}
        if is_player:
            out["vehicle"] = self._player_vehicle(level)
            energy = rng.rand_range(4, 8) * 100000
            out.update(
                {
                    "pos_x": sector_to_world_x(host["x"], plus_one=True),
                    "pos_y": -rng.rand_range(2, 5) * 100,
                    "pos_z": sector_to_world_z(host["y"], plus_one=True),
                    "energy": energy,
                    "reload_const": floor((((energy - 550000) / 4) + 550000) / 5),
                }
            )
            return out

        out["vehicle"] = roster.host_vehicle_by_faction.get(faction, 57)
        energy = rng.rand_range(8, 18) * 100000
        out.update(
            {
                "pos_x": sector_to_world_x(host["x"], plus_one=True),
                "pos_y": -rng.rand_range(2, 5) * 100,
                "pos_z": sector_to_world_z(host["y"], plus_one=True),
                "energy": energy,
                "reload_const": floor(((energy - 500000) / 3) + 500000),
            }
        )
        for key, (low, high) in _BUDGET_RANGES.items():
            value = rng.rand_range(low, high)
            delay_key = key.replace("_budget", "_delay")
            out[key] = value
            out[delay_key] = 0 if level.zero_enemy_station_delays else rng.rand_range(0, 300) * 1000
        rad = rng.rand_range(0, 10)
        out["rad_budget"] = 0 if level.zero_enemy_radar_budgets else rad
        out["rad_delay"] = 0 if level.zero_enemy_station_delays else rng.rand_range(600, 1800) * 1000
        return out

    def _player_vehicle(self, level: _Gen3Level) -> int:
        robos = level.profile.roster.player_robo_ids_by_faction.get(level.player_faction)
        if robos:
            return robos[-1]
        return level.profile.roster.host_vehicle_by_faction.get(level.player_faction, 56)

    def _place_squads(self, level: _Gen3Level, hosts: list[dict[str, Any]]) -> list[dict[str, Any]]:
        rng = level.rng
        roster = level.profile.roster
        factions = [host["faction"] for host in hosts]
        host_cells = {(host["x"], host["y"]) for host in hosts}
        count = len(hosts) + rng.rand_range(0, len(hosts) + 1)

        squads: list[dict[str, Any]] = []
        for _ in range(count):
            faction = rng.choice(factions)
            cell = self._random_interior_cell(level)
            if cell in host_cells:
                continue
            vehicle = choose_squad_vehicle(rng, roster, faction, 1)
            num = 1 if vehicle in _SCOUT_VEHICLES else rng.rand_range(2, 5)
            squads.append(
                {
                    "owner": faction,
                    "vehicle": vehicle,
                    "num": num,
                    "pos_x": sector_to_world_x(cell[0], plus_one=True),
                    "pos_z": sector_to_world_z(cell[1], plus_one=True),
                }
            )
        return squads

    def _place_gate(self, level: _Gen3Level, hosts: list[dict[str, Any]]) -> dict[str, Any]:
        rng = level.rng
        host_cells = {(host["x"], host["y"]) for host in hosts}
        cell = self._random_interior_cell(level)
        for _ in range(16):
            if cell not in host_cells:
                break
            cell = self._random_interior_cell(level)
        keysecs = []
        for _ in range(rng.rand_range(0, 3)):
            kx, ky = self._random_interior_cell(level)
            keysecs.append({"x": kx, "y": ky})
        return {
            "sec_x": cell[0],
            "sec_y": cell[1],
            "closed_bp": 5,
            "opened_bp": 6,
            "targets": [],
            "keysecs": keysecs,
            "mb_status": "unknown",
        }
