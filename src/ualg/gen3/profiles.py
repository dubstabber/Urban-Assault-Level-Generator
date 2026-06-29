"""Generator3 campaign-profile resolution."""

from __future__ import annotations

from ..campaign_profiles import CampaignProfile, ProfileRegistry, default_profile_registry
from ..data import UA_METROPOLIS_DAWN_PROFILE, UA_ORIGINAL_PROFILE

_GENERATOR = "generator3"

# Map a profile's data_profile to the corpus source it draws skeletons from.
_SOURCE_BY_DATA_PROFILE = {
    UA_ORIGINAL_PROFILE: "vanilla",
    UA_METROPOLIS_DAWN_PROFILE: "metropolisDawn",
}

# Owners that are never enemy factions in a remix.
_NON_ENEMY_OWNERS = {0, 7}


class Generator3ProfileResolver:
    def __init__(self, profile_registry: ProfileRegistry | None = None) -> None:
        self._registry = profile_registry or default_profile_registry()

    def names(self) -> tuple[str, ...]:
        return self._registry.names(_GENERATOR)

    def normalize_campaign_profile(self, name: str) -> str:
        normalized = (name or "original").strip().lower()
        self._registry.get(_GENERATOR, normalized)
        return normalized

    def get(self, name: str) -> CampaignProfile:
        return self._registry.get(_GENERATOR, name)

    def source_for(self, profile: CampaignProfile) -> str:
        return _SOURCE_BY_DATA_PROFILE.get(profile.data_profile, "vanilla")

    def enemy_factions(self, profile: CampaignProfile) -> list[int]:
        """Numeric enemy factions a remix can assign, ordered deterministically."""

        player = int(profile.player_faction)
        roster = profile.roster
        return [
            faction
            for faction in sorted(roster.host_vehicle_by_faction)
            if faction != player
            and faction not in _NON_ENEMY_OWNERS
            and roster.vehicles_by_faction.get(faction)
        ]
