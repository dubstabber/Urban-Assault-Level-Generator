"""Mutable Generator1 level context and input options."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..core.maps import set_cell
from ..constants import (
    BUILDINGS_BY_FACTION,
    FACTION_PLAYER,
    GENERATOR1_PLAYER_TECH_BUILDING_IDS,
    GENERATOR1_PLAYER_TECH_VEHICLE_IDS,
    HOST_VEHICLE_BY_FACTION,
    VEHICLES_BY_FACTION,
)
from ..models import MapRows
from ..rng import MSVCRTRandom


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
    campaign_profile: str = "original"
    mission_briefing_map: str = "MB_02.IFF"
    mission_debriefing_map: str = "DB_02.IFF"
    player_faction: int = FACTION_PLAYER
    generator1_campaign_mode: bool = False
    emit_player_enablement: bool = True
    gate_target_level_id: int = 0
    gate_target_level_ids: list[int] = field(default_factory=list)
    min_width: int = 8
    max_width: int = 20
    min_height: int = 8
    max_height: int = 20
    width: int = 0
    height: int = 0
    tileset: int = 1
    player_energy: int = 500000
    player_host_vehicle_id: int = 0
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
    player_tech_vehicle_ids: list[int] = field(default_factory=lambda: list(GENERATOR1_PLAYER_TECH_VEHICLE_IDS))
    player_tech_building_ids: list[int] = field(default_factory=lambda: list(GENERATOR1_PLAYER_TECH_BUILDING_IDS))
    player_vehicle_flags: list[bool] = field(default_factory=lambda: [False] * len(GENERATOR1_PLAYER_TECH_VEHICLE_IDS))
    player_building_flags: list[bool] = field(default_factory=lambda: [False] * len(GENERATOR1_PLAYER_TECH_BUILDING_IDS))
    vehicles_by_faction: dict[int, list[int]] = field(
        default_factory=lambda: {faction: list(vehicles) for faction, vehicles in VEHICLES_BY_FACTION.items()}
    )
    buildings_by_faction: dict[int, list[int]] = field(
        default_factory=lambda: {faction: list(buildings) for faction, buildings in BUILDINGS_BY_FACTION.items()}
    )
    host_vehicle_by_faction: dict[int, int] = field(default_factory=lambda: dict(HOST_VEHICLE_BY_FACTION))
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
        set_cell(self.maps[map_name], x, y, value)
