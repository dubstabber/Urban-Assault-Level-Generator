"""Generator4 campaign-profile resolution."""

from __future__ import annotations

from ..campaign_profiles import CampaignProfile, ProfileRegistry, default_profile_registry
from ..data import UA_METROPOLIS_DAWN_PROFILE, UA_ORIGINAL_PROFILE

_GENERATOR = "generator4"
_SOURCE_BY_DATA_PROFILE = {
    UA_ORIGINAL_PROFILE: "vanilla",
    UA_METROPOLIS_DAWN_PROFILE: "metropolisDawn",
}


class Generator4ProfileResolver:
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
