"""Generator2 campaign profile resolution."""

from __future__ import annotations

from .context import _Level
from ..campaign_profiles import CampaignProfile, ProfileRegistry, default_profile_registry


class Generator2ProfileResolver:
    def __init__(self, registry: ProfileRegistry | None = None) -> None:
        self._registry = registry or default_profile_registry()

    def normalize_campaign_profile(self, campaign_profile: str) -> str:
        return self.profile(campaign_profile).profile_id

    def profile(self, campaign_profile: str) -> CampaignProfile:
        return self._registry.get("generator2", campaign_profile)

    def campaign_level_ids(self, campaign_profile: str) -> list[int]:
        return list(self.profile(campaign_profile).level_ids)

    def original_level_ids(self) -> set[int]:
        return set(self.profile("original").level_ids)

    def apply_campaign_profile(self, level: _Level, campaign_profile: str) -> None:
        profile = self.profile(campaign_profile)
        level.campaign_profile = profile.profile_id
        level.player_faction = str(profile.player_faction)
        level.targets_by_level = {
            level_id: list(targets)
            for level_id, targets in profile.targets_by_level.items()
        }
        level.vehicles_by_faction = {
            str(faction): list(vehicles)
            for faction, vehicles in profile.roster.vehicles_by_faction.items()
        }
        level.buildings_by_faction = {
            str(faction): list(buildings)
            for faction, buildings in profile.roster.buildings_by_faction.items()
        }
        level.host_vehicles = {
            str(faction): int(vehicle)
            for faction, vehicle in profile.roster.host_vehicle_by_faction.items()
        }
        level.enemy_factions = list(profile.enemy_factions)
        level.mission_briefing_map = profile.mission_briefing_map_for_level(level.level_id)
        level.mission_debriefing_map = profile.mission_debriefing_map_for_level(level.level_id)
        level.player_vehicle = self._player_vehicle_for_level(profile, level.level_id)

    @staticmethod
    def _player_vehicle_for_level(profile: CampaignProfile, level_id: int) -> int:
        if profile.player_vehicle:
            return profile.player_vehicle
        robos = list(profile.roster.player_robo_ids_by_faction.get(profile.player_faction, ()))
        if profile.player_robo_by_level:
            fallback = robos[1] if len(robos) > 1 else robos[0] if robos else 56
            return profile.player_robo_by_level.get(level_id, fallback)
        if robos:
            return robos[0]
        return 56
