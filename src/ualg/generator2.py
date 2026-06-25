"""Python port of the PHP-derived former Generator3, exposed as Generator2."""

from __future__ import annotations

from dataclasses import dataclass, field
from math import ceil, floor
from time import time
from typing import Any

from .constants import (
    GENERATOR2_BUILDINGS,
    GENERATOR2_CAMPAIGN_LEVEL_IDS,
    GENERATOR2_FACTION_IDS,
    GENERATOR2_FACTIONS,
    GENERATOR2_HOST_VEHICLES,
    GENERATOR2_LEVELS,
    GENERATOR2_SCOUT_VEHICLES,
    GENERATOR2_SET_LIST,
    GENERATOR2_SKIES,
    GENERATOR2_VEHICLES,
    level_filename,
)
from .ldf import LDFWriter
from .models import GeneratedCampaign, GeneratedLevel, MapRows
from .rng import MSVCRTRandom


@dataclass
class _Level:
    level_id: int
    rng: MSVCRTRandom
    seed: int
    width: int = 0
    height: int = 0
    tileset: int = 1
    gates: list[dict[str, Any]] = field(default_factory=list)
    bombs: list[dict[str, Any]] = field(default_factory=list)
    squads: list[dict[str, Any]] = field(default_factory=list)
    flaks: list[dict[str, Any]] = field(default_factory=list)
    powers: list[dict[str, Any]] = field(default_factory=list)
    excluded: list[dict[str, Any]] = field(default_factory=list)
    hosts: dict[str, list[dict[str, int]]] = field(default_factory=dict)
    maps: dict[str, MapRows] = field(default_factory=dict)


class Generator2:
    """Former PHP/Godot Generator3 implementation, renamed to Generator2."""

    campaign_level_ids = tuple(GENERATOR2_CAMPAIGN_LEVEL_IDS)

    def generate_single(self, seed: int = 0, level_id: int = 1) -> GeneratedLevel:
        if level_id not in GENERATOR2_LEVELS:
            raise ValueError(f"unknown Generator2 level id: {level_id}")
        seed = self._normalize_seed(seed)
        rng = MSVCRTRandom(seed)
        return self._generate_level(level_id, rng, seed)

    def generate_campaign(self, seed: int = 0) -> GeneratedCampaign:
        seed = self._normalize_seed(seed)
        rng = MSVCRTRandom(seed)
        levels = [self._generate_level(level_id, rng, seed) for level_id in GENERATOR2_CAMPAIGN_LEVEL_IDS]
        return GeneratedCampaign(seed=seed, levels=levels)

    def _generate_level(self, level_id: int, rng: MSVCRTRandom, seed: int) -> GeneratedLevel:
        level = _Level(level_id=level_id, rng=rng, seed=seed)
        self._choose_map_size(level)
        level.tileset = rng.rand_range(1, 6)
        self._create_gate(level)
        self._create_player_station(level)
        self._create_enemy_stations(level)
        self._create_bombs(level)
        self._create_squads(level)
        for map_type in ("typ", "own", "hgt", "blg"):
            self._make_map(level, map_type)
        text = self._write_level(level)
        return GeneratedLevel(
            filename=level_filename(level_id),
            level_id=level_id,
            seed=seed,
            width=level.width,
            height=level.height,
            tileset=level.tileset,
            text=text,
            maps=level.maps,
            metadata={"generator": "generator2"},
        )

    @staticmethod
    def _normalize_seed(seed: int) -> int:
        return int(seed) if seed else int(time())

    def _choose_map_size(self, level: _Level) -> None:
        while True:
            level.width = level.rng.rand_range(3, 32)
            level.height = level.rng.rand_range(3, 32)
            if (level.width - 2) * (level.height - 2) >= 80:
                return

    def _create_gate(self, level: _Level) -> None:
        coords = self._random_xy(level, "gates")
        if coords:
            level.gates.append({"x": coords["x"], "y": coords["y"], "targets": GENERATOR2_LEVELS[level.level_id]})

    def _create_player_station(self, level: _Level) -> None:
        level.hosts["res"] = [self._random_xy(level)]

    def _create_enemy_stations(self, level: _Level) -> None:
        self._add_enemy_station(level, require_any_enemy=True)
        max_total_hosts = floor(level.width * level.height * 2 / 192)
        for _ in range(max_total_hosts):
            if self._total_hosts(level) >= 6:
                break
            if level.rng.rand_range(0, 1):
                self._add_enemy_station(level, require_any_enemy=False)
        level.excluded.clear()

    def _add_enemy_station(self, level: _Level, require_any_enemy: bool) -> None:
        for _ in range(100):
            faction = level.rng.choice(GENERATOR2_FACTIONS)
            if self._total_hosts(level, faction) >= 2:
                if require_any_enemy and self._total_hosts(level) == 0:
                    continue
                return
            station = self._distribute_host(level)
            if not station:
                if require_any_enemy and self._total_hosts(level) == 0:
                    continue
                return
            level.hosts.setdefault(faction, []).append(station)
            return

    def _create_bombs(self, level: _Level) -> None:
        for _ in range(2):
            if level.rng.rand_range(0, 3) != 0:
                continue
            coords = self._random_xy(level, "hosts,gates")
            if not coords:
                continue
            bomb = {"x": coords["x"], "y": coords["y"], "timeout": level.rng.rand_range(360, 2100) * 1000, "keys": []}
            level.bombs.append(bomb)
            for _ in range(8):
                if level.rng.rand_range(0, 1):
                    key = self._random_xy(level, "gates,bombs")
                    if key:
                        bomb["keys"].append(key)

    def _create_squads(self, level: _Level) -> None:
        for _ in range(5 * (self._total_hosts(level) + 1)):
            if level.rng.rand_range(0, 1):
                self._add_squad(level)

    def _add_squad(self, level: _Level) -> None:
        coords = self._random_xy(level, "hosts,bombs,squads,flaks")
        if not coords:
            return
        faction = level.rng.choice(self._present_factions(level))
        vehicle = level.rng.choice(GENERATOR2_VEHICLES[faction])
        if vehicle in GENERATOR2_SCOUT_VEHICLES:
            squad_size = 1
        else:
            squad_size = level.rng.rand_range(3, 8)
            if faction != "res" and level.rng.rand_range(0, 5) == 0:
                squad_size *= 2
        level.rng.rand_range(0, 4)  # Legacy template consumes this but does not serialize squad mb_status.
        level.squads.append({
            "faction": faction,
            "vehicle": vehicle,
            "num": squad_size,
            "x": coords["x"],
            "y": coords["y"],
        })

    def _write_level(self, level: _Level) -> str:
        writer = LDFWriter(property_style="php")
        self._write_header(writer, level)
        self._write_beam_gates(writer, level)
        self._write_player_station(writer, level)
        self._write_enemy_stations(writer, level)
        self._write_bombs(writer, level)
        self._write_squads(writer, level)
        self._write_prototypes(writer, level)
        self._write_maps(writer, level)
        return writer.getvalue()

    def _write_header(self, writer: LDFWriter, level: _Level) -> None:
        writer.line(";#*+ don't edit the magic runes")
        writer.line("")
        writer.line(";------------------------------------------------------------")
        writer.line(";--- Generated by Urban Assault Level Generator           ---")
        writer.line(";--- Generator: Generator2 (PHP-derived port)             ---")
        writer.line(";------------------------------------------------------------")
        writer.line(";--- Generation Parameters:")
        writer.line(f";--- Seed: {level.seed}")
        writer.line(f";--- Level ID: {level.level_id}")
        writer.line(f";--- Tileset: {level.tileset}")
        writer.line(f";--- Map Size: {level.width}x{level.height}")
        writer.line(";------------------------------------------------------------")
        writer.line(";--- Main Level Info                                      ---")
        writer.line(";------------------------------------------------------------")
        writer.line("begin_level")
        writer.property("set", level.tileset)
        writer.property("sky", f"objects/{level.rng.choice(GENERATOR2_SKIES)}.base")
        for slot, palette in enumerate(["standard", "red", "blau", "gruen", "inverse", "invdark", "sw", "invtuerk"]):
            writer.property(f"slot{slot}", f"palette/{palette}.pal")
        writer.end_block()
        writer.line("")
        writer.line("; Mission Briefing Map")
        writer.line("begin_mbmap")
        writer.property("name", "MB_15.IFF")
        writer.end_block()
        writer.line("")
        writer.line("; Mission Debriefing Map")
        writer.line("begin_dbmap")
        writer.property("name", "DB_15.IFF")
        writer.end_block()
        writer.line("")

    def _write_beam_gates(self, writer: LDFWriter, level: _Level) -> None:
        writer.line("; Beam Gates")
        for gate in level.gates:
            writer.line("")
            writer.line("begin_gate")
            writer.property("sec_x", gate["x"])
            writer.property("sec_y", gate["y"])
            writer.property("closed_bp", 5)
            writer.property("opened_bp", 6)
            for target in gate["targets"]:
                writer.property("target_level", target)
            for _ in range(6):
                if level.rng.rand_range(0, 1):
                    writer.property("keysec_x", self._random_x(level))
                    writer.property("keysec_y", self._random_y(level))
            writer.property("mb_status", "unknown")
            writer.end_block()
        writer.line("")

    def _write_player_station(self, writer: LDFWriter, level: _Level) -> None:
        station = level.hosts["res"][0]
        energy = level.rng.rand_range(6, 10) * 100000
        reload_const = floor((((energy - 550000) / 4) + 550000) / 5)
        writer.line("; Player Host Station")
        writer.line("")
        writer.line("begin_robo")
        writer.property("owner", 1)
        writer.property("vehicle", 56)
        writer.property("pos_x", self._get_position(station["x"]))
        writer.property("pos_y", level.rng.rand_range(20, 45) * -10)
        writer.property("pos_z", self._get_position(station["y"], vertical=True))
        writer.property("energy", energy)
        writer.property("reload_const", reload_const)
        writer.end_block()
        writer.line("")
        writer.line("; Enemy Host Stations")

    def _write_enemy_stations(self, writer: LDFWriter, level: _Level) -> None:
        for faction in level.hosts:
            if faction == "res":
                continue
            for station in level.hosts[faction]:
                energy = level.rng.rand_range(8, 22) * 100000
                reload_const = floor(((energy - 500000) / 3) + 500000)
                host_vehicle = GENERATOR2_HOST_VEHICLES.get(faction, 57)
                if faction == "gho":
                    host_vehicle = 57 if level.rng.rand_range(0, 2) != 0 else 59
                writer.line("")
                writer.line("begin_robo")
                writer.property("owner", GENERATOR2_FACTION_IDS[faction])
                writer.property("vehicle", host_vehicle)
                writer.property("pos_x", self._get_position(station["x"]))
                writer.property("pos_y", level.rng.rand_range(20, 45) * -10)
                writer.property("pos_z", self._get_position(station["y"], vertical=True))
                writer.property("energy", energy)
                writer.property("reload_const", reload_const)
                if level.rng.rand_range(0, 1) == 0:
                    writer.property("mb_status", "unknown")
                writer.property("con_budget", level.rng.rand_range(80, 90))
                writer.property("con_delay", level.rng.rand_range(0, 300) * 1000)
                writer.property("def_budget", level.rng.rand_range(70, 100))
                writer.property("def_delay", level.rng.rand_range(0, 300) * 1000)
                writer.property("rec_budget", level.rng.rand_range(50, 80))
                writer.property("rec_delay", level.rng.rand_range(0, 300) * 1000)
                writer.property("rob_budget", level.rng.rand_range(50, 90))
                writer.property("rob_delay", level.rng.rand_range(0, 300) * 1000)
                writer.property("pow_budget", level.rng.rand_range(40, 70))
                writer.property("pow_delay", level.rng.rand_range(0, 300) * 1000)
                writer.property("rad_budget", level.rng.rand_range(0, 10))
                writer.property("rad_delay", level.rng.rand_range(600, 1800) * 1000)
                writer.property("saf_budget", level.rng.rand_range(50, 100))
                writer.property("saf_delay", level.rng.rand_range(0, 300) * 1000)
                writer.property("cpl_budget", level.rng.rand_range(30, 50))
                writer.property("cpl_delay", level.rng.rand_range(0, 300) * 1000)
                writer.end_block()

    def _write_bombs(self, writer: LDFWriter, level: _Level) -> None:
        writer.line("")
        writer.line("; Stoudson Bomb")
        for bomb in level.bombs:
            writer.line("")
            writer.line("begin_item")
            writer.property("sec_x", bomb["x"])
            writer.property("sec_y", bomb["y"])
            writer.property("inactive_bp", 68 if level.tileset == 6 else 35)
            writer.property("active_bp", 69 if level.tileset == 6 else 36)
            writer.property("trigger_bp", 70 if level.tileset == 6 else 36)
            writer.property("type", 1)
            writer.property("countdown", bomb["timeout"])
            for key in bomb["keys"]:
                writer.property("keysec_x", key["x"])
                writer.property("keysec_y", key["y"])
            writer.end_block()
        writer.line("")

    def _write_squads(self, writer: LDFWriter, level: _Level) -> None:
        writer.line(";Predefined Squad")
        for squad in level.squads:
            writer.line("")
            writer.line("begin_squad")
            writer.property("owner", GENERATOR2_FACTION_IDS[squad["faction"]])
            writer.property("vehicle", squad["vehicle"])
            writer.property("num", squad["num"])
            writer.property("pos_x", self._get_position(squad["x"]))
            writer.property("pos_z", self._get_position(squad["y"], vertical=True))
            writer.end_block()
        writer.line("")

    def _write_prototypes(self, writer: LDFWriter, level: _Level) -> None:
        writer.line("; Prototype Modifications")
        writer.line("")
        writer.line("include data:scripts/startup2.scr")
        for faction in self._present_factions(level):
            writer.line("")
            writer.line(f"begin_enable {GENERATOR2_FACTION_IDS[faction]}")
            for vehicle in GENERATOR2_VEHICLES[faction]:
                writer.property("vehicle", vehicle)
            for building in GENERATOR2_BUILDINGS[faction]:
                writer.property("building", building)
            writer.end_block()
        writer.line("")

    def _write_maps(self, writer: LDFWriter, level: _Level) -> None:
        writer.line("begin_maps")
        for map_name in ("typ", "own", "hgt", "blg"):
            writer.map_block(f"{map_name}_map", level.maps[map_name], level.width, level.height, php_style=True)
        writer.end_block()

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
                y = self._random_x(level)
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
                    coords = self._random_xy(level, "hosts,gates,bombs")
                    if coords:
                        current[coords["y"]][coords["x"]] = 63
        level.maps[map_type] = current

    @staticmethod
    def _reset_map(level: _Level, map_type: str) -> MapRows:
        value = 7 if map_type == "own" else 128 if map_type == "hgt" else 0
        return [[value for _ in range(level.width)] for _ in range(level.height)]

    def _set_territory(self, level: _Level, current: MapRows, faction: str, max_territory: float) -> None:
        faction_id = GENERATOR2_FACTION_IDS[faction]
        iterations = ceil(max_territory)
        if faction == "res":
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
        current[y][x] = value & 0xFF

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
        return sum(len(stations) for host_faction, stations in level.hosts.items() if host_faction != "res")

    @staticmethod
    def _present_factions(level: _Level) -> list[str]:
        return list(level.hosts.keys())

    @staticmethod
    def _get_station_sectors(level: _Level) -> list[dict[str, Any]]:
        result = []
        for faction, stations in level.hosts.items():
            for station in stations:
                result.append({"x": station["x"], "y": station["y"], "faction": faction})
        return result
