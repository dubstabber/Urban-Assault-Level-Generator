"""Startup script include selection for generated campaign levels."""

from __future__ import annotations


DEFAULT_STARTUP_INCLUDE = "include data:scripts/startup2.scr"
MD_FIRST_LEVEL_STARTUP_INCLUDE = "include script:startup.scr"
MD_GHORKOV_STARTUP_INCLUDE = "include script:startupG.scr"
MD_TAERKASTEN_STARTUP_INCLUDE = "include script:startupT.scr"

_MD_FIRST_LEVEL_IDS_BY_PROFILE = {
    "md-ghorkov": 7,
    "md-taerkasten": 6,
}

_MD_STARTUP_INCLUDES_BY_PROFILE = {
    "md-ghorkov": MD_GHORKOV_STARTUP_INCLUDE,
    "md-taerkasten": MD_TAERKASTEN_STARTUP_INCLUDE,
}


def startup_include_for_level(campaign_profile: str, level_id: int) -> str:
    profile = campaign_profile.strip().lower()
    if profile not in _MD_STARTUP_INCLUDES_BY_PROFILE:
        return DEFAULT_STARTUP_INCLUDE
    if level_id == _MD_FIRST_LEVEL_IDS_BY_PROFILE[profile]:
        return MD_FIRST_LEVEL_STARTUP_INCLUDE
    return _MD_STARTUP_INCLUDES_BY_PROFILE[profile]
