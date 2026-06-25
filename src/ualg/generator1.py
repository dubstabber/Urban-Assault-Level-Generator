"""Generator1: Random UA-derived generator with improved defaults."""

from __future__ import annotations

from dataclasses import dataclass, field
from time import time
from typing import Any

from .constants import (
    BLG_PLAYER_BASE,
    BLG_SUPERITEM,
    BUILDING_TYP_BY_ID,
    BUILDINGS_BY_FACTION,
    BUILDINGS_PLAYER_IDS,
    BUILDINGS_PLAYER_PROBABILITIES,
    FACTION_BLACK_SECT,
    FACTION_GHORKOVS,
    FACTION_MYKONIANS,
    FACTION_PLAYER,
    FACTION_SULGOGARS,
    FACTION_TAERKASTEN,
    FACTION_TUTOR,
    GENERATOR1_CAMPAIGN_FILENAMES,
    GENERATOR1_PLAYER_TECH_BUILDING_IDS,
    GENERATOR1_PLAYER_TECH_VEHICLE_IDS,
    HOST_BUILDING_BY_FACTION,
    HOST_VEHICLE_BY_FACTION,
    SKY_OPTIONS,
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
    TYP_MAP_INTERIOR_LOOKUP,
    TYP_PLAYER_BASE,
    TYP_SUPERITEM,
    VEHICLES_BY_FACTION,
    VEHICLES_PLAYER_IDS,
    VEHICLES_PLAYER_PROBABILITIES,
    level_id_from_filename,
    sector_to_world_x,
    sector_to_world_z,
)
from .data import tileset_compatibility
from .ldf import LDFWriter
from .models import GeneratedCampaign, GeneratedLevel, MapRows
from .rng import MSVCRTRandom


CATEGORY_DIM_RANGES = {
    1: (6, 10, 6, 10),
    2: (8, 13, 10, 25),
    3: (12, 18, 12, 28),
    4: (5, 7, 15, 25),
    5: (19, 22, 19, 22),
    6: (20, 27, 20, 27),
    7: (20, 25, 12, 25),
    8: (40, 45, 3, 3),
    9: (20, 25, 20, 25),
    10: (29, 32, 29, 32),
    11: (38, 45, 32, 32),
    12: (20, 25, 20, 25),
}

CATEGORY_ENERGY_PARAMS: dict[int, dict[Any, Any]] = {
    1: {"player": 320000, FACTION_TUTOR: (40, 40, 4000)},
    2: {"player": 360000, FACTION_GHORKOVS: (200, 75, 1000)},
    3: {"player": 460000, FACTION_GHORKOVS: (250, 100, 1000), FACTION_TAERKASTEN: (250, 100, 1000)},
    4: {"player": 600000, FACTION_GHORKOVS: (375, 125, 1000)},
    5: {"player": 640000, FACTION_GHORKOVS: (390, 140, 1000), FACTION_MYKONIANS: (390, 140, 1000)},
    6: {"player": 730000, FACTION_GHORKOVS: (400, 150, 1000), FACTION_BLACK_SECT: (400, 150, 1000)},
    7: {
        "player": 820000,
        FACTION_GHORKOVS: (475, 170, 1000),
        FACTION_TAERKASTEN: (475, 170, 1000),
        FACTION_MYKONIANS: (475, 170, 1000),
        FACTION_SULGOGARS: (475, 170, 1000),
    },
    8: {"player": 870000, FACTION_SULGOGARS: (575, 190, 1000)},
    9: {
        "player": 910000,
        FACTION_SULGOGARS: (700, 210, 1000),
        FACTION_BLACK_SECT: (700, 210, 1000),
        FACTION_MYKONIANS: (700, 210, 1000),
        FACTION_TAERKASTEN: (700, 210, 1000),
    },
    10: {
        "player": 1000000,
        FACTION_GHORKOVS: (800, 210, 1000),
        FACTION_SULGOGARS: (800, 210, 1000),
        FACTION_BLACK_SECT: (800, 210, 1000),
        FACTION_TAERKASTEN: (800, 210, 1000),
    },
    11: {
        "player": 1000000,
        FACTION_GHORKOVS: (1000, 250, 1000),
        FACTION_SULGOGARS: (1000, 250, 1000),
        FACTION_MYKONIANS: (1000, 250, 1000),
        FACTION_BLACK_SECT: (1000, 250, 1000),
        FACTION_TAERKASTEN: (1000, 250, 1000),
    },
    12: {
        "player": 130000000,
        FACTION_SULGOGARS: (150, 300, 1000),
        FACTION_MYKONIANS: (150, 300, 1000),
        FACTION_TAERKASTEN: (150, 300, 1000),
        FACTION_GHORKOVS: (150, 300, 1000),
    },
}


@dataclass
class Generator1CustomOptions:
    seed: int = 0
    difficulty: int = 5
    improved: bool = True
    width: int | None = None
    height: int | None = None
    gate_target_level_id: int = 0
    gate_key_count: int | None = None
    win_movie: bool = False
    lose_movie: bool = False
    player_energy: int | None = None
    ai_slot_present: dict[int, list[bool]] = field(default_factory=dict)
    ai_slot_energy: dict[int, list[int]] = field(default_factory=dict)
    ai_slot_host_vehicle_id: dict[int, list[int]] = field(default_factory=dict)
    ai_host_vehicle_id: dict[int, int] = field(default_factory=dict)
    superitem_flags: list[bool] | None = None
    random_superitems: bool = False
    superitem_countdowns: dict[int, int] = field(default_factory=dict)
    enabled_vehicles: dict[int, list[int]] = field(default_factory=dict)
    enabled_buildings: dict[int, list[int]] = field(default_factory=dict)


@dataclass
class _State:
    rng: MSVCRTRandom
    seed: int
    difficulty: int = 5
    level_index: int = 1
    level_id: int = 1
    scenario_category: int = 0
    improved: bool = True
    generator1_campaign_mode: bool = False
    emit_player_enablement: bool = True
    gate_target_level_id: int = 0
    min_width: int = 8
    max_width: int = 20
    min_height: int = 8
    max_height: int = 20
    width: int = 0
    height: int = 0
    tileset: int = 1
    player_energy: int = 500000
    faction_enables: list[bool] = field(default_factory=lambda: [False] * 8)
    ai_slot_present: list[list[bool]] = field(default_factory=lambda: [[False] * 3 for _ in range(8)])
    ai_slot_energy: list[list[int]] = field(default_factory=lambda: [[0] * 3 for _ in range(8)])
    ai_slot_world: list[list[tuple[int, int] | None]] = field(default_factory=lambda: [[None] * 3 for _ in range(8)])
    ai_slot_host_vehicle_id: list[list[int]] = field(default_factory=lambda: [[0] * 3 for _ in range(8)])
    ai_host_vehicle_id: list[int] = field(default_factory=lambda: [0] * 8)
    superitem_flags: list[bool] = field(default_factory=lambda: [False, False])
    force_player_base_model: bool = False
    win_movie: bool = False
    lose_movie: bool = False
    base_x: int = 0
    base_y: int = 0
    player_host_x: int = 0
    player_host_y: int = 0
    player_vehicle_flags: list[bool] = field(default_factory=lambda: [False] * len(GENERATOR1_PLAYER_TECH_VEHICLE_IDS))
    player_building_flags: list[bool] = field(default_factory=lambda: [False] * len(GENERATOR1_PLAYER_TECH_BUILDING_IDS))
    maps: dict[str, MapRows] = field(default_factory=dict)
    gate_keys: list[tuple[int, int]] = field(default_factory=list)
    gate_key_count_override: int | None = None
    superitems: list[dict[str, Any]] = field(default_factory=list)
    superitem_countdown_overrides: dict[int, int] = field(default_factory=dict)
    forced_enabled_vehicles: dict[int, list[int]] = field(default_factory=dict)
    forced_enabled_buildings: dict[int, list[int]] = field(default_factory=dict)
    reserved_sectors: set[tuple[int, int]] = field(default_factory=set)
    last_superitem_key_count: int = 0

    @property
    def width_interior(self) -> int:
        return max(1, self.width - 2)

    @property
    def height_interior(self) -> int:
        return max(1, self.height - 2)

    def interior(self, x: int, y: int) -> bool:
        return 0 < x < self.width - 1 and 0 < y < self.height - 1

    def get(self, map_name: str, x: int, y: int) -> int:
        return self.maps[map_name][y][x]

    def set(self, map_name: str, x: int, y: int, value: int) -> None:
        self.maps[map_name][y][x] = value & 0xFF


class Generator1:
    """Random UA-derived generator with Godot-improved defaults."""

    campaign_filenames = tuple(GENERATOR1_CAMPAIGN_FILENAMES)

    def generate_single(
        self,
        seed: int = 0,
        difficulty: int = 5,
        skill: int = 0,
        improved: bool = True,
    ) -> GeneratedLevel:
        seed = self._normalize_seed(seed)
        state = _State(rng=MSVCRTRandom(seed), seed=seed, difficulty=difficulty, improved=improved)
        state.scenario_category = self.category_for_skill(skill) if skill else 0
        state.emit_player_enablement = True
        state.gate_target_level_id = 0
        return self._generate(state, "level_01.ldf")

    def generate_campaign(self, seed: int = 0, difficulty: int = 5, improved: bool = True) -> GeneratedCampaign:
        seed = self._normalize_seed(seed)
        rng = MSVCRTRandom(seed)
        vehicle_flags = [False] * len(GENERATOR1_PLAYER_TECH_VEHICLE_IDS)
        building_flags = [False] * len(GENERATOR1_PLAYER_TECH_BUILDING_IDS)
        if len(vehicle_flags) > 2:
            vehicle_flags[2] = True
        levels: list[GeneratedLevel] = []
        for i, filename in enumerate(GENERATOR1_CAMPAIGN_FILENAMES):
            state = _State(rng=rng, seed=rng.state, difficulty=difficulty, improved=improved)
            state.level_index = i + 1
            state.level_id = level_id_from_filename(filename)
            state.generator1_campaign_mode = True
            state.emit_player_enablement = False
            state.player_vehicle_flags = vehicle_flags
            state.player_building_flags = building_flags
            state.scenario_category = self.category_for_campaign_index(state.level_index)
            if i + 1 < len(GENERATOR1_CAMPAIGN_FILENAMES):
                state.gate_target_level_id = level_id_from_filename(GENERATOR1_CAMPAIGN_FILENAMES[i + 1])
            else:
                state.gate_target_level_id = 0
            levels.append(self._generate(state, filename))
            vehicle_flags = state.player_vehicle_flags
            building_flags = state.player_building_flags
        return GeneratedCampaign(seed=seed, levels=levels)

    def generate_custom(self, options: Generator1CustomOptions) -> GeneratedLevel:
        seed = self._normalize_seed(options.seed)
        state = _State(rng=MSVCRTRandom(seed), seed=seed, difficulty=options.difficulty, improved=options.improved)
        state.emit_player_enablement = True
        self._apply_custom_options(state, options)
        return self._generate(state, "custom_level.ldf", apply_scenario=not self._has_custom_scenario(options))

    @staticmethod
    def category_for_skill(skill: int) -> int:
        return max(1, min(11, int(skill)))

    @staticmethod
    def category_for_campaign_index(level_index: int) -> int:
        if level_index <= 2:
            return 1
        if level_index <= 8:
            return 2
        if level_index <= 11:
            return 3
        if level_index <= 15:
            return 4
        if level_index <= 20:
            return 5
        if level_index <= 25:
            return 6
        if level_index <= 29:
            return 7
        if level_index == 30:
            return 8
        if level_index <= 36:
            return 9
        if level_index <= 42:
            return 10
        if level_index == 43:
            return 11
        if level_index == 44:
            return 12
        return 1

    @staticmethod
    def _normalize_seed(seed: int) -> int:
        return int(seed) if seed else int(time())

    def _generate(self, state: _State, filename: str, apply_scenario: bool = True) -> GeneratedLevel:
        if apply_scenario:
            self._apply_scenario(state)
        if state.width <= 0 or state.height <= 0:
            self._choose_map_size(state)
        self._generate_height_map(state)
        state.tileset = state.rng.rand_range(1, 6)
        self._init_typ_map(state)
        self._init_own_map(state)
        state.maps["blg"] = [[0 for _ in range(state.width)] for _ in range(state.height)]
        self._place_player_base(state)
        self._place_hosts_and_ambient(state)
        self._seed_superitems(state)
        self._repair_building_ownership(state)
        text = self._write_level(state)
        return GeneratedLevel(
            filename=filename,
            level_id=state.level_id,
            seed=state.seed,
            width=state.width,
            height=state.height,
            tileset=state.tileset,
            text=text,
            maps=state.maps,
            metadata={
                "generator": "generator1",
                "scenario_category": state.scenario_category,
                "player_host": (state.player_host_x, state.player_host_y),
                "base": (state.base_x, state.base_y),
            },
        )

    def _apply_custom_options(self, state: _State, options: Generator1CustomOptions) -> None:
        state.faction_enables[FACTION_PLAYER] = True
        state.gate_target_level_id = max(0, int(options.gate_target_level_id))
        state.gate_key_count_override = _clamp_optional(options.gate_key_count, 0, 16)
        state.win_movie = bool(options.win_movie)
        state.lose_movie = bool(options.lose_movie)
        state.superitem_countdown_overrides = {
            int(index): max(0, int(value))
            for index, value in options.superitem_countdowns.items()
            if int(index) in (1, 2)
        }
        state.forced_enabled_vehicles = {
            int(faction): list(dict.fromkeys(int(vehicle) for vehicle in vehicles))
            for faction, vehicles in options.enabled_vehicles.items()
        }
        state.forced_enabled_buildings = {
            int(faction): list(dict.fromkeys(int(building) for building in buildings))
            for faction, buildings in options.enabled_buildings.items()
        }

        if options.width is not None and options.height is not None:
            state.width = max(4, min(45, int(options.width)))
            state.height = max(3, min(32, int(options.height)))
            state.min_width = state.max_width = state.width
            state.min_height = state.max_height = state.height

        if options.player_energy is not None:
            state.player_energy = max(1, int(options.player_energy))

        if options.superitem_flags is not None:
            flags = list(options.superitem_flags[:2])
            state.superitem_flags = (flags + [False, False])[:2]
        elif options.random_superitems:
            count = state.rng.rand_mod(3)
            state.superitem_flags = [index < count for index in range(2)]

        for faction, present_slots in options.ai_slot_present.items():
            faction = int(faction)
            if not 0 <= faction < len(state.ai_slot_present):
                continue
            any_present = False
            for slot, present in enumerate(present_slots[:3]):
                state.ai_slot_present[faction][slot] = bool(present)
                any_present = any_present or bool(present)
            if any_present:
                state.faction_enables[faction] = True

        for faction, energy_slots in options.ai_slot_energy.items():
            faction = int(faction)
            if not 0 <= faction < len(state.ai_slot_energy):
                continue
            for slot, energy in enumerate(energy_slots[:3]):
                if energy:
                    state.ai_slot_energy[faction][slot] = max(1, int(energy))

        for faction, vehicle_id in options.ai_host_vehicle_id.items():
            faction = int(faction)
            if 0 <= faction < len(state.ai_host_vehicle_id):
                state.ai_host_vehicle_id[faction] = int(vehicle_id)

        for faction, vehicle_slots in options.ai_slot_host_vehicle_id.items():
            faction = int(faction)
            if not 0 <= faction < len(state.ai_slot_host_vehicle_id):
                continue
            for slot, vehicle_id in enumerate(vehicle_slots[:3]):
                if vehicle_id:
                    state.ai_slot_host_vehicle_id[faction][slot] = int(vehicle_id)

    @staticmethod
    def _has_custom_scenario(options: Generator1CustomOptions) -> bool:
        return bool(
            options.ai_slot_present
            or options.ai_slot_energy
            or options.player_energy is not None
            or options.superitem_flags is not None
            or options.random_superitems
        )

    def _apply_scenario(self, state: _State) -> None:
        state.faction_enables[FACTION_PLAYER] = True
        if state.scenario_category:
            self._apply_category(state)
            return

        if state.difficulty <= 2:
            state.min_width, state.max_width, state.min_height, state.max_height = 8, 10, 8, 10
            state.player_energy = 400000
            self._set_presence_slots(state, FACTION_SULGOGARS, 1)
            chances = (0.10, 0.0)
        elif state.difficulty <= 5:
            state.min_width, state.max_width, state.min_height, state.max_height = 10, 14, 10, 14
            state.player_energy = 500000
            for faction in (FACTION_SULGOGARS, FACTION_MYKONIANS, FACTION_TAERKASTEN):
                self._set_presence_slots(state, faction, 1)
            chances = (0.30, 0.10)
        elif state.difficulty <= 8:
            state.min_width, state.max_width, state.min_height, state.max_height = 12, 18, 12, 18
            state.player_energy = 600000
            for faction in (FACTION_SULGOGARS, FACTION_MYKONIANS, FACTION_TAERKASTEN, FACTION_BLACK_SECT, FACTION_GHORKOVS):
                self._set_presence_slots(state, faction, 1)
            chances = (0.50, 0.30)
        else:
            state.min_width, state.max_width, state.min_height, state.max_height = 14, 20, 14, 20
            state.player_energy = 800000
            for faction in (FACTION_SULGOGARS, FACTION_MYKONIANS, FACTION_TAERKASTEN, FACTION_BLACK_SECT, FACTION_GHORKOVS):
                self._set_presence_slots(state, faction, 1)
            chances = (0.70, 0.50)
        state.superitem_flags[0] = state.rng.rand_float() < chances[0]
        state.superitem_flags[1] = state.rng.rand_float() < chances[1]

    def _apply_category(self, state: _State) -> None:
        category = max(1, min(12, state.scenario_category))
        state.scenario_category = category
        state.faction_enables = [False] * 8
        state.faction_enables[FACTION_PLAYER] = True
        state.superitem_flags = [False, False]
        match category:
            case 1:
                self._set_presence_slots(state, FACTION_TUTOR, 3)
            case 2:
                self._set_presence_slots(state, FACTION_GHORKOVS, 1)
            case 3:
                self._set_presence_slots(state, FACTION_GHORKOVS, 1)
                self._set_presence_slots(state, FACTION_TAERKASTEN, 1)
            case 4:
                self._set_presence_slots(state, FACTION_GHORKOVS, 2)
                state.superitem_flags[0] = True
            case 5:
                self._set_presence_slots(state, FACTION_GHORKOVS, 1)
                self._set_presence_slots(state, FACTION_MYKONIANS, 1)
                state.superitem_flags[0] = True
            case 6:
                self._set_presence_slots(state, FACTION_GHORKOVS, 2)
                self._set_presence_slots(state, FACTION_BLACK_SECT, 1)
            case 7:
                for faction in (FACTION_SULGOGARS, FACTION_MYKONIANS, FACTION_TAERKASTEN, FACTION_GHORKOVS):
                    self._set_presence_slots(state, faction, 1)
            case 8:
                self._set_presence_slots(state, FACTION_SULGOGARS, 3)
            case 9:
                for faction in (FACTION_SULGOGARS, FACTION_BLACK_SECT, FACTION_MYKONIANS, FACTION_TAERKASTEN):
                    self._set_presence_slots(state, faction, 1)
                state.superitem_flags[0] = True
            case 10:
                self._set_presence_slots(state, FACTION_GHORKOVS, 2)
                for faction in (FACTION_SULGOGARS, FACTION_BLACK_SECT, FACTION_TAERKASTEN):
                    self._set_presence_slots(state, faction, 1)
                state.superitem_flags[0] = True
            case 11:
                for faction in (FACTION_GHORKOVS, FACTION_SULGOGARS, FACTION_MYKONIANS, FACTION_TAERKASTEN):
                    self._set_presence_slots(state, faction, 1)
                self._set_presence_slots(state, FACTION_BLACK_SECT, 2)
                state.superitem_flags = [True, True]
                state.win_movie = True
                state.lose_movie = True
            case 12:
                for faction in (FACTION_GHORKOVS, FACTION_SULGOGARS, FACTION_MYKONIANS, FACTION_TAERKASTEN):
                    self._set_presence_slots(state, faction, 1)
                state.force_player_base_model = True
        state.min_width, state.max_width, state.min_height, state.max_height = CATEGORY_DIM_RANGES[category]
        state.player_energy = int(CATEGORY_ENERGY_PARAMS[category]["player"])
        self._assign_slot_energies(state)
        if category in (2, 3, 4):
            state.ai_host_vehicle_id[FACTION_GHORKOVS] = 59
        elif category in (5, 6, 7, 10, 11, 12):
            state.ai_host_vehicle_id[FACTION_GHORKOVS] = 57

    @staticmethod
    def _set_presence_slots(state: _State, faction: int, count: int) -> None:
        state.faction_enables[faction] = True
        for slot in range(max(0, min(3, count))):
            state.ai_slot_present[faction][slot] = True

    def _assign_slot_energies(self, state: _State) -> None:
        params = CATEGORY_ENERGY_PARAMS.get(state.scenario_category, {})
        for faction in range(2, 8):
            if faction not in params:
                continue
            base_k, range_k, scale = params[faction]
            for slot in range(3):
                if state.ai_slot_present[faction][slot]:
                    state.ai_slot_energy[faction][slot] = scale * (state.rng.rand_mod(range_k) + base_k)

    def _choose_map_size(self, state: _State) -> None:
        state.width = state.rng.rand_range(state.min_width, state.max_width)
        state.height = state.rng.rand_range(state.min_height, state.max_height)

    def _generate_height_map(self, state: _State) -> None:
        rows = [[128 for _ in range(state.width)] for _ in range(state.height)]
        for x in range(1, state.width):
            rows[0][x] = max(4, min(247, rows[0][x - 1] + state.rng.rand_variation(4)))
        for y in range(1, state.height):
            rows[y][0] = max(4, min(247, rows[y - 1][0] + state.rng.rand_variation(4)))
        for y in range(1, state.height):
            for x in range(1, state.width):
                up = rows[y - 1][x]
                left = rows[y][x - 1]
                lo = min(up, left) + 4
                hi = max(up, left) - 4
                rows[y][x] = max(4, min(247, state.rng.rand_range(hi, lo)))
        state.maps["hgt"] = rows

    def _init_typ_map(self, state: _State) -> None:
        compat = tileset_compatibility()[state.tileset] if state.improved else set(TYP_MAP_INTERIOR_LOOKUP)
        candidates = [value for value in TYP_MAP_INTERIOR_LOOKUP if value in compat] or TYP_MAP_INTERIOR_LOOKUP
        rows = [[0 for _ in range(state.width)] for _ in range(state.height)]
        for y in range(1, state.height - 1):
            for x in range(1, state.width - 1):
                rows[y][x] = state.rng.choice(candidates)
        for x in range(state.width):
            rows[0][x] = TYP_BORDER_TOP
            rows[state.height - 1][x] = TYP_BORDER_BOTTOM
        for y in range(state.height):
            rows[y][0] = TYP_BORDER_LEFT
            rows[y][state.width - 1] = TYP_BORDER_RIGHT
        rows[0][0] = TYP_BORDER_TOP_LEFT
        rows[0][state.width - 1] = TYP_BORDER_TOP_RIGHT
        rows[state.height - 1][0] = TYP_BORDER_BOTTOM_LEFT
        rows[state.height - 1][state.width - 1] = TYP_BORDER_BOTTOM_RIGHT
        state.maps["typ"] = rows

    def _init_own_map(self, state: _State) -> None:
        owners = [0, FACTION_PLAYER] + [faction for faction in range(2, 8) if state.faction_enables[faction]]
        rows = [[0 for _ in range(state.width)] for _ in range(state.height)]
        for y in range(1, state.height - 1):
            for x in range(1, state.width - 1):
                rows[y][x] = state.rng.choice(owners)
        state.maps["own"] = rows

    def _place_player_base(self, state: _State) -> None:
        x = state.rng.rand_range(1, state.width - 2)
        y = state.rng.rand_range(1, state.height - 2)
        state.base_x, state.base_y = x, y
        state.set("typ", x, y, TYP_PLAYER_BASE)
        state.set("blg", x, y, BLG_PLAYER_BASE)
        state.set("own", x, y, FACTION_PLAYER)
        self._reserve_sector(state, x, y)

    def _place_hosts_and_ambient(self, state: _State) -> None:
        self._place_player_host(state)
        for faction in range(2, 8):
            for slot in range(3):
                if state.ai_slot_present[faction][slot]:
                    self._place_ai_host(state, faction, slot)
        density = 0.4 + min(0.6, state.difficulty * 0.06)
        attempts = int((state.width * state.height) * density / 18)
        for _ in range(max(1, min(10, attempts))):
            sector = self._find_empty_sector(state)
            if not sector:
                continue
            x, y = sector
            owner = self._pick_present_faction(state)
            candidates = BUILDINGS_BY_FACTION.get(owner) or BUILDINGS_BY_FACTION[FACTION_PLAYER]
            building = state.rng.choice(candidates)
            state.set("blg", x, y, building)
            state.set("typ", x, y, BUILDING_TYP_BY_ID.get(building, state.get("typ", x, y)))
            state.set("own", x, y, owner)
            self._reserve_sector(state, x, y)

    def _place_player_host(self, state: _State) -> None:
        x, y = self._find_empty_sector(state) or (state.base_x, state.base_y)
        state.player_host_x, state.player_host_y = x, y
        if state.force_player_base_model:
            building = 64
        else:
            building = state.rng.choice(HOST_BUILDING_BY_FACTION[FACTION_PLAYER])
        self._write_host_cell(state, x, y, FACTION_PLAYER, building)

    def _place_ai_host(self, state: _State, faction: int, slot: int) -> None:
        sector = self._find_empty_sector(state, avoid=(state.base_x, state.base_y))
        if not sector:
            return
        x, y = sector
        building = state.rng.choice(HOST_BUILDING_BY_FACTION.get(faction, [12]))
        self._write_host_cell(state, x, y, faction, building)
        state.ai_slot_world[faction][slot] = (sector_to_world_x(x), sector_to_world_z(y))

    def _write_host_cell(self, state: _State, x: int, y: int, owner: int, building: int) -> None:
        state.set("blg", x, y, building)
        state.set("typ", x, y, BUILDING_TYP_BY_ID.get(building, 201))
        state.set("own", x, y, owner)
        self._reserve_sector(state, x, y)

    def _find_empty_sector(self, state: _State, avoid: tuple[int, int] | None = None) -> tuple[int, int] | None:
        max_attempts = max(10, state.width_interior * state.height_interior * 3)
        for _ in range(max_attempts):
            x = state.rng.rand_range(1, state.width - 2)
            y = state.rng.rand_range(1, state.height - 2)
            if avoid and (x, y) == avoid:
                continue
            if self._sector_is_available(state, x, y):
                return x, y
        for y in range(1, state.height - 1):
            for x in range(1, state.width - 1):
                if (not avoid or (x, y) != avoid) and self._sector_is_available(state, x, y):
                    return x, y
        return None

    @staticmethod
    def _reserve_sector(state: _State, x: int, y: int) -> None:
        state.reserved_sectors.add((x, y))

    @staticmethod
    def _sector_is_available(state: _State, x: int, y: int) -> bool:
        return state.interior(x, y) and state.get("blg", x, y) == 0 and (x, y) not in state.reserved_sectors

    def _pick_present_faction(self, state: _State) -> int:
        factions = [FACTION_PLAYER] + [faction for faction in range(2, 8) if state.faction_enables[faction]]
        return state.rng.choice(factions)

    def _seed_superitems(self, state: _State) -> None:
        for index, enabled in enumerate(state.superitem_flags, start=1):
            if not enabled:
                continue
            sector = self._find_empty_sector(state)
            if not sector:
                continue
            x, y = sector
            state.set("typ", x, y, TYP_SUPERITEM)
            state.set("blg", x, y, BLG_SUPERITEM)
            self._reserve_sector(state, x, y)
            countdown = self._superitem_countdown(state, index)
            keys = self._superitem_keys(state, index)
            state.superitems.append({"x": x, "y": y, "countdown": countdown, "keys": keys})

    def _superitem_countdown(self, state: _State, index: int) -> int:
        if index in state.superitem_countdown_overrides:
            return state.superitem_countdown_overrides[index]
        if index == 1:
            value = state.rng.rand_mod(900) * 1000
            value = max(value, 180000)
            if state.difficulty > 5:
                value = max(value, 420000)
            return value
        value = state.rng.rand_mod(2700) * 1000
        value = max(value, 600000)
        if state.difficulty > 6:
            value = max(value, 1200000)
        return value

    def _superitem_keys(self, state: _State, item_index: int) -> list[tuple[int, int]]:
        if item_index == 2 and state.last_superitem_key_count:
            key_count = state.last_superitem_key_count
        else:
            key_count = min(16, self._normalize_superitem_key_count(1 + state.rng.rand_mod(63)))
            state.last_superitem_key_count = key_count
        keys: list[tuple[int, int]] = []
        attempts = max(key_count * 4, state.width_interior * state.height_interior)
        while len(keys) < key_count and attempts > 0:
            attempts -= 1
            sector = self._find_empty_sector(state)
            if not sector:
                break
            x, y = sector
            keys.append((x, y))
            self._mark_stoudson_key_sector(state, x, y)
            self._reserve_sector(state, x, y)
        return keys

    def _mark_stoudson_key_sector(self, state: _State, x: int, y: int) -> None:
        state.set("typ", x, y, TYP_GATE_CLOSED_1 if state.rng.rand_mod(2) else TYP_GATE_CLOSED_2)

    def _seed_beam_gate_keys(self, state: _State) -> None:
        if state.gate_keys:
            return
        key_count = self._gate_key_count(state)
        for _ in range(key_count):
            sector = self._find_empty_sector(state, avoid=(state.base_x, state.base_y))
            if not sector:
                break
            x, y = sector
            state.gate_keys.append((x, y))
            self._reserve_sector(state, x, y)

    def _gate_key_count(self, state: _State) -> int:
        if state.gate_key_count_override is not None:
            return min(state.width_interior * state.height_interior, state.gate_key_count_override)
        area = state.width_interior * state.height_interior
        if area < 17:
            return min(2, area)
        return min(16, self._normalize_superitem_key_count(1 + state.rng.rand_mod(63)))

    @staticmethod
    def _normalize_superitem_key_count(prelim: int) -> int:
        for limit, value in ((2, 15), (3, 14), (5, 13), (7, 12), (10, 11), (13, 10), (17, 9),
                             (21, 8), (26, 7), (31, 6), (37, 5), (44, 4), (52, 3)):
            if prelim <= limit:
                return value
        return 2

    def _repair_building_ownership(self, state: _State) -> None:
        for y in range(1, state.height - 1):
            for x in range(1, state.width - 1):
                if state.get("blg", x, y) and state.get("own", x, y) in (0, 7):
                    state.set("own", x, y, self._pick_present_faction(state))

    def _write_level(self, state: _State) -> str:
        writer = LDFWriter(property_style="tabs")
        self._write_header(writer, state)
        self._write_brief_maps(writer)
        self._seed_beam_gate_keys(state)
        self._write_beam_gate(writer, state)
        self._write_superitems(writer, state)
        self._write_robos(writer, state)
        self._write_include_and_enables(writer, state)
        self._write_tech_upgrades(writer, state)
        self._write_maps(writer, state)
        return writer.getvalue()

    def _write_header(self, writer: LDFWriter, state: _State) -> None:
        writer.line(";#*+ don't edit the magic runes")
        writer.line("")
        writer.line(";------------------------------------------------------------")
        writer.line(";--- Generated by Urban Assault Level Generator           ---")
        writer.line(";--- Generator: Generator1                                ---")
        writer.line(";------------------------------------------------------------")
        writer.line("begin_level")
        writer.property("set", state.tileset)
        writer.property("sky", f"objects/{state.rng.choice(SKY_OPTIONS)}")
        writer.property("slot0", "palette/standard.pal")
        writer.property("slot1", "palette/red.pal")
        writer.property("slot2", "palette/blau.pal")
        writer.property("slot3", "palette/gruen.pal")
        writer.property("slot4", "palette/inverse.pal")
        writer.property("slot5", "palette/invdark.pal")
        writer.property("slot6", "palette/sw.pal")
        writer.property("slot7", "palette/invtuerk.pal")
        if state.win_movie:
            writer.property("win_movie", "win.iff")
        if state.lose_movie:
            writer.property("lose_movie", "lose.iff")
        writer.end_block()
        writer.line("")

    def _write_brief_maps(self, writer: LDFWriter) -> None:
        writer.line("begin_mbmap")
        writer.property("name", "MB_02.IFF")
        writer.end_block()
        writer.line("")
        writer.line("begin_dbmap")
        writer.property("name", "DB_02.IFF")
        writer.end_block()
        writer.line("")

    def _write_beam_gate(self, writer: LDFWriter, state: _State) -> None:
        writer.line(";------------------------------------------------------------")
        writer.line(";--- Beam Gates                                           ---")
        writer.line(";------------------------------------------------------------")
        writer.line("begin_gate")
        writer.property("sec_x", state.base_x)
        writer.property("sec_y", state.base_y)
        writer.property("closed_bp", 5)
        writer.property("opened_bp", 6)
        writer.property("target_level", state.gate_target_level_id)
        for x, y in state.gate_keys:
            writer.property("keysec_x", x)
            writer.property("keysec_y", y)
        writer.property("mb_status", "unknown")
        writer.end_block()
        writer.line("")

    def _write_superitems(self, writer: LDFWriter, state: _State) -> None:
        writer.line(";------------------------------------------------------------")
        writer.line(";--- Superitems                                           ---")
        writer.line(";------------------------------------------------------------")
        for item in state.superitems:
            writer.line("begin_item")
            writer.property("sec_x", item["x"])
            writer.property("sec_y", item["y"])
            writer.property("inactive_bp", 35)
            writer.property("active_bp", 36)
            writer.property("trigger_bp", 36)
            writer.property("type", 1)
            writer.property("countdown", item["countdown"])
            for x, y in item["keys"]:
                writer.property("keysec_x", x)
                writer.property("keysec_y", y)
            writer.end_block()
            writer.line("")

    def _write_robos(self, writer: LDFWriter, state: _State) -> None:
        writer.line(";------------------------------------------------------------")
        writer.line(";--- Robo Definitions                                    ---")
        writer.line(";------------------------------------------------------------")
        writer.line("begin_robo")
        writer.property("owner", FACTION_PLAYER)
        writer.property("vehicle", HOST_VEHICLE_BY_FACTION[FACTION_PLAYER])
        writer.property("pos_x", sector_to_world_x(state.player_host_x))
        writer.property("pos_y", -330)
        writer.property("pos_z", sector_to_world_z(state.player_host_y))
        writer.property("energy", state.player_energy)
        writer.property("reload_const", 165625)
        writer.property("viewangle", 23)
        writer.end_block()
        writer.line("")
        for faction in range(2, 8):
            for slot in range(3):
                world = state.ai_slot_world[faction][slot]
                if world:
                    energy = state.ai_slot_energy[faction][slot] or self._default_ai_energy(state, faction)
                    self._write_ai_robo(writer, state, faction, slot, world[0], world[1], energy)

    def _write_ai_robo(
        self,
        writer: LDFWriter,
        state: _State,
        faction: int,
        slot: int,
        pos_x: int,
        pos_z: int,
        energy: int,
    ) -> None:
        vehicle = (
            state.ai_slot_host_vehicle_id[faction][slot]
            or state.ai_host_vehicle_id[faction]
            or HOST_VEHICLE_BY_FACTION.get(faction, 57)
        )
        writer.line("begin_robo")
        writer.property("owner", faction)
        writer.property("vehicle", vehicle)
        writer.property("pos_x", pos_x)
        writer.property("pos_y", -330)
        writer.property("pos_z", pos_z)
        writer.property("energy", energy)
        writer.property("reload_const", 600000)
        self._write_ai_budgets(writer, state, faction)
        writer.end_block()
        writer.line("")

    @staticmethod
    def _default_ai_energy(state: _State, faction: int) -> int:
        if faction == FACTION_TUTOR:
            return 200000
        return 300000 + state.difficulty * 50000

    def _write_ai_budgets(self, writer: LDFWriter, state: _State, faction: int) -> None:
        if faction == FACTION_TUTOR:
            values = {
                "con_budget": 70, "con_delay": 290000, "def_budget": 80, "def_delay": 200000,
                "rec_budget": 80, "rec_delay": 250000, "rob_budget": 80, "rob_delay": 300000,
                "pow_budget": 0, "pow_delay": 0, "rad_budget": 0, "rad_delay": 0,
                "saf_budget": 0, "saf_delay": 0, "cpl_budget": 0, "cpl_delay": 0,
            }
        elif state.difficulty >= 6:
            values = {
                "con_budget": 100, "con_delay": 0, "def_budget": 99, "def_delay": 0,
                "rec_budget": 90, "rec_delay": 0, "rob_budget": 85, "rob_delay": 0,
                "pow_budget": 20, "pow_delay": 0, "rad_budget": 20, "rad_delay": 0,
                "saf_budget": 20, "saf_delay": 0,
            }
        else:
            values = {
                "con_budget": 100, "con_delay": 200, "def_budget": 90, "def_delay": 100,
                "rec_budget": 85, "rec_delay": 50, "rob_budget": 95, "rob_delay": 100000,
                "pow_budget": 20, "pow_delay": 0, "rad_budget": 20, "rad_delay": 0,
                "saf_budget": 20, "saf_delay": 0, "cpl_budget": 80, "cpl_delay": 50000,
            }
        for key, value in values.items():
            writer.property(key, value)
        if faction != FACTION_TUTOR and state.difficulty >= 6:
            writer.property("cpl_delay", 95)
            writer.property("cpl_delay", 0)

    def _write_include_and_enables(self, writer: LDFWriter, state: _State) -> None:
        writer.line(";------------------------------------------------------------")
        writer.line(";--- Prototype Modifications                             ---")
        writer.line(";------------------------------------------------------------")
        writer.line("include data:scripts/startup2.scr")
        writer.line("")
        writer.line(";------------------------------------------------------------")
        writer.line(";--- Prototype Enabling                                   ---")
        writer.line(";------------------------------------------------------------")
        if state.emit_player_enablement:
            self._write_enable_block(writer, state, FACTION_PLAYER)
        for faction in range(2, 8):
            if any(state.ai_slot_world[faction]):
                self._write_enable_block(writer, state, faction)

    def _write_enable_block(self, writer: LDFWriter, state: _State, faction: int) -> None:
        vehicles, buildings = self._enabled_vehicles(state, faction), self._enabled_buildings(state, faction)
        if not vehicles and not buildings:
            return
        writer.line(f"begin_enable\t{faction}" if faction == FACTION_PLAYER else f"begin_enable {faction}")
        for vehicle in vehicles:
            writer.line(f"\tvehicle = {vehicle}")
        for building in buildings:
            writer.line(f"\tbuilding = {building}")
        writer.end_block()
        writer.line("")

    def _enabled_vehicles(self, state: _State, faction: int) -> list[int]:
        if faction in state.forced_enabled_vehicles:
            return list(state.forced_enabled_vehicles[faction])
        if faction == FACTION_PLAYER:
            enabled = [16, 9]
            self._record_vehicle_flags(state, enabled)
            for vehicle, probability in zip(VEHICLES_PLAYER_IDS, VEHICLES_PLAYER_PROBABILITIES, strict=True):
                if state.rng.rand_mod(probability) == 0 and vehicle not in enabled:
                    enabled.append(vehicle)
            self._record_vehicle_flags(state, enabled)
            return enabled
        if faction == FACTION_TUTOR:
            return [142]
        if faction == FACTION_SULGOGARS:
            enabled = [73]
            if state.rng.rand_mod(2) == 0:
                enabled.append(71)
            if state.rng.rand_mod(2) == 0:
                enabled.append(72)
            enabled.append(74)
            return enabled
        candidates = VEHICLES_BY_FACTION.get(faction, [])
        return [vehicle for vehicle in candidates if state.rng.rand_mod(3) == 0] or candidates[:1]

    def _enabled_buildings(self, state: _State, faction: int) -> list[int]:
        if faction in state.forced_enabled_buildings:
            return list(state.forced_enabled_buildings[faction])
        if faction == FACTION_PLAYER:
            enabled = [
                building for building, probability in zip(BUILDINGS_PLAYER_IDS, BUILDINGS_PLAYER_PROBABILITIES, strict=True)
                if state.rng.rand_mod(probability) == 0
            ]
            self._record_building_flags(state, enabled)
            return enabled
        if faction == FACTION_TUTOR:
            return []
        candidates = BUILDINGS_BY_FACTION.get(faction, [])
        return [building for building in candidates if state.rng.rand_mod(3) == 0] or candidates[:1]

    @staticmethod
    def _record_vehicle_flags(state: _State, vehicles: list[int]) -> None:
        for vehicle in vehicles:
            if vehicle in GENERATOR1_PLAYER_TECH_VEHICLE_IDS:
                state.player_vehicle_flags[GENERATOR1_PLAYER_TECH_VEHICLE_IDS.index(vehicle)] = True

    @staticmethod
    def _record_building_flags(state: _State, buildings: list[int]) -> None:
        for building in buildings:
            if building in GENERATOR1_PLAYER_TECH_BUILDING_IDS:
                state.player_building_flags[GENERATOR1_PLAYER_TECH_BUILDING_IDS.index(building)] = True

    def _write_tech_upgrades(self, writer: LDFWriter, state: _State) -> None:
        writer.line(";------------------------------------------------------------")
        writer.line(";--- Tech Up-Grades                                       ---")
        writer.line(";------------------------------------------------------------")
        if state.level_index in (3, 43):
            return
        free_cells = self._free_cells(state)
        if not free_cells:
            return
        count = 1 + state.rng.rand_mod(min(5, len(free_cells)))
        for _ in range(count):
            if not free_cells:
                break
            x, y = free_cells.pop(state.rng.rand_mod(len(free_cells)))
            self._write_tech_gem(writer, state, x, y)

    @staticmethod
    def _free_cells(state: _State) -> list[tuple[int, int]]:
        return [
            (x, y)
            for y in range(1, state.height - 1)
            for x in range(1, state.width - 1)
            if state.get("blg", x, y) == 0 and (x, y) not in state.reserved_sectors
        ]

    def _write_tech_gem(self, writer: LDFWriter, state: _State, x: int, y: int) -> None:
        family = state.rng.rand_mod(4)
        writer.line("begin_gem")
        writer.property("sec_x", x)
        writer.property("sec_y", y)
        writer.property("building", state.rng.choice([4, 7, 15, 16, 50, 51, 61, 65]))
        writer.property("type", 1)
        writer.line("begin_action")
        if family == 0:
            vehicle = self._choose_enabled_player_vehicle(state)
            writer.property("modify_vehicle", vehicle)
            writer.property("add_energy", 100 + state.rng.rand_mod(401))
        elif family == 1:
            vehicle = self._choose_enabled_player_vehicle(state)
            writer.property("modify_weapon", vehicle)
            writer.property("num_weapons", 1 + state.rng.rand_mod(3))
        elif family == 2:
            vehicle = self._unlock_next_vehicle(state)
            writer.property("modify_vehicle", vehicle)
            writer.property("enable", FACTION_PLAYER)
        else:
            building = self._unlock_next_building(state)
            writer.property("modify_building", building)
            writer.property("enable", FACTION_PLAYER)
        writer.line("end_action")
        writer.property("mb_status", "unknown")
        writer.end_block()
        writer.line("")

    def _choose_enabled_player_vehicle(self, state: _State) -> int:
        enabled = [
            vehicle for vehicle, flag in zip(GENERATOR1_PLAYER_TECH_VEHICLE_IDS, state.player_vehicle_flags, strict=True)
            if flag
        ]
        return state.rng.choice(enabled or [16])

    def _unlock_next_vehicle(self, state: _State) -> int:
        for i, flag in enumerate(state.player_vehicle_flags):
            if not flag:
                state.player_vehicle_flags[i] = True
                return GENERATOR1_PLAYER_TECH_VEHICLE_IDS[i]
        return self._choose_enabled_player_vehicle(state)

    def _unlock_next_building(self, state: _State) -> int:
        for i, flag in enumerate(state.player_building_flags):
            if not flag:
                state.player_building_flags[i] = True
                return GENERATOR1_PLAYER_TECH_BUILDING_IDS[i]
        return GENERATOR1_PLAYER_TECH_BUILDING_IDS[state.rng.rand_mod(len(GENERATOR1_PLAYER_TECH_BUILDING_IDS))]

    def _write_maps(self, writer: LDFWriter, state: _State) -> None:
        writer.line(";------------------------------------------------------------")
        writer.line(";--- Map Dumps                                            ---")
        writer.line(";------------------------------------------------------------")
        writer.line("begin_maps")
        for name in ("typ", "own", "hgt", "blg"):
            writer.map_block(f"{name}_map", state.maps[name], state.width, state.height)
        writer.end_block()
        writer.line(";------------------------------------------------------------")
        writer.line(";--- End Of File                                          ---")
        writer.line(";------------------------------------------------------------")


def _clamp_optional(value: int | None, minimum: int, maximum: int) -> int | None:
    if value is None:
        return None
    return max(minimum, min(maximum, int(value)))
