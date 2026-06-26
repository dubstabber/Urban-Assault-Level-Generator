"""Generator constants recovered from the legacy project."""

from __future__ import annotations

from .data import (
    UA_METROPOLIS_DAWN_PROFILE,
    UA_ORIGINAL_PROFILE,
    ua_building_labels,
    ua_building_typ_map,
    ua_faction_buildings,
    ua_faction_player_robo_ids,
    ua_faction_robo_ids,
    ua_faction_units,
    ua_level_ids,
    ua_unit_labels,
)

TYP_MAP_INTERIOR_LOOKUP = [
    0x00, 0x01, 0x02, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B,
    0x0C, 0x0D, 0x10, 0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17,
    0x18, 0x19, 0x1A, 0x1B, 0x1C, 0x1D, 0x1E, 0x1F, 0x20, 0x21,
    0x22, 0x23, 0x24, 0x25, 0x26, 0x27, 0x28, 0x29, 0x2A, 0x2B,
    0x2C, 0x2D, 0x2E, 0x2F, 0x30, 0x30, 0x31, 0x32, 0x33, 0x34,
    0x42, 0x43, 0x44, 0x45, 0x46, 0x47, 0x48, 0x49, 0x4B, 0x4C,
    0x4D, 0x4E, 0x4F, 0x50, 0x51, 0x5F, 0x60, 0x61, 0x62, 0x63,
    0x78, 0x82, 0x83, 0x84, 0x85, 0x86, 0x87, 0x88, 0x89, 0x8A,
    0x8B, 0x8C, 0x96, 0x97, 0x98, 0x99, 0x9A, 0x9B, 0x9C, 0x9D,
    0x9E, 0x9F, 0xA0, 0xA1, 0xA2, 0xA3, 0xA4, 0xA5, 0xA6, 0xA7,
    0xA8, 0xA9, 0xAA, 0xAB, 0xAC, 0xAD, 0xAE, 0xAF, 0xB0, 0xB1,
    0xB2, 0xB3, 0xB4, 0xB5, 0xB6, 0xB7, 0xB8, 0xB9, 0xBA, 0xBB,
    0xBC, 0x32, 0xC6, 0xC7, 0xE6, 0xE7, 0xE8, 0xE9, 0xEA,
]

TYP_BORDER_TOP_LEFT = 0xF8
TYP_BORDER_TOP = 0xFC
TYP_BORDER_TOP_RIGHT = 0xF9
TYP_BORDER_LEFT = 0xFF
TYP_BORDER_RIGHT = 0xFD
TYP_BORDER_BOTTOM_LEFT = 0xFB
TYP_BORDER_BOTTOM = 0xFE
TYP_BORDER_BOTTOM_RIGHT = 0xFA
TYP_PLAYER_BASE = 0xCA
TYP_GATE_CLOSED_1 = 0xF4
TYP_GATE_CLOSED_2 = 0xF3
TYP_SUPERITEM = 0xF5

BLG_PLAYER_BASE = 5
BLG_SUPERITEM = 35

FACTION_NEUTRAL = 0
FACTION_PLAYER = 1
FACTION_SULGOGARS = 2
FACTION_MYKONIANS = 3
FACTION_TAERKASTEN = 4
FACTION_BLACK_SECT = 5
FACTION_GHORKOVS = 6
FACTION_TUTOR = 7

FACTION_NAMES = {
    FACTION_PLAYER: "Resistance",
    FACTION_SULGOGARS: "Sulgogars",
    FACTION_MYKONIANS: "Mykonians",
    FACTION_TAERKASTEN: "Taerkasten",
    FACTION_BLACK_SECT: "Black Sect",
    FACTION_GHORKOVS: "Ghorkovs",
    FACTION_TUTOR: "Tutor",
}

GENERATOR1_CAMPAIGN_FILENAMES = [
    "l2525.ldf", "l2626.ldf", "l9898.ldf",
    "l0101.ldf", "l0202.ldf", "l0303.ldf", "l0404.ldf", "l0505.ldf",
    "l1010.ldf", "l1111.ldf", "l1212.ldf",
    "l2020.ldf", "l2121.ldf", "l2222.ldf", "l2323.ldf",
    "l3030.ldf", "l3131.ldf", "l3232.ldf", "l3333.ldf", "l3434.ldf",
    "l4040.ldf", "l4141.ldf", "l4242.ldf", "l4343.ldf", "l4444.ldf",
    "l5050.ldf", "l5151.ldf", "l5252.ldf", "l5353.ldf", "l5454.ldf",
    "l6060.ldf", "l6161.ldf", "l6262.ldf", "l6363.ldf", "l6464.ldf",
    "l6666.ldf",
    "l7070.ldf", "l7171.ldf", "l7272.ldf", "l7373.ldf", "l7474.ldf", "l7575.ldf",
    "l1515.ldf", "l9999.ldf",
]

GENERATOR1_MD_CAMPAIGN_LEVEL_IDS = ua_level_ids(UA_METROPOLIS_DAWN_PROFILE)
GENERATOR1_MD_CAMPAIGN_FILENAMES = [f"L{level_id:02d}{level_id:02d}.ldf" for level_id in GENERATOR1_MD_CAMPAIGN_LEVEL_IDS]
GENERATOR1_CAMPAIGN_PROFILES = ("original", "md-ghorkov", "md-taerkasten")
GENERATOR1_MD_GHORKOV_LEVEL_IDS = [7, 14, 17, 19, 28, 35, 37, 39, 46, 48, 56, 58, 67, 69, 77, 79]
GENERATOR1_MD_TAERKASTEN_LEVEL_IDS = [6, 8, 13, 16, 18, 29, 36, 38, 45, 47, 55, 57, 65, 68, 78]
GENERATOR1_MD_CAMPAIGN_LEVEL_IDS_BY_PROFILE = {
    "md-ghorkov": GENERATOR1_MD_GHORKOV_LEVEL_IDS,
    "md-taerkasten": GENERATOR1_MD_TAERKASTEN_LEVEL_IDS,
}
GENERATOR1_MD_CAMPAIGN_TARGETS_BY_PROFILE = {
    "md-ghorkov": {
        7: [14],
        14: [17, 19],
        17: [28],
        19: [35],
        28: [37, 39],
        35: [46],
        37: [48],
        39: [56],
        46: [58, 67],
        48: [69],
        56: [69],
        58: [77],
        67: [77],
        69: [79],
        77: [79],
        79: [7],
    },
    "md-taerkasten": {
        6: [13, 16],
        8: [45],
        13: [18],
        16: [8, 29],
        18: [36, 38],
        29: [45],
        36: [47],
        38: [55, 57],
        45: [55, 57],
        47: [65, 68],
        55: [68],
        57: [68],
        65: [78],
        68: [78],
        78: [6],
    },
}
GENERATOR1_MD_GHORKOV_PLAYER_ROBO_BY_LEVEL = {
    7: 176,
    14: 176,
    17: 176,
    19: 176,
    28: 176,
    35: 176,
    37: 177,
    39: 177,
    46: 177,
    48: 177,
    56: 177,
    58: 177,
    67: 177,
    69: 177,
    77: 177,
    79: 177,
}


def _dedupe(values: list[int]) -> list[int]:
    return list(dict.fromkeys(values))


def _with_black_sect_mixed_units(units: dict[int, list[int]]) -> dict[int, list[int]]:
    result = {owner: list(values) for owner, values in units.items()}
    mixed: list[int] = []
    for faction in (FACTION_PLAYER, FACTION_SULGOGARS, FACTION_MYKONIANS, FACTION_TAERKASTEN, FACTION_GHORKOVS):
        mixed.extend(result.get(faction, []))
    mixed.extend(result.get(FACTION_BLACK_SECT, []))
    result[FACTION_BLACK_SECT] = _dedupe(mixed)
    return result


def _with_black_sect_mixed_buildings(buildings: dict[int, list[int]]) -> dict[int, list[int]]:
    result = {owner: list(values) for owner, values in buildings.items()}
    mixed: list[int] = []
    for faction in (
        FACTION_PLAYER,
        FACTION_SULGOGARS,
        FACTION_MYKONIANS,
        FACTION_TAERKASTEN,
        FACTION_BLACK_SECT,
        FACTION_GHORKOVS,
    ):
        mixed.extend(result.get(faction, []))
    result[FACTION_BLACK_SECT] = _dedupe(mixed)
    return result


def _default_robo_ids(robos: dict[int, list[int]]) -> dict[int, int]:
    return {owner: values[-1] for owner, values in robos.items() if values}


VEHICLES_BY_FACTION = _with_black_sect_mixed_units(ua_faction_units(UA_ORIGINAL_PROFILE))
BUILDINGS_BY_FACTION = _with_black_sect_mixed_buildings(ua_faction_buildings(UA_ORIGINAL_PROFILE))
METROPOLIS_DAWN_VEHICLES_BY_FACTION = _with_black_sect_mixed_units(ua_faction_units(UA_METROPOLIS_DAWN_PROFILE))
METROPOLIS_DAWN_BUILDINGS_BY_FACTION = _with_black_sect_mixed_buildings(
    ua_faction_buildings(UA_METROPOLIS_DAWN_PROFILE)
)

GENERATOR1_PLAYER_TECH_VEHICLE_IDS = [vehicle for vehicle in VEHICLES_BY_FACTION[FACTION_PLAYER] if vehicle != 9]
GENERATOR1_PLAYER_TECH_BUILDING_IDS = list(BUILDINGS_BY_FACTION[FACTION_PLAYER])

_VEHICLE_PROBABILITY_BY_ID = {1: 2, 2: 2, 3: 3, 12: 5, 11: 5, 10: 2, 6: 2, 15: 3, 14: 4, 4: 4, 7: 4, 5: 2, 133: 6, 134: 6}
VEHICLES_PLAYER_IDS = [vehicle for vehicle in VEHICLES_BY_FACTION[FACTION_PLAYER] if vehicle in _VEHICLE_PROBABILITY_BY_ID]
VEHICLES_PLAYER_PROBABILITIES = [_VEHICLE_PROBABILITY_BY_ID[vehicle] for vehicle in VEHICLES_PLAYER_IDS]
BUILDINGS_PLAYER_IDS = list(BUILDINGS_BY_FACTION[FACTION_PLAYER])
BUILDINGS_PLAYER_PROBABILITIES = [3, 4, 4, 5, 3, 4, 3, 4]

HOST_VEHICLE_BY_FACTION = _default_robo_ids(ua_faction_robo_ids(UA_ORIGINAL_PROFILE))
METROPOLIS_DAWN_PLAYER_ROBOS_BY_FACTION = ua_faction_player_robo_ids(UA_METROPOLIS_DAWN_PROFILE)
METROPOLIS_DAWN_HOST_VEHICLE_BY_FACTION = _default_robo_ids(ua_faction_robo_ids(UA_METROPOLIS_DAWN_PROFILE))
METROPOLIS_DAWN_PLAYER_HOST_VEHICLE_BY_FACTION = _default_robo_ids(
    METROPOLIS_DAWN_PLAYER_ROBOS_BY_FACTION
)

HOST_BUILDING_BY_FACTION = {
    FACTION_PLAYER: [63, 1, 11, 64],
    FACTION_SULGOGARS: [11],
    FACTION_MYKONIANS: [10],
    FACTION_TAERKASTEN: [17],
    FACTION_BLACK_SECT: [11],
    FACTION_GHORKOVS: [12],
    FACTION_TUTOR: [64],
}

BUILDING_TYP_BY_ID = {
    **ua_building_typ_map(UA_ORIGINAL_PROFILE),
    **ua_building_typ_map(UA_METROPOLIS_DAWN_PROFILE),
    35: TYP_SUPERITEM,
}

VEHICLE_LABELS_BY_ID = {
    **ua_unit_labels(UA_ORIGINAL_PROFILE),
    **ua_unit_labels(UA_METROPOLIS_DAWN_PROFILE),
}
BUILDING_LABELS_BY_ID = {
    **ua_building_labels(UA_ORIGINAL_PROFILE),
    **ua_building_labels(UA_METROPOLIS_DAWN_PROFILE),
}

SKY_OPTIONS = [
    "1998_02.base", "1998_03.base", "1998_05.base", "1998_06.base",
    "am_2.base", "am_3.base", "ct6.base", "mod7.base", "moda.base",
    "Nacht1.base", "Nacht2.base", "nt3.base", "nt7.base", "s3_4.base",
    "smod2.base", "smod4.base", "smod5.bas", "Smod6.base", "smod7.base",
    "smod8.base", "sterne.base", "wow1.base", "wow5.base", "wow7.base",
    "wow8.bas", "wow9.base", "wowa.bas", "wowb.base", "wowc.base",
    "wowd.base", "wowe.base", "wowf.base", "wowh.bas", "wowi.base",
    "x2.base", "x4.base", "x7.base", "X9.bas", "xb.base", "xc.base",
]

GENERATOR2_LEVELS = {
    1: [2, 3], 2: [4], 3: [5], 4: [10], 5: [11, 12],
    10: [20], 11: [21], 12: [22, 23], 15: [], 20: [30, 34],
    21: [31], 22: [32], 23: [33], 25: [], 26: [], 30: [40],
    31: [41], 32: [42], 33: [43], 34: [40, 44], 40: [50, 51],
    41: [52], 42: [53], 43: [54], 44: [50], 50: [60], 51: [66],
    52: [61, 62], 53: [63], 54: [64], 60: [70], 61: [75],
    62: [72], 63: [73], 64: [74], 66: [71], 70: [15], 71: [15],
    72: [15], 73: [15], 74: [15], 75: [15],
}

GENERATOR2_CAMPAIGN_LEVEL_IDS = [
    1, 2, 3, 4, 5, 10, 11, 12, 15, 20, 21, 22, 23, 25, 26,
    30, 31, 32, 33, 34, 40, 41, 42, 43, 44, 50, 51, 52, 53, 54,
    60, 61, 62, 63, 64, 66, 70, 71, 72, 73, 74, 75,
]
GENERATOR2_CAMPAIGN_PROFILES = ("original", "md-ghorkov", "md-taerkasten")
GENERATOR2_MD_CAMPAIGN_LEVEL_IDS_BY_PROFILE = {
    profile: list(level_ids)
    for profile, level_ids in GENERATOR1_MD_CAMPAIGN_LEVEL_IDS_BY_PROFILE.items()
}
GENERATOR2_MD_CAMPAIGN_TARGETS_BY_PROFILE = {
    profile: {level_id: list(targets) for level_id, targets in target_graph.items()}
    for profile, target_graph in GENERATOR1_MD_CAMPAIGN_TARGETS_BY_PROFILE.items()
}

GENERATOR2_FACTIONS = ["sul", "myk", "tae", "bla", "gho"]
GENERATOR2_FACTION_IDS = {"res": 1, "sul": 2, "myk": 3, "tae": 4, "bla": 5, "gho": 6}
GENERATOR2_FACTION_CODES_BY_ID = {faction_id: faction for faction, faction_id in GENERATOR2_FACTION_IDS.items()}
GENERATOR2_HOST_VEHICLES = {"sul": 61, "myk": 58, "tae": 60, "bla": 62}
GENERATOR2_SET_LIST = {
    1: [
        0, 1, 2, 5, 6, 7, 8, 9, 10, 11, 12, 13, 16, 17, 18, 19,
        20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 31, 32, 33, 34,
        35, 36, 37, 38, 39, 40, 41, 44, 50, 51, 59, 67, 70, 71,
        72, 74, 75, 76, 77, 78, 80, 81, 82, 95, 96, 97, 98, 99,
        100, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 150,
        151, 153, 154, 155, 157, 159, 160, 161, 162, 163, 164, 166,
        167, 168, 169, 170, 171, 172, 173, 174, 175, 176, 177, 178,
        179, 180, 181, 182, 183, 184, 185, 186, 187, 188, 189, 198,
        232, 233, 234, 235, 236,
    ],
    2: [
        0, 1, 2, 5, 6, 7, 8, 9, 11, 12, 13, 16, 17, 18, 19, 20,
        21, 22, 23, 24, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36,
        37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50,
        51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 65,
        66, 67, 68, 69, 70, 71, 72, 75, 76, 77, 78, 80, 81, 82,
        83, 87, 89, 90, 92, 93, 94, 95, 97, 99, 100, 120, 121,
        122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 133, 150,
        151, 152, 153, 155, 158, 159, 160, 161, 162, 163, 167, 168,
        171, 172, 173, 174, 175, 176, 177, 178, 179, 180, 181, 182,
        183, 184, 185, 186, 187, 188, 189, 190, 191, 192, 193, 198,
        199, 210, 211, 212, 213, 214, 215, 216, 217, 218, 219, 220,
        221, 222, 223, 224, 225,
    ],
    3: [
        0, 1, 2, 5, 6, 7, 8, 9, 10, 11, 12, 13, 16, 17, 18, 19,
        20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 31, 32, 33, 34,
        35, 36, 37, 38, 39, 40, 41, 44, 59, 67, 69, 70, 71, 72,
        74, 75, 76, 77, 78, 80, 81, 82, 100, 130, 131, 132, 133,
        134, 135, 136, 137, 138, 139, 150, 151, 152, 153, 155, 156,
        157, 158, 159, 160, 161, 162, 163, 164, 165, 166, 167, 168,
        169, 170, 171, 172, 173, 174, 175, 176, 177, 178, 179, 180,
        181, 182, 183, 184, 185, 186, 187, 188, 189,
    ],
    4: [
        0, 1, 2, 5, 6, 7, 8, 9, 10, 11, 12, 13, 16, 17, 18, 19,
        20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 31, 32, 33, 34,
        35, 36, 37, 38, 39, 40, 41, 59, 60, 66, 67, 69, 70, 71,
        72, 74, 75, 76, 77, 78, 80, 81, 82, 130, 131, 132, 133,
        134, 135, 136, 137, 138, 139, 140, 141, 150, 151, 153, 155,
        158, 159, 160, 161, 162, 163, 164, 165, 166, 167, 168, 169,
        170, 171, 172, 173, 174, 175, 176, 177, 178, 179, 180, 181,
        182, 183, 184, 185, 186, 187, 188, 189,
    ],
    5: [
        0, 1, 2, 5, 6, 7, 8, 9, 10, 11, 12, 13, 16, 17, 18, 19,
        20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33,
        34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47,
        48, 49, 50, 51, 52, 53, 54, 55, 57, 58, 59, 62, 63, 65,
        66, 67, 68, 69, 70, 71, 72, 75, 76, 78, 79, 82, 84, 87,
        92, 93, 94, 95, 97, 98, 99, 105, 106, 107, 108, 109, 113,
        114, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130,
        131, 133, 134, 135, 150, 151, 152, 153, 155, 157, 158, 159,
        161, 160, 162, 163, 166, 167, 168, 171, 172, 173, 174, 175,
        176, 177, 178, 179, 180, 181, 182, 183, 184, 185, 186, 187,
        188, 190, 191, 198, 199, 210, 211, 212, 213, 214, 215, 216,
        217, 218, 219, 220, 221, 222, 223, 224, 225,
    ],
    6: [
        0, 1, 2, 5, 6, 7, 8, 9, 10, 11, 12, 13, 16, 17, 18, 19,
        20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 31, 32, 33, 34,
        35, 36, 37, 38, 39, 40, 41, 44, 59, 66, 67, 68, 70, 71,
        72, 74, 75, 76, 77, 78, 79, 80, 81, 82, 95, 96, 97, 98,
        99, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140,
        141, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160,
        161, 162, 163, 164, 165, 166, 167, 168, 169, 170, 171, 172,
        173, 174, 175, 176, 177, 178, 179, 180, 181, 182, 183, 184,
        185, 186, 188, 189, 228, 229, 230, 231, 232, 233, 234, 248,
    ],
}
GENERATOR2_VEHICLES = {
    "res": [1, 2, 3, 4, 5, 6, 7, 9, 10, 11, 12, 14, 15, 16],
    "sul": [71, 72, 73, 74],
    "myk": [63, 64, 65, 66, 67, 68, 69, 70],
    "tae": [8, 32, 33, 34, 35, 36, 37, 38, 131],
    "gho": [22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 130],
}
GENERATOR2_VEHICLES["bla"] = (
    GENERATOR2_VEHICLES["res"] + GENERATOR2_VEHICLES["sul"] + GENERATOR2_VEHICLES["myk"]
    + GENERATOR2_VEHICLES["tae"] + GENERATOR2_VEHICLES["gho"]
)
GENERATOR2_BUILDINGS = {
    "res": [11, 63, 2, 28, 3],
    "sul": [10],
    "myk": [10, 13, 72],
    "tae": [17, 31, 53, 73],
    "bla": [18, 1, 54, 64],
    "gho": [30, 52, 12, 71],
}
GENERATOR2_MD_VEHICLES = {
    GENERATOR2_FACTION_CODES_BY_ID[faction]: list(vehicles)
    for faction, vehicles in METROPOLIS_DAWN_VEHICLES_BY_FACTION.items()
    if faction in GENERATOR2_FACTION_CODES_BY_ID
}
GENERATOR2_MD_BUILDINGS = {
    GENERATOR2_FACTION_CODES_BY_ID[faction]: list(buildings)
    for faction, buildings in METROPOLIS_DAWN_BUILDINGS_BY_FACTION.items()
    if faction in GENERATOR2_FACTION_CODES_BY_ID
}
GENERATOR2_MD_PLAYER_ROBOS = {
    GENERATOR2_FACTION_CODES_BY_ID[faction]: list(robos)
    for faction, robos in METROPOLIS_DAWN_PLAYER_ROBOS_BY_FACTION.items()
    if faction in GENERATOR2_FACTION_CODES_BY_ID
}
GENERATOR2_SCOUT_VEHICLES = {9, 74, 67, 35, 29}
GENERATOR2_SKIES = [
    "1998_01", "1998_02", "1998_03", "1998_05", "1998_06", "Am_1", "Am_2", "Am_3",
    "Arz1", "Asky2", "Braun1", "Ct6", "H", "H7", "Haamitt1", "Haamitt4",
    "Mod2", "Mod4", "Mod5", "Mod7", "Mod8", "Mod9", "Moda", "Modb",
    "Nacht1", "Nacht2", "Newtry5", "Nosky", "Nt1", "Nt2", "Nt3", "Nt5",
    "Nt6", "Nt7", "Nt8", "Nt9", "Nta", "S3_1", "S3_4", "Smod1",
    "Smod2", "Smod3", "Smod4", "Smod5", "Smod6", "Smod7", "Smod8",
    "Sterne", "wow1", "wow5", "wow7", "wow8", "wow9", "wowa", "wowb",
    "wowc", "wowd", "wowe", "wowf", "wowh", "wowi", "wowj", "x1",
    "x2", "x4", "x5", "x7", "x8", "x9", "xa", "xb", "xc",
]


def level_id_from_filename(filename: str) -> int:
    digits = "".join(ch for ch in filename if ch.isdigit())
    if len(digits) >= 2:
        return int(digits[:2])
    return 0


def level_filename(level_id: int) -> str:
    return f"L{level_id:02d}{level_id:02d}.ldf"


def sector_to_world_x(sector_x: int, plus_one: bool = False) -> int:
    value = int((sector_x + 0.5) * 1200)
    return value + (1 if plus_one else 0)


def sector_to_world_z(sector_y: int, plus_one: bool = False) -> int:
    value = int(-(sector_y + 0.5) * 1200)
    return value + (1 if plus_one else 0)
