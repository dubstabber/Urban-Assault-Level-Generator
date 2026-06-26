"""Custom level option state and validation helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

from ..constants import (
    FACTION_BLACK_SECT,
    FACTION_GHORKOVS,
    FACTION_MYKONIANS,
    FACTION_PLAYER,
    FACTION_SULGOGARS,
    FACTION_TAERKASTEN,
    FACTION_TUTOR,
    BUILDING_LABELS_BY_ID,
    BUILDINGS_BY_FACTION,
    VEHICLE_LABELS_BY_ID,
    VEHICLES_BY_FACTION,
)
from ..data import UA_ORIGINAL_PROFILE, ua_faction_robo_names
from ..generator1 import Generator1CustomOptions


CUSTOM_WIZARD_FACTIONS = [
    FACTION_GHORKOVS,
    FACTION_TAERKASTEN,
    FACTION_MYKONIANS,
    FACTION_SULGOGARS,
    FACTION_BLACK_SECT,
    FACTION_TUTOR,
]
CUSTOM_BUILD_FACTIONS = [FACTION_PLAYER, *CUSTOM_WIZARD_FACTIONS]
CUSTOM_WIZARD_PAGE_TITLES = [
    "Level Size",
    "Host Stations",
    "Beam Gate",
    "Stoudson Bombs",
    "Build Options",
]
GHORKOV_HOST_VEHICLES = {
    name: robo_id
    for robo_id, name in ua_faction_robo_names(UA_ORIGINAL_PROFILE)[FACTION_GHORKOVS].items()
}
GHORKOV_HOST_VEHICLE_ALIASES = {"Tarantul 1": 59, "Tarantul 2": 57}
RESISTANCE_NEW_BUILDING_IDS = tuple(range(38, 50)) + tuple(range(90, 94))
BLACK_SECT_NEW_BUILDING_IDS = tuple(range(38, 50)) + tuple(range(90, 97))
NEW_BUILDING_IDS = set(BLACK_SECT_NEW_BUILDING_IDS)

VEHICLE_LABELS = {
    1: "Weasel",
    2: "Jaguar",
    3: "Tiger",
    4: "Falcon",
    5: "Warhammer",
    6: "Wasp",
    7: "Mosquito",
    8: "Hetzel",
    9: "Dragonfly",
    10: "Firefly",
    11: "Rock-Sled",
    12: "Rhino",
    14: "Eagle",
    15: "Hornet",
    16: "Fox",
    22: "Bronsteijn",
    23: "Ghorkov Host",
    24: "Giant",
    25: "Shark",
    26: "Tekh-Trak",
    27: "Rokh",
    28: "Gorokhov",
    29: "Ghargoil",
    30: "Ghok",
    31: "Minenleger",
    32: "Pamir",
    33: "Eisenhans",
    34: "Flammenwerfer",
    35: "Leopard",
    36: "Tiger II",
    37: "Marder",
    38: "Jaguar II",
    57: "Tarantul 2",
    59: "Tarantul 1",
    63: "Myko 1",
    64: "Myko 2",
    65: "Myko 3",
    66: "Myko 4",
    67: "Myko 5",
    68: "Myko 6",
    69: "Myko 7",
    70: "Myko 8",
    71: "Sulgogar 2",
    72: "Sulgogar 3",
    73: "Sulgogar 1",
    74: "Sulgogar 4",
    130: "Ghorkov Special",
    131: "Taerkast Special",
    133: "Resistance Special 1",
    134: "Resistance Special 2",
    142: "Tutorial Drone",
}

BUILDING_LABELS = {
    1: "Resistance Power",
    2: "Resistance Radar",
    3: "Resistance Flak",
    10: "Mykonian Power",
    11: "Resistance Station",
    12: "Ghorkov Power",
    13: "Mykonian Flak",
    17: "Taerkast Power",
    18: "Black Sect Flak",
    28: "Resistance Beam",
    30: "Ghorkov Flak",
    31: "Taerkast Flak",
    38: "New Building 38",
    39: "New Building 39",
    40: "New Building 40",
    41: "New Building 41",
    42: "New Building 42",
    43: "New Building 43",
    44: "New Building 44",
    45: "New Building 45",
    46: "New Building 46",
    47: "New Building 47",
    48: "New Building 48",
    49: "New Building 49",
    52: "Ghorkov Station",
    53: "Taerkast Station",
    54: "Resistance Defense",
    63: "Resistance Base",
    64: "Resistance Power 2",
    71: "Black Sect Station",
    72: "Mykonian Station",
    73: "Taerkast Station 2",
    90: "New Building 90",
    91: "New Building 91",
    92: "New Building 92",
    93: "New Building 93",
    94: "New Building 94",
    95: "New Building 95",
    96: "New Building 96",
}
VEHICLE_LABELS.update(VEHICLE_LABELS_BY_ID)
BUILDING_LABELS.update(BUILDING_LABELS_BY_ID)


class CustomGenerationOptions:
    seed: int = 0
    difficulty: int = 5
    skill: int = 0
    improved: bool = True


def _default_host_slots(value: bool = False) -> dict[int, list[bool]]:
    return {faction: [value, value, value] for faction in CUSTOM_WIZARD_FACTIONS}


def _default_host_energy_slots() -> dict[int, list[int]]:
    return {faction: [1500, 1500, 1500] for faction in CUSTOM_WIZARD_FACTIONS}


def _default_faction_random_build_options() -> dict[int, bool]:
    return {faction: True for faction in CUSTOM_BUILD_FACTIONS}


@dataclass(slots=True)
class CustomWizardState:
    random_size: bool = True
    width: int = 20
    height: int = 20
    player_energy: int = 1500
    host_present: dict[int, list[bool]] = field(default_factory=_default_host_slots)
    host_energy: dict[int, list[int]] = field(default_factory=_default_host_energy_slots)
    ghorkov_host_types: list[str] = field(default_factory=lambda: ["Turantul I", "Turantul I", "Turantul I"])
    gate_target_level_id: int = 0
    random_gate_keys: bool = True
    gate_key_count: int = 0
    win_movie: bool = False
    lose_movie: bool = False
    random_bombs: bool = True
    bomb_included: list[bool] = field(default_factory=lambda: [False, False])
    bomb_custom_countdown: list[bool] = field(default_factory=lambda: [False, False])
    bomb_countdown_seconds: list[int] = field(default_factory=lambda: [600, 1200])
    random_build_options: bool = True
    faction_random_build_options: dict[int, bool] = field(default_factory=_default_faction_random_build_options)
    enabled_vehicles: dict[int, set[int]] = field(default_factory=dict)
    enabled_buildings: dict[int, set[int]] = field(default_factory=dict)


def custom_wizard_options_from_state(
    state: CustomWizardState,
    *,
    allow_new_buildings: bool = True,
) -> Generator1CustomOptions:
    options = Generator1CustomOptions()

    if not state.random_size:
        width = _int_value(state.width, "horizontal level size")
        height = _int_value(state.height, "vertical level size")
        if not 4 <= width <= 43:
            raise ValueError("Horizontal level size must be between 4 and 43.")
        if not 4 <= height <= 30:
            raise ValueError("Vertical level size must be between 4 and 30.")
        options.width = width + 2
        options.height = height + 2

    options.player_energy = _legacy_energy_value(state.player_energy, "player host station energy")

    any_host = False
    for faction in CUSTOM_WIZARD_FACTIONS:
        present = _bool_slots(state.host_present.get(faction, []))
        if not any(present):
            continue
        any_host = True
        options.ai_slot_present[faction] = present
        energies = _int_slots(state.host_energy.get(faction, []), 1500)
        options.ai_slot_energy[faction] = [
            _legacy_energy_value(energies[slot], f"{_faction_label(faction)} host #{slot + 1} energy")
            if present[slot]
            else 0
            for slot in range(3)
        ]
        if faction == FACTION_GHORKOVS:
            host_types = (state.ghorkov_host_types + ["Turantul I", "Turantul I", "Turantul I"])[:3]
            vehicles = []
            for slot, host_type in enumerate(host_types):
                vehicle_id = _ghorkov_host_vehicle_id(host_type)
                if present[slot] and not vehicle_id:
                    raise ValueError(f"Ghorkov host #{slot + 1} must use a valid Turantul host type.")
                vehicles.append(vehicle_id if present[slot] else 0)
            options.ai_slot_host_vehicle_id[faction] = vehicles

    if not any_host:
        raise ValueError("You must have at least 1 enemy host station.")

    options.gate_target_level_id = max(0, _int_value(state.gate_target_level_id, "beam gate target level"))
    options.win_movie = bool(state.win_movie)
    options.lose_movie = bool(state.lose_movie)
    if not state.random_gate_keys:
        gate_key_count = _int_value(state.gate_key_count, "beam gate key sector count")
        if not 0 <= gate_key_count <= 16:
            raise ValueError("Beam gate key sector count must be between 0 and 16.")
        options.gate_key_count = gate_key_count

    if state.random_bombs:
        options.random_superitems = True
    else:
        bomb_flags = _bool_slots(state.bomb_included, count=2)
        if bomb_flags[1] and not bomb_flags[0]:
            raise ValueError("Bomb 2 requires Bomb 1.")
        options.superitem_flags = bomb_flags
        countdowns = _int_slots(state.bomb_countdown_seconds, 600, count=2)
        custom_countdowns = _bool_slots(state.bomb_custom_countdown, count=2)
        for index, enabled in enumerate(bomb_flags, start=1):
            if not enabled or not custom_countdowns[index - 1]:
                continue
            seconds = countdowns[index - 1]
            if not 1 <= seconds <= 3601:
                raise ValueError("Bomb countdowns must be between 1 and 3601 seconds.")
            options.superitem_countdowns[index] = seconds * 1000

    _collect_build_options_from_state(state, options, allow_new_buildings=allow_new_buildings)
    return options


def _int_value(value: object, label: str) -> int:
    if isinstance(value, str):
        raw_value = value.strip()
        if not raw_value:
            raise ValueError(f"Please enter {label}.")
        value = raw_value
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be a whole number.") from exc


def _bool_slots(values: Sequence[object], *, count: int = 3) -> list[bool]:
    result = [bool(value) for value in list(values)[:count]]
    return (result + [False] * count)[:count]


def _int_slots(values: Sequence[object], default: int, *, count: int = 3) -> list[int]:
    raw_values = list(values)[:count]
    result = []
    for value in raw_values:
        try:
            result.append(int(value))
        except (TypeError, ValueError):
            result.append(default)
    return (result + [default] * count)[:count]


def _legacy_energy_value(value: object, label: str) -> int:
    energy = _int_value(value, label)
    if not 1 <= energy <= 10_000_000:
        raise ValueError(f"{label} must be between 1 and 10000000.")
    return energy * 400


def _faction_label(faction: int) -> str:
    labels = {
        FACTION_PLAYER: "Resistance",
        FACTION_GHORKOVS: "Ghorkovs",
        FACTION_TAERKASTEN: "Taerkasten",
        FACTION_MYKONIANS: "Mykonians",
        FACTION_SULGOGARS: "Sulgogars",
        FACTION_BLACK_SECT: "Black Sect",
        FACTION_TUTOR: "Tutorial",
    }
    return labels.get(faction, f"Faction {faction}")


def _vehicle_options_for_faction(faction: int) -> tuple[int, ...]:
    return tuple(dict.fromkeys(VEHICLES_BY_FACTION.get(faction, [])))


def _building_options_for_faction(faction: int, *, allow_new_buildings: bool = True) -> tuple[int, ...]:
    buildings = list(BUILDINGS_BY_FACTION.get(faction, []))
    if allow_new_buildings and faction == FACTION_PLAYER:
        buildings.extend(RESISTANCE_NEW_BUILDING_IDS)
    elif allow_new_buildings and faction == FACTION_BLACK_SECT:
        buildings.extend(BLACK_SECT_NEW_BUILDING_IDS)
    return tuple(dict.fromkeys(buildings))


def _option_label(kind: str, value: int) -> str:
    labels = VEHICLE_LABELS if kind == "vehicle" else BUILDING_LABELS
    return f"{labels.get(value, kind.title())} ({value})"


def _ghorkov_host_vehicle_id(host_type: str) -> int:
    return GHORKOV_HOST_VEHICLES.get(host_type, GHORKOV_HOST_VEHICLE_ALIASES.get(host_type, 0))


def _ordered_selected(selected: set[int], allowed: Sequence[int]) -> list[int]:
    return [value for value in allowed if value in selected]


def _active_custom_build_factions(state: CustomWizardState) -> list[int]:
    active = [FACTION_PLAYER]
    for faction in CUSTOM_WIZARD_FACTIONS:
        if any(_bool_slots(state.host_present.get(faction, []))):
            active.append(faction)
    return active


def _collect_build_options_from_state(
    state: CustomWizardState,
    options: Generator1CustomOptions,
    *,
    allow_new_buildings: bool,
) -> None:
    if state.random_build_options:
        return

    for faction in _active_custom_build_factions(state):
        if state.faction_random_build_options.get(faction, True):
            continue
        vehicle_options = _vehicle_options_for_faction(faction)
        building_options = _building_options_for_faction(faction, allow_new_buildings=allow_new_buildings)
        vehicles = _ordered_selected(state.enabled_vehicles.get(faction, set()), vehicle_options)
        buildings = _ordered_selected(state.enabled_buildings.get(faction, set()), building_options)
        options.enabled_vehicles[faction] = vehicles
        options.enabled_buildings[faction] = buildings

def _leading_int(value: str) -> int:
    digits = []
    for char in value.strip():
        if char.isdigit():
            digits.append(char)
        elif digits:
            break
    return int("".join(digits)) if digits else 0
