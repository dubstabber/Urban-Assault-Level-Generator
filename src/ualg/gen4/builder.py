"""Build a campaign-aware synthesized Generator4 level."""

from __future__ import annotations

from functools import lru_cache
import re
from math import floor
from typing import Any

from ..constants import (
    BLACK_SECT_ENABLE_EXCLUDED_BUILDING_IDS,
    BUILDING_TYP_BY_ID,
    ENABLE_EXCLUDED_VEHICLE_IDS,
    MD_TAERKASTEN_ENABLE_EXCLUDED_VEHICLE_IDS,
    SKY_OPTIONS,
    TYP_GATE_CLOSED_1,
    TYP_GATE_CLOSED_2,
    sector_to_world_x,
    sector_to_world_z,
)
from ..core.maps import filled_rows
from ..models import MapRows
from ..startup_scripts import startup_include_for_level
from ..gen3.corpus import skeletons_for_source
from ..gen3.synthesis import adjacency_model_for, border_tile, synthesize_typ_map
from .context import _Gen4Level
from .infrastructure import station_counts, synthesize_infrastructure
from .passability import required_cells_connected, synthesize_hgt_map, terrain_metrics

_FACTION_PLAYER = 1
_FACTION_TAERKASTEN = 4
_FACTION_BLACK_SECT = 5
_FACTION_TUTOR = 7
_MD_TAERKASTEN_PROFILE = "md-taerkasten"
_SCOUT_VEHICLES = {9, 29, 35, 67, 74}
_SCOUT_VEHICLE_BY_OWNER = {
    _FACTION_PLAYER: 9,
    2: 74,
    3: 67,
    _FACTION_TAERKASTEN: 35,
    6: 29,
}

_ENABLE_OWNER_RE = re.compile(r"(\benable\s*=\s*)(-?\d+)", re.IGNORECASE)
_SEC_X_RE = re.compile(r"^(\s*sec_x\s*=\s*)-?\d+(.*)$", re.IGNORECASE)
_SEC_Y_RE = re.compile(r"^(\s*sec_y\s*=\s*)-?\d+(.*)$", re.IGNORECASE)


class Generator4Builder:
    def build(self, level: _Gen4Level) -> None:
        record = level.archetype.record
        rng = level.rng

        level.source = level.archetype.source
        level.title = str(record.get("header", {}).get("title_default", level.archetype.name))
        level.tileset = level.archetype.tileset
        level.width = level.archetype.width
        level.height = level.archetype.height
        level.header = dict(record.get("header", {}))
        level.mbmap_block = dict(record.get("mbmap", {}))
        level.dbmap_block = dict(record.get("dbmap", {}))
        level.sky = f"objects/{rng.choice(SKY_OPTIONS)}"
        level.mission_briefing_map = level.profile.mission_briefing_map_for_level(level.level_id)
        level.mission_debriefing_map = level.profile.mission_debriefing_map_for_level(level.level_id)

        typ, method = self._synthesize_typ_map(level)
        level.synth_method = method

        level.enables, level.legal_vehicles_by_owner = self._build_enables(level)
        hosts = self._place_hosts(level)
        occupied = {(host["x"], host["y"]) for host in hosts}
        level.gates = self._place_gates(level, occupied)
        occupied.update((gate["sec_x"], gate["sec_y"]) for gate in level.gates)
        for gate in level.gates:
            occupied.update((key["x"], key["y"]) for key in gate.get("keysecs", []))
        level.items = self._place_items(level, occupied)
        for item in level.items:
            occupied.add((item["sec_x"], item["sec_y"]))
            occupied.update((key["x"], key["y"]) for key in item.get("keysecs", []))
        level.gems = self._place_gems(level, occupied)

        required = self._required_cells(level, hosts)
        terrain_profile = record.get("terrain_profile") or record.get("height_stats", {})
        hgt = synthesize_hgt_map(
            level.width,
            level.height,
            rng,
            median=int(terrain_profile.get("median", 0x7F) or 0x7F),
            required_cells=required,
            target_blocked_ratio=float(terrain_profile.get("blocked_edge_ratio", 0.0) or 0.0),
            terrain_profile=terrain_profile,
        )
        blg = filled_rows(level.width, level.height, 0)
        self._apply_host_buildings(level, hosts, typ, blg)
        self._apply_gate_tiles(level, typ, blg)
        self._apply_item_tiles(level, typ, blg)
        self._apply_gem_tiles(level, typ, blg)
        level.infrastructure = synthesize_infrastructure(level, hosts, occupied, typ, blg, hgt)
        own = self._own_map(level, hosts, level.infrastructure)

        level.maps = {"typ": typ, "own": own, "hgt": hgt, "blg": blg}
        level.robos = [self._robo(level, host) for host in hosts]
        level.squads = self._place_squads(level, hosts, occupied)
        level.prototype = self._prototype(level)
        level.required_route_cells = required
        level.tech_phase = {
            "baseline_level_ids": self._baseline_level_ids(level),
            "new_unlocks": list(record.get("new_unlocks", [])),
        }
        level.terrain_profile = self._terrain_metadata(terrain_profile, hgt)
        level.infrastructure_profile = self._infrastructure_metadata(level)

    # -- enables --------------------------------------------------------------

    def _synthesize_typ_map(self, level: _Gen4Level) -> tuple[MapRows, str]:
        if level.width * level.height <= 225:
            return synthesize_typ_map(level.source, level.tileset, level.width, level.height, level.rng)
        return self._scanline_typ_map(level), "scanline"

    def _scanline_typ_map(self, level: _Gen4Level) -> MapRows:
        model = adjacency_model_for(level.source, level.tileset)
        interior = model.interior_tiles
        rows: MapRows = []
        for y in range(level.height):
            row: list[int] = []
            for x in range(level.width):
                fixed = border_tile(x, y, level.width, level.height)
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
                row.append(model.weighted_choice(level.rng, candidates or interior))
            rows.append(row)
        return rows

    def _build_enables(self, level: _Gen4Level) -> tuple[list[dict[str, Any]], dict[int, set[int]]]:
        record = level.archetype.record
        enables: list[dict[str, Any]] = []
        legal: dict[int, set[int]] = {}
        enemy_enables = record.get("enemy_enables", {})
        for owner_text in sorted(enemy_enables, key=lambda value: int(value)):
            owner = int(owner_text)
            data = enemy_enables[owner_text]
            vehicles = self._filter_enable_vehicles(level.profile_id, owner, data.get("vehicles", []))
            buildings = self._filter_enable_buildings(owner, data.get("buildings", []))
            enables.append({"owner": owner, "vehicles": vehicles, "buildings": buildings})
            legal[owner] = set(vehicles)

        for enable in record.get("player_enables", []):
            owner = level.player_faction if int(enable["owner"]) == level.archetype.player_owner else int(enable["owner"])
            vehicles = self._filter_enable_vehicles(level.profile_id, owner, enable.get("vehicles", []))
            buildings = self._filter_enable_buildings(owner, enable.get("buildings", []))
            enables.append({"owner": owner, "vehicles": vehicles, "buildings": buildings})
            legal[owner] = set(vehicles)
        return enables, legal

    @staticmethod
    def _filter_enable_vehicles(profile_id: str, owner: int, vehicles: list[int]) -> list[int]:
        excluded: set[int] = set()
        if owner in {_FACTION_PLAYER, _FACTION_BLACK_SECT}:
            excluded |= set(ENABLE_EXCLUDED_VEHICLE_IDS)
        if profile_id == _MD_TAERKASTEN_PROFILE and owner in {_FACTION_TAERKASTEN, _FACTION_BLACK_SECT}:
            excluded |= set(MD_TAERKASTEN_ENABLE_EXCLUDED_VEHICLE_IDS)
        return [int(vehicle) for vehicle in vehicles if int(vehicle) not in excluded]

    @staticmethod
    def _filter_enable_buildings(owner: int, buildings: list[int]) -> list[int]:
        if owner == _FACTION_BLACK_SECT:
            return [int(building) for building in buildings if int(building) not in BLACK_SECT_ENABLE_EXCLUDED_BUILDING_IDS]
        return [int(building) for building in buildings]

    # -- placement ------------------------------------------------------------

    def _place_hosts(self, level: _Gen4Level) -> list[dict[str, Any]]:
        hosts: list[dict[str, Any]] = []
        occupied: set[tuple[int, int]] = set()
        for index, source_robo in enumerate(level.archetype.record.get("robos", [])):
            owner = int(source_robo.get("owner", level.player_faction))
            is_player = owner == level.archetype.player_owner
            faction = level.player_faction if is_player else owner
            cell = self._cell_from_entity(source_robo)
            if cell is None:
                cell = self._fallback_cell(level, occupied)
            else:
                cell = self._jitter_cell(level, cell, occupied, radius=2)
            occupied.add(cell)
            hosts.append({
                "faction": faction,
                "source_owner": owner,
                "source": source_robo,
                "x": cell[0],
                "y": cell[1],
                "is_player": is_player,
                "index": index,
            })
        if not any(host["is_player"] for host in hosts):
            cell = self._fallback_cell(level, occupied)
            hosts.insert(0, {"faction": level.player_faction, "source_owner": level.archetype.player_owner, "source": {}, "x": cell[0], "y": cell[1], "is_player": True, "index": 0})
        return hosts[:7]

    def _place_gates(self, level: _Gen4Level, occupied: set[tuple[int, int]]) -> list[dict[str, Any]]:
        gates: list[dict[str, Any]] = []
        for source_gate in level.archetype.record.get("gates", []):
            source_cell = (int(source_gate.get("sec_x", 1)), int(source_gate.get("sec_y", 1)))
            cell = self._jitter_cell(level, source_cell, occupied, radius=3)
            occupied.add(cell)
            keysecs: list[dict[str, int]] = []
            for key in source_gate.get("keysecs", []):
                key_cell = self._jitter_cell(level, (int(key["x"]), int(key["y"])), occupied, radius=3)
                occupied.add(key_cell)
                keysecs.append({"x": key_cell[0], "y": key_cell[1]})
            gates.append({
                "sec_x": cell[0],
                "sec_y": cell[1],
                "closed_bp": source_gate.get("closed_bp", 5),
                "opened_bp": source_gate.get("opened_bp", 6),
                "targets": list(source_gate.get("targets", [])),
                "keysecs": keysecs,
                "mb_status": source_gate.get("mb_status"),
            })
        if not gates:
            cell = self._fallback_cell(level, occupied)
            gates.append({"sec_x": cell[0], "sec_y": cell[1], "closed_bp": 5, "opened_bp": 6, "targets": [], "keysecs": [], "mb_status": "unknown"})
        return gates

    def _place_items(self, level: _Gen4Level, occupied: set[tuple[int, int]]) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for source_item in level.archetype.record.get("items", []):
            source_cell = (int(source_item.get("sec_x", 1)), int(source_item.get("sec_y", 1)))
            cell = self._jitter_cell(level, source_cell, occupied, radius=3)
            occupied.add(cell)
            item = dict(source_item)
            item["sec_x"], item["sec_y"] = cell
            item["keysecs"] = []
            for key in source_item.get("keysecs", []):
                key_cell = self._jitter_cell(level, (int(key["x"]), int(key["y"])), occupied, radius=3)
                occupied.add(key_cell)
                item["keysecs"].append({"x": key_cell[0], "y": key_cell[1]})
            items.append(item)
        return items

    def _place_gems(self, level: _Gen4Level, occupied: set[tuple[int, int]]) -> list[list[str]]:
        gems: list[list[str]] = []
        for source_gem in level.archetype.record.get("upgrade_gems", []):
            source_cell = (int(source_gem.get("sec_x") or 1), int(source_gem.get("sec_y") or 1))
            cell = self._jitter_cell(level, source_cell, occupied, radius=3)
            occupied.add(cell)
            gems.append(self._rewrite_gem(level, source_gem, cell))
        return gems

    def _place_squads(
        self,
        level: _Gen4Level,
        hosts: list[dict[str, Any]],
        occupied: set[tuple[int, int]],
    ) -> list[dict[str, Any]]:
        squads: list[dict[str, Any]] = []
        host_factions = {host["faction"] for host in hosts}
        for source_squad in level.archetype.record.get("squads", []):
            owner = int(source_squad.get("owner", level.player_faction))
            faction = level.player_faction if owner == level.archetype.player_owner else owner
            if faction not in host_factions and faction not in level.legal_vehicles_by_owner:
                continue
            source_cell = self._cell_from_entity(source_squad)
            cell = self._jitter_cell(level, source_cell or self._fallback_cell(level, occupied), occupied, radius=3)
            occupied.add(cell)
            vehicle = self._squad_vehicle(level, faction, int(source_squad.get("vehicle", 1)))
            num = max(1, min(32, int(source_squad.get("num", 1))))
            if vehicle in _SCOUT_VEHICLES:
                num = min(num, 2)
            squad = {
                "owner": faction,
                "vehicle": vehicle,
                "num": num,
                "pos_x": sector_to_world_x(cell[0], plus_one=True),
                "pos_z": sector_to_world_z(cell[1], plus_one=True),
            }
            if source_squad.get("mb_status") is not None:
                squad["mb_status"] = source_squad["mb_status"]
            if source_squad.get("useable"):
                squad["useable"] = True
            squads.append(squad)
            if len(squads) >= 100:
                break
        self._maybe_add_scout_near_player(level, hosts, occupied, squads)
        return squads

    def _maybe_add_scout_near_player(
        self,
        level: _Gen4Level,
        hosts: list[dict[str, Any]],
        occupied: set[tuple[int, int]],
        squads: list[dict[str, Any]],
    ) -> None:
        if len(squads) >= 100:
            return
        player_host = next((host for host in hosts if host.get("is_player")), None)
        if player_host is None:
            return
        candidates: list[tuple[int, int]] = []
        for owner, legal in sorted(level.legal_vehicles_by_owner.items()):
            if owner in {0, _FACTION_TUTOR, level.player_faction}:
                continue
            vehicle = self._scout_vehicle_for_owner(owner, legal)
            if vehicle is not None:
                candidates.append((owner, vehicle))
        if not candidates:
            return
        owner, vehicle = candidates[level.rng.rand_mod(len(candidates))]
        cell = self._scout_cell_near_player(level, (int(player_host["x"]), int(player_host["y"])), occupied)
        if cell is None:
            return
        occupied.add(cell)
        squads.append(
            {
                "owner": owner,
                "vehicle": vehicle,
                "num": 1,
                "pos_x": sector_to_world_x(cell[0], plus_one=True),
                "pos_z": sector_to_world_z(cell[1], plus_one=True),
            }
        )

    @staticmethod
    def _scout_vehicle_for_owner(owner: int, legal: set[int]) -> int | None:
        if owner == _FACTION_BLACK_SECT:
            scouts = sorted(set(legal) & _SCOUT_VEHICLES)
            return scouts[0] if scouts else None
        preferred = _SCOUT_VEHICLE_BY_OWNER.get(owner)
        if preferred in legal:
            return preferred
        scouts = sorted(set(legal) & _SCOUT_VEHICLES)
        return scouts[0] if scouts else None

    def _scout_cell_near_player(
        self,
        level: _Gen4Level,
        player_cell: tuple[int, int],
        occupied: set[tuple[int, int]],
    ) -> tuple[int, int] | None:
        px, py = player_cell
        candidates: list[tuple[int, int, int]] = []
        for y in range(max(1, py - 5), min(level.height - 1, py + 6)):
            for x in range(max(1, px - 5), min(level.width - 1, px + 6)):
                cell = (x, y)
                if cell in occupied:
                    continue
                distance = abs(x - px) + abs(y - py)
                if not (2 <= distance <= 7):
                    continue
                hgt = level.maps.get("hgt", [])
                if hgt and not required_cells_connected(hgt, [player_cell, cell]):
                    continue
                candidates.append((abs(distance - 4) * 4 + level.rng.rand_mod(5), x, y))
        if not candidates:
            return None
        candidates.sort()
        return candidates[0][1], candidates[0][2]

    # -- maps -----------------------------------------------------------------

    def _own_map(
        self,
        level: _Gen4Level,
        hosts: list[dict[str, Any]],
        infrastructure: list[dict[str, Any]],
    ) -> MapRows:
        rows = filled_rows(level.width, level.height, 0)
        seeds: list[dict[str, Any]] = [
            {"x": host["x"], "y": host["y"], "faction": host["faction"]}
            for host in hosts
            if host["faction"] != _FACTION_TUTOR
        ]
        seeds.extend(
            {"x": item["x"], "y": item["y"], "faction": item["owner"]}
            for item in infrastructure
            if int(item.get("owner", 0)) not in {0, _FACTION_TUTOR}
        )
        if not seeds:
            return rows
        for y in range(1, level.height - 1):
            for x in range(1, level.width - 1):
                nearest = min(seeds, key=lambda host: (host["x"] - x) ** 2 + (host["y"] - y) ** 2)
                rows[y][x] = int(nearest["faction"])
        for item in infrastructure:
            rows[int(item["y"])][int(item["x"])] = int(item["owner"])
        return rows

    def _apply_host_buildings(self, level: _Gen4Level, hosts: list[dict[str, Any]], typ: MapRows, blg: MapRows) -> None:
        for host in hosts:
            buildings = level.profile.roster.buildings_by_faction.get(host["faction"], ())
            if not buildings:
                continue
            building = int(buildings[0])
            x, y = host["x"], host["y"]
            blg[y][x] = building
            typ[y][x] = BUILDING_TYP_BY_ID.get(building, typ[y][x])

    def _apply_gate_tiles(self, level: _Gen4Level, typ: MapRows, blg: MapRows) -> None:
        for gate in level.gates:
            typ[gate["sec_y"]][gate["sec_x"]] = TYP_GATE_CLOSED_1
            blg[gate["sec_y"]][gate["sec_x"]] = 0

    def _apply_item_tiles(self, level: _Gen4Level, typ: MapRows, blg: MapRows) -> None:
        for item in level.items:
            for key in ("inactive_bp", "active_bp", "trigger_bp"):
                if item.get(key) is not None:
                    blg[item["sec_y"]][item["sec_x"]] = int(item[key])
                    break
            for key in item.get("keysecs", []):
                typ[key["y"]][key["x"]] = self._bomb_key_typ(level, typ, int(key["x"]), int(key["y"]))
                blg[key["y"]][key["x"]] = 0

    def _bomb_key_typ(self, level: _Gen4Level, typ: MapRows, x: int, y: int) -> int:
        if self._bomb_key_has_four_road_edges(str(getattr(level, "source", "")), typ, x, y):
            return TYP_GATE_CLOSED_1
        return TYP_GATE_CLOSED_2

    @staticmethod
    def _bomb_key_has_four_road_edges(source: str, typ: MapRows, x: int, y: int) -> bool:
        if not (0 < y < len(typ) - 1 and 0 < x < len(typ[y]) - 1):
            return False
        edges = _bomb_key_road_edge_tiles(source)
        if not all(edges.values()):
            return False
        return (
            int(typ[y - 1][x]) in edges["north"]
            and int(typ[y][x + 1]) in edges["east"]
            and int(typ[y + 1][x]) in edges["south"]
            and int(typ[y][x - 1]) in edges["west"]
        )

    def _apply_gem_tiles(self, level: _Gen4Level, typ: MapRows, blg: MapRows) -> None:
        for raw in level.gems:
            x = y = building = None
            for line in raw:
                stripped = line.strip().lower()
                if stripped.startswith("sec_x"):
                    x = int(stripped.split("=", 1)[1].split(";", 1)[0])
                elif stripped.startswith("sec_y"):
                    y = int(stripped.split("=", 1)[1].split(";", 1)[0])
                elif stripped.startswith("building"):
                    building = int(stripped.split("=", 1)[1].split(";", 1)[0])
            if x is None or y is None or building is None:
                continue
            blg[y][x] = building
            typ[y][x] = BUILDING_TYP_BY_ID.get(building, typ[y][x])

    # -- metadata -------------------------------------------------------------

    @staticmethod
    def _terrain_metadata(source_profile: dict[str, Any], generated_hgt: MapRows) -> dict[str, Any]:
        generated = terrain_metrics(generated_hgt)
        return {
            "source_unique_heights": int(source_profile.get("unique_count", 1) or 1),
            "generated_unique_heights": int(generated["unique_count"]),
            "source_height_range": int(source_profile.get("range", 0) or 0),
            "generated_height_range": int(generated["range"]),
            "source_blocked_edge_ratio": float(source_profile.get("blocked_edge_ratio", 0.0) or 0.0),
            "generated_blocked_edge_ratio": float(generated["blocked_edge_ratio"]),
        }

    @staticmethod
    def _infrastructure_metadata(level: _Gen4Level) -> dict[str, Any]:
        source_profile = level.archetype.record.get("infrastructure_profile", {})
        return {
            "source_counts": {
                "power": int(source_profile.get("counts", {}).get("power", 0) or 0),
                "flak": int(source_profile.get("counts", {}).get("flak", 0) or 0),
                "radar": int(source_profile.get("counts", {}).get("radar", 0) or 0),
            },
            "generated_counts": station_counts(level.infrastructure),
        }

    # -- entities -------------------------------------------------------------

    def _robo(self, level: _Gen4Level, host: dict[str, Any]) -> dict[str, Any]:
        source = host["source"]
        faction = int(host["faction"])
        is_player = bool(host["is_player"])
        out: dict[str, Any] = {"owner": faction}
        out["vehicle"] = self._player_vehicle(level, source) if is_player else self._host_vehicle(level, faction, source)
        energy = int(source.get("energy", 600000 if is_player else 1200000))
        out.update({
            "pos_x": sector_to_world_x(host["x"], plus_one=True),
            "pos_y": int(source.get("pos_y", -300)),
            "pos_z": sector_to_world_z(host["y"], plus_one=True),
            "energy": energy,
            "reload_const": int(source.get("reload_const", floor((((energy - 550000) / 4) + 550000) / 5) if is_player else floor(((energy - 500000) / 3) + 500000))),
        })
        if source.get("viewangle") is not None:
            out["viewangle"] = source["viewangle"]
        if source.get("mb_status") is not None:
            out["mb_status"] = source["mb_status"]
        if not is_player:
            for key, value in source.items():
                if not (key.endswith("_budget") or key.endswith("_delay")):
                    continue
                if key == "rad_budget" and level.zero_enemy_radar_budgets:
                    out[key] = 0
                elif key.endswith("_delay") and level.zero_enemy_station_delays:
                    out[key] = 0
                else:
                    out[key] = value
        return out

    def _player_vehicle(self, level: _Gen4Level, source: dict[str, Any]) -> int:
        by_level = level.profile.player_robo_by_level.get(level.level_id)
        if by_level:
            return by_level
        robos = level.profile.roster.player_robo_ids_by_faction.get(level.player_faction)
        if robos:
            return int(robos[-1])
        return int(level.profile.roster.host_vehicle_by_faction.get(level.player_faction, source.get("vehicle", 56)))

    def _host_vehicle(self, level: _Gen4Level, faction: int, source: dict[str, Any]) -> int:
        return int(level.profile.roster.host_vehicle_by_faction.get(faction, source.get("vehicle", 57)))

    def _squad_vehicle(self, level: _Gen4Level, faction: int, source_vehicle: int) -> int:
        if faction == level.player_faction:
            vehicles = tuple(level.profile.roster.vehicles_by_faction.get(faction, ()))
            if source_vehicle in vehicles:
                return source_vehicle
            return int(vehicles[level.rng.rand_mod(len(vehicles))]) if vehicles else source_vehicle
        legal = sorted(level.legal_vehicles_by_owner.get(faction, ()))
        if source_vehicle in legal:
            return source_vehicle
        if legal:
            return legal[level.rng.rand_mod(len(legal))]
        return source_vehicle

    # -- raw block rewrites ----------------------------------------------------

    def _prototype(self, level: _Gen4Level) -> list[str]:
        include = startup_include_for_level(level.profile_id, level.level_id)
        lines = [include]
        for line in level.archetype.record.get("player_baseline", {}).get("prototype", []):
            if str(line).strip().lower().startswith("include"):
                continue
            lines.append(str(line))
        return lines

    def _rewrite_gem(self, level: _Gen4Level, gem: dict[str, Any], cell: tuple[int, int]) -> list[str]:
        lines: list[str] = []
        for line in gem.get("raw", []):
            rewritten = _SEC_X_RE.sub(rf"\g<1>{cell[0]}\2", str(line))
            rewritten = _SEC_Y_RE.sub(rf"\g<1>{cell[1]}\2", rewritten)
            rewritten = self._remap_player_enable_owner(level, rewritten)
            lines.append(rewritten)
        return lines

    def _remap_player_enable_owner(self, level: _Gen4Level, line: str) -> str:
        def replace(match: re.Match[str]) -> str:
            owner = int(match.group(2))
            if owner == level.archetype.player_owner:
                return f"{match.group(1)}{level.player_faction}"
            return match.group(0)

        return _ENABLE_OWNER_RE.sub(replace, line)

    # -- misc -----------------------------------------------------------------

    def _required_cells(self, level: _Gen4Level, hosts: list[dict[str, Any]]) -> list[tuple[int, int]]:
        cells = [(host["x"], host["y"]) for host in hosts]
        for gate in level.gates:
            cells.append((gate["sec_x"], gate["sec_y"]))
            cells.extend((key["x"], key["y"]) for key in gate.get("keysecs", []))
        for item in level.items:
            cells.append((item["sec_x"], item["sec_y"]))
            cells.extend((key["x"], key["y"]) for key in item.get("keysecs", []))
        for raw in level.gems:
            x = y = None
            for line in raw:
                stripped = line.strip().lower()
                if stripped.startswith("sec_x"):
                    x = int(stripped.split("=", 1)[1].split(";", 1)[0])
                elif stripped.startswith("sec_y"):
                    y = int(stripped.split("=", 1)[1].split(";", 1)[0])
            if x is not None and y is not None:
                cells.append((x, y))
        return list(dict.fromkeys((x, y) for x, y in cells if 0 < x < level.width - 1 and 0 < y < level.height - 1))

    def _baseline_level_ids(self, level: _Gen4Level) -> list[int]:
        result: list[int] = []
        for candidate in level.profile.level_ids:
            if candidate == level.level_id:
                break
            result.append(int(candidate))
        return result

    def _jitter_cell(
        self,
        level: _Gen4Level,
        source_cell: tuple[int, int],
        occupied: set[tuple[int, int]],
        *,
        radius: int,
    ) -> tuple[int, int]:
        sx = max(1, min(level.width - 2, int(source_cell[0])))
        sy = max(1, min(level.height - 2, int(source_cell[1])))
        best = (sx, sy)
        for _ in range(48):
            x = max(1, min(level.width - 2, sx + level.rng.rand_range(-radius, radius)))
            y = max(1, min(level.height - 2, sy + level.rng.rand_range(-radius, radius)))
            if (x, y) not in occupied:
                return x, y
            best = (x, y)
        if best not in occupied:
            return best
        return self._fallback_cell(level, occupied)

    def _fallback_cell(self, level: _Gen4Level, occupied: set[tuple[int, int]]) -> tuple[int, int]:
        for _ in range(128):
            cell = (level.rng.rand_range(1, level.width - 2), level.rng.rand_range(1, level.height - 2))
            if cell not in occupied:
                return cell
        for y in range(1, level.height - 1):
            for x in range(1, level.width - 1):
                if (x, y) not in occupied:
                    return x, y
        return 1, 1

    @staticmethod
    def _cell_from_entity(entity: dict[str, Any]) -> tuple[int, int] | None:
        if entity.get("pos_x") is None or entity.get("pos_z") is None:
            return None
        x = max(1, int(round((int(entity["pos_x"]) - 1) / 1200 - 0.5)))
        y = max(1, int(round((-(int(entity["pos_z"]) - 1)) / 1200 - 0.5)))
        return x, y


@lru_cache(maxsize=None)
def _bomb_key_road_edge_tiles(source: str) -> dict[str, frozenset[int]]:
    edges: dict[str, set[int]] = {"north": set(), "east": set(), "south": set(), "west": set()}
    if not source:
        return {key: frozenset() for key in edges}
    for skeleton in skeletons_for_source(source):
        typ = skeleton.maps().get("typ", [])
        if not typ:
            continue
        for item in skeleton.record.get("items", []):
            for key in item.get("keysecs", []):
                x = int(key["x"])
                y = int(key["y"])
                if not (0 < y < len(typ) - 1 and 0 < x < len(typ[y]) - 1):
                    continue
                if int(typ[y][x]) != TYP_GATE_CLOSED_1:
                    continue
                edges["north"].add(int(typ[y - 1][x]))
                edges["east"].add(int(typ[y][x + 1]))
                edges["south"].add(int(typ[y + 1][x]))
                edges["west"].add(int(typ[y][x - 1]))
    return {key: frozenset(values) for key, values in edges.items()}
