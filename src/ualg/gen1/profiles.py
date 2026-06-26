"""Generator1 campaign profile selection."""

from __future__ import annotations

from .context import _State
from ..constants import (
    BUILDINGS_BY_FACTION,
    FACTION_GHORKOVS,
    FACTION_PLAYER,
    FACTION_TAERKASTEN,
    GENERATOR1_CAMPAIGN_FILENAMES,
    GENERATOR1_CAMPAIGN_PROFILES,
    GENERATOR1_MD_CAMPAIGN_LEVEL_IDS_BY_PROFILE,
    GENERATOR1_MD_GHORKOV_PLAYER_ROBO_BY_LEVEL,
    METROPOLIS_DAWN_BUILDINGS_BY_FACTION,
    METROPOLIS_DAWN_HOST_VEHICLE_BY_FACTION,
    METROPOLIS_DAWN_PLAYER_ROBOS_BY_FACTION,
    METROPOLIS_DAWN_VEHICLES_BY_FACTION,
    VEHICLES_BY_FACTION,
)
from ..data import UA_METROPOLIS_DAWN_PROFILE, ua_mission_briefing_maps


class Generator1ProfileMixin:
    @staticmethod
    def _normalize_campaign_profile(campaign_profile: str) -> str:
        profile = campaign_profile.strip().lower()
        if profile not in GENERATOR1_CAMPAIGN_PROFILES:
            choices = ", ".join(GENERATOR1_CAMPAIGN_PROFILES)
            raise ValueError(f"Unknown Generator1 campaign profile '{campaign_profile}'. Choose one of: {choices}.")
        return profile

    @staticmethod
    def _campaign_filenames(campaign_profile: str) -> tuple[str, ...]:
        if campaign_profile == "original":
            return tuple(GENERATOR1_CAMPAIGN_FILENAMES)
        return tuple(f"L{level_id:02d}{level_id:02d}.ldf" for level_id in GENERATOR1_MD_CAMPAIGN_LEVEL_IDS_BY_PROFILE[campaign_profile])

    @staticmethod
    def _profile_player_faction(campaign_profile: str) -> int:
        if campaign_profile == "md-ghorkov":
            return FACTION_GHORKOVS
        if campaign_profile == "md-taerkasten":
            return FACTION_TAERKASTEN
        return FACTION_PLAYER

    @staticmethod
    def _profile_vehicles(campaign_profile: str) -> dict[int, list[int]]:
        source = METROPOLIS_DAWN_VEHICLES_BY_FACTION if campaign_profile.startswith("md-") else VEHICLES_BY_FACTION
        return {faction: list(vehicles) for faction, vehicles in source.items()}

    @staticmethod
    def _profile_buildings(campaign_profile: str) -> dict[int, list[int]]:
        source = METROPOLIS_DAWN_BUILDINGS_BY_FACTION if campaign_profile.startswith("md-") else BUILDINGS_BY_FACTION
        return {faction: list(buildings) for faction, buildings in source.items()}

    def _player_tech_vehicle_ids(self, campaign_profile: str) -> list[int]:
        player_faction = self._profile_player_faction(campaign_profile)
        vehicles = self._profile_vehicles(campaign_profile).get(player_faction, [])
        if player_faction == FACTION_PLAYER:
            return [vehicle for vehicle in vehicles if vehicle != 9]
        return list(vehicles)

    def _player_tech_building_ids(self, campaign_profile: str) -> list[int]:
        player_faction = self._profile_player_faction(campaign_profile)
        return list(self._profile_buildings(campaign_profile).get(player_faction, []))

    def _apply_campaign_profile(self, state: _State, campaign_profile: str) -> None:
        state.campaign_profile = campaign_profile
        state.player_faction = self._profile_player_faction(campaign_profile)
        state.vehicles_by_faction = self._profile_vehicles(campaign_profile)
        state.buildings_by_faction = self._profile_buildings(campaign_profile)
        if campaign_profile.startswith("md-"):
            state.host_vehicle_by_faction = dict(METROPOLIS_DAWN_HOST_VEHICLE_BY_FACTION)
            state.mission_briefing_map = self._mission_briefing_map_for_level(state.level_id)
            state.mission_debriefing_map = state.mission_briefing_map

    @staticmethod
    def _mission_briefing_map_for_level(level_id: int) -> str:
        maps = ua_mission_briefing_maps(UA_METROPOLIS_DAWN_PROFILE)
        expected = f"mb_{level_id:02d}.iff"
        for map_name in maps:
            if map_name.lower() == expected:
                return map_name.upper()
        return maps[level_id % len(maps)].upper()

    @staticmethod
    def _assign_player_host_vehicle(state: _State) -> None:
        if not state.campaign_profile.startswith("md-"):
            return
        robos = METROPOLIS_DAWN_PLAYER_ROBOS_BY_FACTION.get(state.player_faction, [])
        if not robos:
            return
        if state.player_faction == FACTION_GHORKOVS and len(robos) > 1:
            state.player_host_vehicle_id = GENERATOR1_MD_GHORKOV_PLAYER_ROBO_BY_LEVEL.get(state.level_id, robos[1])
        else:
            state.player_host_vehicle_id = robos[0]
