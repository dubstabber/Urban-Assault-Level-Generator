"""Packaged Urban Assault reference data."""

from __future__ import annotations

import json
from functools import cache
from importlib import resources
from typing import Any

UA_ORIGINAL_PROFILE = "original"
UA_METROPOLIS_DAWN_PROFILE = "metropolisDawn"


@cache
def load_json(name: str) -> dict[str, Any]:
    data_ref = resources.files(__name__).joinpath(name)
    return json.loads(data_ref.read_text(encoding="utf-8"))


@cache
def tileset_compatibility() -> dict[int, set[int]]:
    raw = load_json("UA_tileset_compat.json")["sets"]
    return {int(key): {int(value) for value in values} for key, values in raw.items()}


@cache
def ua_data() -> dict[str, Any]:
    return load_json("UAdata.json")


@cache
def gen3_corpus() -> dict[str, Any]:
    """Baked dataset of parsed original levels used by Generator3 (Remix)."""

    return load_json("gen3_corpus.json")


@cache
def ua_hoststations(profile: str = UA_ORIGINAL_PROFILE) -> dict[int, dict[str, Any]]:
    raw = ua_data()[profile]["hoststations"]
    return {int(data["owner"]): data for data in raw.values()}


@cache
def ua_faction_names(profile: str = UA_ORIGINAL_PROFILE) -> dict[int, str]:
    raw = ua_data()[profile]["hoststations"]
    return {int(data["owner"]): name for name, data in raw.items()}


@cache
def ua_faction_units(profile: str = UA_ORIGINAL_PROFILE) -> dict[int, list[int]]:
    return {
        owner: [int(unit["id"]) for unit in data.get("units", [])]
        for owner, data in ua_hoststations(profile).items()
    }


@cache
def ua_faction_buildings(profile: str = UA_ORIGINAL_PROFILE) -> dict[int, list[int]]:
    return {
        owner: [int(building["id"]) for building in data.get("buildings", [])]
        for owner, data in ua_hoststations(profile).items()
    }


@cache
def ua_faction_robo_ids(profile: str = UA_ORIGINAL_PROFILE) -> dict[int, list[int]]:
    return {
        owner: [int(robo["id"]) for robo in data.get("robos", [])]
        for owner, data in ua_hoststations(profile).items()
    }


@cache
def ua_faction_player_robo_ids(profile: str = UA_ORIGINAL_PROFILE) -> dict[int, list[int]]:
    result: dict[int, list[int]] = {}
    for owner, data in ua_hoststations(profile).items():
        ids: list[int] = []
        for robo in data.get("robos", []):
            ids.append(int(robo.get("player_id") or robo["id"]))
        result[owner] = ids
    return result


@cache
def ua_faction_robo_names(profile: str = UA_ORIGINAL_PROFILE) -> dict[int, dict[int, str]]:
    return {
        owner: {int(robo["id"]): str(robo["name"]) for robo in data.get("robos", [])}
        for owner, data in ua_hoststations(profile).items()
    }


@cache
def ua_unit_labels(profile: str = UA_ORIGINAL_PROFILE) -> dict[int, str]:
    labels: dict[int, str] = {}
    for data in ua_hoststations(profile).values():
        labels.update({int(unit["id"]): str(unit["name"]) for unit in data.get("units", [])})
        labels.update({int(robo["id"]): str(robo["name"]) for robo in data.get("robos", [])})
        for robo in data.get("robos", []):
            if robo.get("player_id"):
                labels[int(robo["player_id"])] = str(robo["name"])
    labels.update({int(unit["id"]): str(unit["name"]) for unit in ua_data()[profile]["other"].get("units", [])})
    return labels


@cache
def ua_building_labels(profile: str = UA_ORIGINAL_PROFILE) -> dict[int, str]:
    labels: dict[int, str] = {}
    for data in ua_hoststations(profile).values():
        labels.update({int(building["id"]): str(building["name"]) for building in data.get("buildings", [])})
    labels.update({int(building["id"]): str(building["name"]) for building in ua_data()[profile]["other"].get("buildings", [])})
    return labels


@cache
def ua_building_typ_map(profile: str = UA_ORIGINAL_PROFILE) -> dict[int, int]:
    result: dict[int, int] = {}
    for data in ua_hoststations(profile).values():
        result.update({
            int(building["id"]): int(building["typ_map"])
            for building in data.get("buildings", [])
            if "typ_map" in building
        })
    result.update({
        int(building["id"]): int(building["typ_map"])
        for building in ua_data()[profile]["other"].get("buildings", [])
        if "typ_map" in building
    })
    return result


@cache
def ua_mission_briefing_maps(profile: str = UA_ORIGINAL_PROFILE) -> list[str]:
    return [str(map_name) for map_name in ua_data()[profile].get("missionBriefingMaps", [])]


@cache
def ua_mission_debriefing_maps(profile: str = UA_ORIGINAL_PROFILE) -> list[str]:
    return [str(map_name) for map_name in ua_data()[profile].get("missionDebriefingMaps", [])]


@cache
def ua_level_ids(profile: str = UA_ORIGINAL_PROFILE) -> list[int]:
    return [int(level_id) for level_id in ua_data()[profile].get("levels", [])]
