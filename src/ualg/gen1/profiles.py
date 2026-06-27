"""Generator1 campaign profile resolution."""

from __future__ import annotations

from .context import _State
from ..campaign_profiles import CampaignProfile, ProfileRegistry, default_profile_registry


_RESISTANCE_CAMPAIGN_TECH_EXCLUDED_VEHICLES = {9, 11, 133, 134}
_MD_TAERKASTEN_CAMPAIGN_TECH_EXCLUDED_VEHICLES = {143, 144}


class Generator1ProfileResolver:
    def __init__(self, registry: ProfileRegistry | None = None) -> None:
        self._registry = registry or default_profile_registry()

    def normalize_campaign_profile(self, campaign_profile: str) -> str:
        return self.profile(campaign_profile).profile_id

    def profile(self, campaign_profile: str) -> CampaignProfile:
        return self._registry.get("generator1", campaign_profile)

    def campaign_filenames(self, campaign_profile: str) -> tuple[str, ...]:
        return self.profile(campaign_profile).filenames

    def campaign_targets(self, campaign_profile: str, level_id: int) -> list[int]:
        return list(self.profile(campaign_profile).targets_by_level.get(level_id, ()))

    def player_tech_vehicle_ids(self, campaign_profile: str) -> list[int]:
        profile = self.profile(campaign_profile)
        vehicles = list(profile.roster.vehicles_by_faction.get(profile.player_faction, ()))
        if profile.player_faction == 1:
            return [vehicle for vehicle in vehicles if vehicle not in _RESISTANCE_CAMPAIGN_TECH_EXCLUDED_VEHICLES]
        if profile.profile_id == "md-taerkasten" and profile.player_faction == 4:
            return [vehicle for vehicle in vehicles if vehicle not in _MD_TAERKASTEN_CAMPAIGN_TECH_EXCLUDED_VEHICLES]
        return vehicles

    def player_tech_building_ids(self, campaign_profile: str) -> list[int]:
        profile = self.profile(campaign_profile)
        return list(profile.roster.buildings_by_faction.get(profile.player_faction, ()))

    def apply_campaign_profile(self, state: _State, campaign_profile: str) -> None:
        profile = self.profile(campaign_profile)
        state.campaign_profile = profile.profile_id
        state.player_faction = int(profile.player_faction)
        state.vehicles_by_faction = {
            int(faction): list(vehicles)
            for faction, vehicles in profile.roster.vehicles_by_faction.items()
        }
        state.buildings_by_faction = {
            int(faction): list(buildings)
            for faction, buildings in profile.roster.buildings_by_faction.items()
        }
        state.host_vehicle_by_faction = {
            int(faction): int(vehicle)
            for faction, vehicle in profile.roster.host_vehicle_by_faction.items()
        }
        state.mission_briefing_map = profile.mission_briefing_map_for_level(state.level_id)
        state.mission_debriefing_map = profile.mission_debriefing_map_for_level(state.level_id)

    def assign_player_host_vehicle(self, state: _State) -> None:
        profile = self.profile(state.campaign_profile)
        if profile.profile_id == "original":
            return
        robos = list(profile.roster.player_robo_ids_by_faction.get(state.player_faction, ()))
        if not robos:
            return
        if profile.player_robo_by_level:
            fallback = robos[1] if len(robos) > 1 else robos[0]
            state.player_host_vehicle_id = profile.player_robo_by_level.get(state.level_id, fallback)
            return
        state.player_host_vehicle_id = robos[0]
