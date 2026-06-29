"""Profile slot data shared by Generator4 rule building and runtime code."""

from __future__ import annotations

from ..campaign_profiles import default_profile_registry

_GENERATOR = "generator3"


def level_ids_for(profile_id: str) -> tuple[int, ...]:
    return default_profile_registry().get(_GENERATOR, profile_id).level_ids


def targets_for(profile_id: str, level_id: int) -> tuple[int, ...]:
    return default_profile_registry().get(_GENERATOR, profile_id).targets_by_level.get(level_id, ())
