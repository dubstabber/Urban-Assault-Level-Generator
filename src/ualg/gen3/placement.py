"""Identity-remap helpers shared by the Generator3 remix builder.

These functions keep the authored *structure* (territory shapes, building
roles) while swapping the *identity* (which faction owns what) according to a
seeded faction remap.
"""

from __future__ import annotations

from ..campaign_profiles import ProfileRoster
from ..models import MapRows
from ..rng import MSVCRTRandom


def build_faction_remap(
    rng: MSVCRTRandom,
    *,
    player_owner: int,
    player_faction: int,
    enemy_owners: list[int],
    enemy_pool: list[int],
) -> dict[int, int]:
    """Map each skeleton owner to an output faction.

    The player owner becomes the profile's player faction; each distinct enemy
    owner is assigned a seeded enemy faction (without repeats while the pool
    lasts) so the same authored terrain hosts a different line-up per seed.
    """

    remap = {player_owner: player_faction}
    available = [faction for faction in enemy_pool if faction != player_faction]
    bag: list[int] = []
    for owner in enemy_owners:
        if owner in remap:
            continue
        if not bag:
            bag = list(available)
        if not bag:
            remap[owner] = owner
            continue
        index = rng.rand_mod(len(bag))
        remap[owner] = bag.pop(index)
    return remap


def relabel_own_map(rows: MapRows, faction_remap: dict[int, int]) -> MapRows:
    return [[faction_remap.get(value, value) for value in row] for row in rows]


def build_building_remap(roster: ProfileRoster, faction_remap: dict[int, int]) -> dict[int, int]:
    """Map faction-specific building ids to the remapped faction's analog."""

    owner_of_building: dict[int, tuple[int, int]] = {}
    for faction, buildings in roster.buildings_by_faction.items():
        if not isinstance(faction, int):
            continue
        for index, building in enumerate(buildings):
            owner_of_building.setdefault(building, (faction, index))

    remap: dict[int, int] = {}
    for building, (faction, index) in owner_of_building.items():
        new_faction = faction_remap.get(faction, faction)
        if new_faction == faction:
            continue
        replacements = roster.buildings_by_faction.get(new_faction, ())
        if replacements:
            remap[building] = replacements[min(index, len(replacements) - 1)]
    return remap


def remap_blg_map(rows: MapRows, building_remap: dict[int, int]) -> MapRows:
    if not building_remap:
        return [list(row) for row in rows]
    return [[building_remap.get(value, value) for value in row] for row in rows]


def choose_squad_vehicle(rng: MSVCRTRandom, roster: ProfileRoster, faction: int, fallback: int) -> int:
    vehicles = roster.vehicles_by_faction.get(faction, ())
    if not vehicles:
        return fallback
    return rng.choice(vehicles)
