"""Typed campaign profile registry for generator backends."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .data import (
    UA_ORIGINAL_PROFILE,
    load_json,
    ua_faction_buildings,
    ua_faction_player_robo_ids,
    ua_faction_robo_ids,
    ua_faction_units,
    ua_mission_briefing_maps,
    ua_mission_debriefing_maps,
)

_FACTION_PLAYER = 1
_FACTION_SULGOGARS = 2
_FACTION_MYKONIANS = 3
_FACTION_TAERKASTEN = 4
_FACTION_BLACK_SECT = 5
_FACTION_GHORKOVS = 6
_FACTION_TUTOR = 7
_ROCK_SLED_VEHICLE_ID = 11
_GENERATOR2_ROCK_SLED_EXCLUDED_FACTIONS = {"res", "bla", _FACTION_PLAYER, _FACTION_BLACK_SECT}

GENERATOR2_FACTION_IDS = {"res": 1, "sul": 2, "myk": 3, "tae": 4, "bla": 5, "gho": 6}
GENERATOR2_FACTION_CODES_BY_ID = {faction_id: code for code, faction_id in GENERATOR2_FACTION_IDS.items()}


@dataclass(frozen=True, slots=True)
class ProfileRoster:
    vehicles_by_faction: dict[Any, tuple[int, ...]]
    buildings_by_faction: dict[Any, tuple[int, ...]]
    host_vehicle_by_faction: dict[Any, int]
    player_robo_ids_by_faction: dict[Any, tuple[int, ...]]


@dataclass(frozen=True, slots=True)
class CampaignProfile:
    generator: str
    profile_id: str
    data_profile: str
    mission_map_profile: str | None
    mission_debriefing_uses_briefing: bool
    mission_briefing_default: str
    mission_debriefing_default: str
    player_faction: int | str
    player_vehicle: int
    level_ids: tuple[int, ...]
    filenames: tuple[str, ...]
    targets_by_level: dict[int, tuple[int, ...]]
    roster: ProfileRoster
    player_robo_by_level: dict[int, int]
    enemy_factions: tuple[str, ...] = ()

    def mission_briefing_map_for_level(self, level_id: int) -> str:
        return _mission_map_for_level(self.mission_map_profile, level_id, self.mission_briefing_default, briefing=True)

    def mission_debriefing_map_for_level(self, level_id: int) -> str:
        if self.mission_debriefing_uses_briefing:
            return self.mission_briefing_map_for_level(level_id)
        return _mission_map_for_level(
            self.mission_map_profile,
            level_id,
            self.mission_debriefing_default,
            briefing=False,
        )


class ProfileRegistry:
    """Resolves generator campaign profiles from validated package data."""

    def __init__(self, profiles_by_generator: dict[str, dict[str, CampaignProfile]]) -> None:
        self._profiles_by_generator = profiles_by_generator

    @classmethod
    def from_package(cls) -> ProfileRegistry:
        return cls.from_mapping(load_json("campaign_profiles.json"))

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> ProfileRegistry:
        if data.get("version") != 1:
            raise ValueError("Unsupported campaign profile data version.")
        generators = data.get("generators")
        if not isinstance(generators, dict):
            raise ValueError("Campaign profile data must contain a generators mapping.")

        profiles_by_generator: dict[str, dict[str, CampaignProfile]] = {}
        for generator, raw_profiles in generators.items():
            if generator not in {"generator1", "generator2", "generator3", "generator4"}:
                raise ValueError(f"Unsupported campaign profile generator: {generator!r}.")
            if not isinstance(raw_profiles, dict) or not raw_profiles:
                raise ValueError(f"Generator {generator!r} must define at least one profile.")
            profiles_by_generator[generator] = {
                profile_id: _build_profile(generator, profile_id, spec)
                for profile_id, spec in raw_profiles.items()
            }
        return cls(profiles_by_generator)

    def names(self, generator: str) -> tuple[str, ...]:
        return tuple(self._profiles_by_generator.get(generator, ()))

    def get(self, generator: str, profile_id: str) -> CampaignProfile:
        profile_id = profile_id.strip().lower()
        profiles = self._profiles_by_generator.get(generator)
        if profiles is None:
            raise ValueError(f"Unknown generator profile namespace: {generator!r}.")
        try:
            return profiles[profile_id]
        except KeyError as exc:
            choices = ", ".join(profiles)
            raise ValueError(f"Unknown {generator} campaign profile '{profile_id}'. Choose one of: {choices}.") from exc


def default_profile_registry() -> ProfileRegistry:
    return _DEFAULT_PROFILE_REGISTRY


def _build_profile(generator: str, profile_id: str, spec: dict[str, Any]) -> CampaignProfile:
    if not isinstance(spec, dict):
        raise ValueError(f"Profile {generator}/{profile_id} must be a mapping.")

    filenames = tuple(str(filename) for filename in spec.get("level_filenames", ()))
    level_ids = tuple(int(level_id) for level_id in spec.get("level_ids", ()))
    if not level_ids and filenames:
        level_ids = tuple(_level_id_from_filename(filename) for filename in filenames)
    if not filenames and level_ids:
        filenames = tuple(_level_filename(level_id) for level_id in level_ids)
    if not level_ids or not filenames:
        raise ValueError(f"Profile {generator}/{profile_id} must define level_ids or level_filenames.")

    data_profile = str(spec.get("data_profile", UA_ORIGINAL_PROFILE))
    roster_profile = str(spec.get("roster_profile", data_profile))
    numeric_faction_generators = {"generator1", "generator3", "generator4"}
    roster = (
        _build_generator1_roster(roster_profile)
        if generator in numeric_faction_generators
        else _build_generator2_roster(spec, roster_profile)
    )
    player_faction = spec.get("player_faction")
    if player_faction is None:
        raise ValueError(f"Profile {generator}/{profile_id} must define player_faction.")
    roster = _apply_roster_exceptions(generator, roster)
    targets_by_level = _targets_by_level(spec, level_ids)
    player_vehicle = int(spec.get("player_vehicle", 0))
    player_robo_by_level = {int(level_id): int(vehicle) for level_id, vehicle in spec.get("player_robo_by_level", {}).items()}
    enemy_factions = _enemy_factions(generator, spec, player_faction)

    return CampaignProfile(
        generator=generator,
        profile_id=profile_id,
        data_profile=data_profile,
        mission_map_profile=spec.get("mission_map_profile"),
        mission_debriefing_uses_briefing=bool(spec.get("mission_debriefing_uses_briefing", False)),
        mission_briefing_default=str(spec.get("mission_briefing_default", "")),
        mission_debriefing_default=str(spec.get("mission_debriefing_default", "")),
        player_faction=int(player_faction) if generator in numeric_faction_generators else str(player_faction),
        player_vehicle=player_vehicle,
        level_ids=level_ids,
        filenames=filenames,
        targets_by_level=targets_by_level,
        roster=roster,
        player_robo_by_level=player_robo_by_level,
        enemy_factions=enemy_factions,
    )


def _targets_by_level(spec: dict[str, Any], level_ids: tuple[int, ...]) -> dict[int, tuple[int, ...]]:
    target_mode = spec.get("target_mode")
    if target_mode == "next":
        return {
            level_id: ((level_ids[index + 1],) if index + 1 < len(level_ids) else (0,))
            for index, level_id in enumerate(level_ids)
        }
    raw_targets = spec.get("targets_by_level", {})
    return {
        int(level_id): tuple(int(target) for target in targets)
        for level_id, targets in raw_targets.items()
    }


def _build_generator1_roster(profile: str) -> ProfileRoster:
    vehicles = _with_black_sect_mixed_units(ua_faction_units(profile))
    buildings = _with_black_sect_mixed_buildings(ua_faction_buildings(profile))
    return ProfileRoster(
        vehicles_by_faction=_tuple_values(vehicles),
        buildings_by_faction=_tuple_values(buildings),
        host_vehicle_by_faction=_default_robo_ids(ua_faction_robo_ids(profile)),
        player_robo_ids_by_faction=_tuple_values(ua_faction_player_robo_ids(profile)),
    )


def _build_generator2_roster(spec: dict[str, Any], profile: str) -> ProfileRoster:
    if "vehicles_by_faction" in spec:
        return ProfileRoster(
            vehicles_by_faction=_tuple_values(spec["vehicles_by_faction"]),
            buildings_by_faction=_tuple_values(spec.get("buildings_by_faction", {})),
            host_vehicle_by_faction={str(faction): int(vehicle) for faction, vehicle in spec.get("host_vehicles", {}).items()},
            player_robo_ids_by_faction={},
        )

    vehicles = _int_faction_roster_to_codes(_with_black_sect_mixed_units(ua_faction_units(profile)))
    buildings = _int_faction_roster_to_codes(_with_black_sect_mixed_buildings(ua_faction_buildings(profile)))
    host_vehicles = _int_faction_values_to_codes(_default_robo_ids(ua_faction_robo_ids(profile)))
    player_robos = _int_faction_roster_to_codes(ua_faction_player_robo_ids(profile))
    return ProfileRoster(
        vehicles_by_faction=_tuple_values(vehicles),
        buildings_by_faction=_tuple_values(buildings),
        host_vehicle_by_faction=host_vehicles,
        player_robo_ids_by_faction=_tuple_values(player_robos),
    )


def _apply_roster_exceptions(generator: str, roster: ProfileRoster) -> ProfileRoster:
    if generator != "generator2":
        return roster

    excluded = set(_GENERATOR2_ROCK_SLED_EXCLUDED_FACTIONS)
    if not excluded:
        return roster

    vehicles = {
        faction: tuple(vehicle for vehicle in faction_vehicles if vehicle != _ROCK_SLED_VEHICLE_ID)
        if faction in excluded else faction_vehicles
        for faction, faction_vehicles in roster.vehicles_by_faction.items()
    }
    return ProfileRoster(
        vehicles_by_faction=vehicles,
        buildings_by_faction=roster.buildings_by_faction,
        host_vehicle_by_faction=roster.host_vehicle_by_faction,
        player_robo_ids_by_faction=roster.player_robo_ids_by_faction,
    )


def _enemy_factions(generator: str, spec: dict[str, Any], player_faction: Any) -> tuple[str, ...]:
    if generator != "generator2":
        return ()
    if "enemy_factions" in spec:
        return tuple(str(faction) for faction in spec["enemy_factions"])
    return tuple(faction for faction in GENERATOR2_FACTION_IDS if faction != str(player_faction))


def _mission_map_for_level(profile: str | None, level_id: int, default: str, *, briefing: bool) -> str:
    if not profile:
        return default
    maps = ua_mission_briefing_maps(profile) if briefing else ua_mission_debriefing_maps(profile)
    if not maps:
        return default
    expected = f"mb_{level_id:02d}.iff" if briefing else f"db_{level_id:02d}.iff"
    for map_name in maps:
        if map_name.lower() == expected:
            return map_name.upper()
    return maps[level_id % len(maps)].upper()


def _tuple_values(values: dict[Any, list[int] | tuple[int, ...]]) -> dict[Any, tuple[int, ...]]:
    return {key: tuple(int(value) for value in sequence) for key, sequence in values.items()}


def _int_faction_roster_to_codes(values: dict[int, list[int]]) -> dict[str, list[int]]:
    return {
        GENERATOR2_FACTION_CODES_BY_ID[faction]: list(items)
        for faction, items in values.items()
        if faction in GENERATOR2_FACTION_CODES_BY_ID
    }


def _int_faction_values_to_codes(values: dict[int, int]) -> dict[str, int]:
    return {
        GENERATOR2_FACTION_CODES_BY_ID[faction]: int(value)
        for faction, value in values.items()
        if faction in GENERATOR2_FACTION_CODES_BY_ID
    }


def _level_id_from_filename(filename: str) -> int:
    digits = "".join(ch for ch in filename if ch.isdigit())
    if len(digits) >= 2:
        return int(digits[:2])
    return 0


def _level_filename(level_id: int) -> str:
    return f"L{level_id:02d}{level_id:02d}.ldf"


def _dedupe(values: list[int]) -> list[int]:
    return list(dict.fromkeys(values))


def _with_black_sect_mixed_units(units: dict[int, list[int]]) -> dict[int, list[int]]:
    result = {owner: list(values) for owner, values in units.items()}
    mixed: list[int] = []
    for faction in (_FACTION_PLAYER, _FACTION_SULGOGARS, _FACTION_MYKONIANS, _FACTION_TAERKASTEN, _FACTION_GHORKOVS):
        mixed.extend(result.get(faction, []))
    mixed.extend(result.get(_FACTION_BLACK_SECT, []))
    result[_FACTION_BLACK_SECT] = _dedupe(mixed)
    return result


def _with_black_sect_mixed_buildings(buildings: dict[int, list[int]]) -> dict[int, list[int]]:
    result = {owner: list(values) for owner, values in buildings.items()}
    mixed: list[int] = []
    for faction in (
        _FACTION_PLAYER,
        _FACTION_SULGOGARS,
        _FACTION_MYKONIANS,
        _FACTION_TAERKASTEN,
        _FACTION_BLACK_SECT,
        _FACTION_GHORKOVS,
    ):
        mixed.extend(result.get(faction, []))
    result[_FACTION_BLACK_SECT] = _dedupe(mixed)
    return result


def _default_robo_ids(robos: dict[int, list[int]]) -> dict[int, int]:
    return {owner: values[-1] for owner, values in robos.items() if values}


_DEFAULT_PROFILE_REGISTRY = ProfileRegistry.from_package()
