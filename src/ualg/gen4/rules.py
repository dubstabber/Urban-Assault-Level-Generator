"""Runtime access to baked Generator4 campaign rules."""

from __future__ import annotations

from dataclasses import dataclass
from functools import cache
from typing import Any

from ..data import gen4_rules
from .rules_builder import build_rules, write_rules


@dataclass(frozen=True)
class Archetype:
    """One campaign-slot rule record used to synthesize a new level."""

    record: dict[str, Any]

    @property
    def level_id(self) -> int:
        return int(self.record["level_id"])

    @property
    def name(self) -> str:
        return str(self.record["name"])

    @property
    def source(self) -> str:
        return str(self.record["source"])

    @property
    def tileset(self) -> int:
        return int(self.record["tileset"])

    @property
    def width(self) -> int:
        return int(self.record["width"])

    @property
    def height(self) -> int:
        return int(self.record["height"])

    @property
    def player_owner(self) -> int:
        return int(self.record["player_owner"])

    @property
    def enemy_owners(self) -> list[int]:
        return [int(owner) for owner in self.record.get("enemy_owners", [])]


def _load_rules() -> dict[str, Any]:
    try:
        return gen4_rules()
    except FileNotFoundError:
        rules = build_rules()
        try:
            write_rules(rules)
        except OSError:
            pass
        return rules


@cache
def rules_data() -> dict[str, Any]:
    data = _load_rules()
    if data.get("version") not in {1, 2}:
        raise ValueError("Unsupported Generator4 rules version.")
    return data


def rules_version() -> int:
    return int(rules_data().get("version", 1))


def profile_names() -> tuple[str, ...]:
    return tuple(rules_data().get("profiles", ()))


def source_for_profile(profile_id: str) -> str:
    return str(rules_data()["profiles"][profile_id]["source"])


def archetypes_for_profile(profile_id: str) -> tuple[Archetype, ...]:
    profile = rules_data()["profiles"][profile_id]
    return tuple(Archetype(record) for record in profile.get("levels", ()))


def archetype_for_level(profile_id: str, level_id: int) -> Archetype:
    for archetype in archetypes_for_profile(profile_id):
        if archetype.level_id == int(level_id):
            return archetype
    raise ValueError(f"no Generator4 archetype for level id {level_id} in profile {profile_id!r}")


def archetype_for_source_level(source: str, level_id: int) -> Archetype:
    for profile_id in profile_names():
        if source_for_profile(profile_id) != source:
            continue
        for archetype in archetypes_for_profile(profile_id):
            if archetype.level_id == int(level_id):
                return archetype
    raise ValueError(f"no Generator4 archetype for level id {level_id} in source {source!r}")
