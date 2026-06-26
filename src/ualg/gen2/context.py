"""Mutable Generator2 level context."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..constants import (
    GENERATOR2_BUILDINGS,
    GENERATOR2_HOST_VEHICLES,
    GENERATOR2_LEVELS,
    GENERATOR2_VEHICLES,
)
from ..models import MapRows
from ..rng import MSVCRTRandom


@dataclass
class _Level:
    level_id: int
    rng: MSVCRTRandom
    seed: int
    campaign_profile: str = "original"
    mission_briefing_map: str = "MB_15.IFF"
    mission_debriefing_map: str = "DB_15.IFF"
    player_faction: str = "res"
    player_vehicle: int = 56
    width: int = 0
    height: int = 0
    tileset: int = 1
    targets_by_level: dict[int, list[int]] = field(
        default_factory=lambda: {key: list(value) for key, value in GENERATOR2_LEVELS.items()}
    )
    vehicles_by_faction: dict[str, list[int]] = field(
        default_factory=lambda: {faction: list(vehicles) for faction, vehicles in GENERATOR2_VEHICLES.items()}
    )
    buildings_by_faction: dict[str, list[int]] = field(
        default_factory=lambda: {faction: list(buildings) for faction, buildings in GENERATOR2_BUILDINGS.items()}
    )
    host_vehicles: dict[str, int] = field(default_factory=lambda: {"res": 56, **GENERATOR2_HOST_VEHICLES})
    gates: list[dict[str, Any]] = field(default_factory=list)
    bombs: list[dict[str, Any]] = field(default_factory=list)
    squads: list[dict[str, Any]] = field(default_factory=list)
    flaks: list[dict[str, Any]] = field(default_factory=list)
    powers: list[dict[str, Any]] = field(default_factory=list)
    excluded: list[dict[str, Any]] = field(default_factory=list)
    hosts: dict[str, list[dict[str, int]]] = field(default_factory=dict)
    maps: dict[str, MapRows] = field(default_factory=dict)
