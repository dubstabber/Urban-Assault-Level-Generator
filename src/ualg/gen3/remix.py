"""Remix builder: bind authored structure to profile-driven content."""

from __future__ import annotations

from typing import Any

from ..constants import SKY_OPTIONS
from ..startup_scripts import startup_include_for_level
from .context import _Gen3Level
from .placement import (
    build_building_remap,
    build_enables,
    build_faction_remap,
    choose_squad_vehicle,
    relabel_own_map,
    remap_blg_map,
)

# Robo AI keys, emitted in this order after the positional/identity keys.
_BUDGET_KEYS = (
    "con_budget", "con_delay",
    "def_budget", "def_delay",
    "rec_budget", "rec_delay",
    "rob_budget", "rob_delay",
    "pow_budget", "pow_delay",
    "rad_budget", "rad_delay",
    "saf_budget", "saf_delay",
    "cpl_budget", "cpl_delay",
)


class Generator3RemixBuilder:
    def build(self, level: _Gen3Level, enemy_pool: list[int]) -> None:
        skeleton = level.skeleton
        rng = level.rng

        level.mode = "remix"
        level.skeleton_name = skeleton.name
        level.source = skeleton.source
        level.title = str(skeleton.record["header"].get("title_default", skeleton.name))
        level.mbmap_block = dict(skeleton.record.get("mbmap", {}))
        level.dbmap_block = dict(skeleton.record.get("dbmap", {}))
        level.tileset = skeleton.tileset
        level.width = skeleton.width
        level.height = skeleton.height
        level.header = dict(skeleton.record["header"])
        level.sky = f"objects/{rng.choice(SKY_OPTIONS)}"
        level.mission_briefing_map = level.profile.mission_briefing_map_for_level(level.level_id)
        level.mission_debriefing_map = level.profile.mission_debriefing_map_for_level(level.level_id)

        level.faction_remap = build_faction_remap(
            rng,
            player_owner=skeleton.player_owner,
            player_faction=level.player_faction,
            enemy_owners=skeleton.enemy_owners,
            enemy_pool=enemy_pool,
        )

        source_maps = skeleton.maps()
        building_remap = build_building_remap(level.profile.roster, level.faction_remap)
        level.maps = {
            "typ": source_maps["typ"],
            "hgt": source_maps["hgt"],
            "own": relabel_own_map(source_maps["own"], level.faction_remap),
            "blg": remap_blg_map(source_maps["blg"], building_remap),
        }

        level.robos = [self._remix_robo(level, robo) for robo in skeleton.record["robos"]]
        level.squads = [self._remix_squad(level, squad) for squad in skeleton.record["squads"]]
        level.gates = [self._copy_gate(gate) for gate in skeleton.record["gates"]]
        level.items = [dict(item) for item in skeleton.record["items"]]
        level.gems = [list(gem["raw"]) for gem in skeleton.record["gems"]]
        level.enables = self._build_enables(level)
        level.prototype = self._remix_prototype(level)

    def _remix_robo(self, level: _Gen3Level, robo: dict[str, Any]) -> dict[str, Any]:
        owner = int(robo["owner"])
        is_player = owner == level.skeleton.player_owner
        new_owner = level.player_faction if is_player else level.faction_remap.get(owner, owner)

        out: dict[str, Any] = {"owner": new_owner}
        if is_player:
            out["vehicle"] = self._player_vehicle(level, robo)
        else:
            out["vehicle"] = level.profile.roster.host_vehicle_by_faction.get(new_owner, robo.get("vehicle"))

        for key in ("pos_x", "pos_y", "pos_z", "energy", "reload_const", "viewangle", "mb_status"):
            if key in robo:
                out[key] = robo[key]

        if not is_player:
            for key in _BUDGET_KEYS:
                if key not in robo:
                    continue
                value = robo[key]
                if key == "rad_budget" and level.zero_enemy_radar_budgets:
                    value = 0
                elif key.endswith("_delay") and level.zero_enemy_station_delays:
                    value = 0
                out[key] = value
        return out

    def _player_vehicle(self, level: _Gen3Level, robo: dict[str, Any]) -> int:
        by_level = level.profile.player_robo_by_level.get(level.level_id)
        if by_level:
            return by_level
        player_robos = level.profile.roster.player_robo_ids_by_faction.get(level.player_faction)
        if player_robos:
            return player_robos[-1]
        host = level.profile.roster.host_vehicle_by_faction.get(level.player_faction)
        if host:
            return host
        return int(robo.get("vehicle", 56))

    def _remix_squad(self, level: _Gen3Level, squad: dict[str, Any]) -> dict[str, Any]:
        owner = int(squad["owner"])
        new_owner = level.faction_remap.get(owner, owner)
        out: dict[str, Any] = {
            "owner": new_owner,
            "vehicle": choose_squad_vehicle(level.rng, level.profile.roster, new_owner, squad.get("vehicle", 1)),
            "num": squad.get("num", 1),
            "pos_x": squad.get("pos_x"),
            "pos_z": squad.get("pos_z"),
        }
        if squad.get("mb_status") is not None:
            out["mb_status"] = squad["mb_status"]
        if squad.get("useable"):
            out["useable"] = True
        return out

    @staticmethod
    def _copy_gate(gate: dict[str, Any]) -> dict[str, Any]:
        copied = dict(gate)
        copied["targets"] = list(gate.get("targets", []))
        copied["keysecs"] = [dict(key) for key in gate.get("keysecs", [])]
        return copied

    def _build_enables(self, level: _Gen3Level) -> list[dict[str, Any]]:
        present = [level.player_faction, *level.faction_remap.values()]
        return build_enables(level.profile.roster, present, profile_id=level.profile_id)

    def _remix_prototype(self, level: _Gen3Level) -> list[str]:
        include_line = startup_include_for_level(level.profile_id, level.level_id)
        result: list[str] = []
        include_added = False
        for line in level.skeleton.record["prototype"]:
            if line.strip().lower().startswith("include"):
                if not include_added:
                    result.append(include_line)
                    include_added = True
                continue
            result.append(line)
        if not include_added:
            result.insert(0, include_line)
        return result
