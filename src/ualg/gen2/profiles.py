"""Generator2 campaign profile selection."""

from __future__ import annotations

from .context import _Level
from ..constants import (
    GENERATOR1_MD_GHORKOV_PLAYER_ROBO_BY_LEVEL,
    GENERATOR2_CAMPAIGN_LEVEL_IDS,
    GENERATOR2_CAMPAIGN_PROFILES,
    GENERATOR2_MD_BUILDINGS,
    GENERATOR2_MD_CAMPAIGN_LEVEL_IDS_BY_PROFILE,
    GENERATOR2_MD_CAMPAIGN_TARGETS_BY_PROFILE,
    GENERATOR2_MD_PLAYER_ROBOS,
    GENERATOR2_MD_VEHICLES,
)
from ..data import UA_METROPOLIS_DAWN_PROFILE, ua_mission_briefing_maps


class Generator2ProfileMixin:
    @staticmethod
    def _normalize_campaign_profile(campaign_profile: str) -> str:
        profile = campaign_profile.strip().lower()
        if profile not in GENERATOR2_CAMPAIGN_PROFILES:
            choices = ", ".join(GENERATOR2_CAMPAIGN_PROFILES)
            raise ValueError(f"Unknown Generator2 campaign profile '{campaign_profile}'. Choose one of: {choices}.")
        return profile

    @staticmethod
    def _campaign_level_ids(campaign_profile: str) -> list[int]:
        if campaign_profile == "original":
            return list(GENERATOR2_CAMPAIGN_LEVEL_IDS)
        return list(GENERATOR2_MD_CAMPAIGN_LEVEL_IDS_BY_PROFILE[campaign_profile])

    @staticmethod
    def _apply_campaign_profile(level: _Level, campaign_profile: str) -> None:
        level.campaign_profile = campaign_profile
        if campaign_profile == "original":
            return
        level.player_faction = "gho" if campaign_profile == "md-ghorkov" else "tae"
        level.targets_by_level = {
            key: list(value)
            for key, value in GENERATOR2_MD_CAMPAIGN_TARGETS_BY_PROFILE[campaign_profile].items()
        }
        level.vehicles_by_faction = {faction: list(vehicles) for faction, vehicles in GENERATOR2_MD_VEHICLES.items()}
        level.buildings_by_faction = {faction: list(buildings) for faction, buildings in GENERATOR2_MD_BUILDINGS.items()}
        level.mission_briefing_map = Generator2ProfileMixin._mission_briefing_map_for_level(level.level_id)
        level.mission_debriefing_map = level.mission_briefing_map
        if level.player_faction == "gho":
            level.player_vehicle = GENERATOR1_MD_GHORKOV_PLAYER_ROBO_BY_LEVEL.get(level.level_id, 177)
        else:
            level.player_vehicle = GENERATOR2_MD_PLAYER_ROBOS["tae"][0]

    @staticmethod
    def _mission_briefing_map_for_level(level_id: int) -> str:
        maps = ua_mission_briefing_maps(UA_METROPOLIS_DAWN_PROFILE)
        expected = f"mb_{level_id:02d}.iff"
        for map_name in maps:
            if map_name.lower() == expected:
                return map_name.upper()
        return maps[level_id % len(maps)].upper()
