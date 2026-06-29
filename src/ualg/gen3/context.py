"""Mutable Generator3 level context."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..campaign_profiles import CampaignProfile
from ..models import MapRows
from ..rng import MSVCRTRandom
from .corpus import Skeleton


@dataclass
class _Gen3Level:
    level_id: int
    rng: MSVCRTRandom
    seed: int
    profile_id: str
    profile: CampaignProfile
    skeleton: Skeleton
    player_faction: int
    zero_enemy_radar_budgets: bool = False
    zero_enemy_station_delays: bool = False

    # Filled by the remix builder.
    faction_remap: dict[int, int] = field(default_factory=dict)
    tileset: int = 1
    width: int = 0
    height: int = 0
    sky: str = ""
    mission_briefing_map: str = ""
    mission_debriefing_map: str = ""
    header: dict[str, Any] = field(default_factory=dict)
    maps: dict[str, MapRows] = field(default_factory=dict)
    gates: list[dict[str, Any]] = field(default_factory=list)
    robos: list[dict[str, Any]] = field(default_factory=list)
    squads: list[dict[str, Any]] = field(default_factory=list)
    items: list[dict[str, Any]] = field(default_factory=list)
    gems: list[list[str]] = field(default_factory=list)
    enables: list[dict[str, Any]] = field(default_factory=list)
    prototype: list[str] = field(default_factory=list)
