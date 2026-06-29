"""Mutable Generator4 level context."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..campaign_profiles import CampaignProfile
from ..models import MapRows
from ..rng import MSVCRTRandom
from .rules import Archetype


@dataclass
class _Gen4Level:
    level_id: int
    rng: MSVCRTRandom
    seed: int
    profile_id: str
    profile: CampaignProfile
    player_faction: int
    archetype: Archetype
    zero_enemy_radar_budgets: bool = False
    zero_enemy_station_delays: bool = False

    mode: str = "hybrid-synthesis"
    source: str = ""
    synth_method: str = ""
    title: str = ""
    tileset: int = 1
    width: int = 0
    height: int = 0
    sky: str = ""
    mission_briefing_map: str = ""
    mission_debriefing_map: str = ""
    mbmap_block: dict[str, Any] = field(default_factory=dict)
    dbmap_block: dict[str, Any] = field(default_factory=dict)
    header: dict[str, Any] = field(default_factory=dict)
    maps: dict[str, MapRows] = field(default_factory=dict)
    gates: list[dict[str, Any]] = field(default_factory=list)
    robos: list[dict[str, Any]] = field(default_factory=list)
    squads: list[dict[str, Any]] = field(default_factory=list)
    items: list[dict[str, Any]] = field(default_factory=list)
    gems: list[list[str]] = field(default_factory=list)
    enables: list[dict[str, Any]] = field(default_factory=list)
    prototype: list[str] = field(default_factory=list)
    required_route_cells: list[tuple[int, int]] = field(default_factory=list)
    legal_vehicles_by_owner: dict[int, set[int]] = field(default_factory=dict)
    tech_phase: dict[str, Any] = field(default_factory=dict)
    infrastructure: list[dict[str, Any]] = field(default_factory=list)
    terrain_profile: dict[str, Any] = field(default_factory=dict)
    infrastructure_profile: dict[str, Any] = field(default_factory=dict)
