"""Mutable Generator3 level context (shared by Remix and Synthesis modes)."""

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
    player_faction: int
    zero_enemy_radar_budgets: bool = False
    zero_enemy_station_delays: bool = False

    # Provenance (Remix populates skeleton; Synthesis populates synth_method).
    mode: str = "remix"
    skeleton: Skeleton | None = None
    skeleton_name: str = ""
    source: str = ""
    synth_method: str = ""
    title: str = ""

    # Filled by the builder.
    faction_remap: dict[int, int] = field(default_factory=dict)
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
