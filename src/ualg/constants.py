"""Generator constants recovered from the legacy project."""

from __future__ import annotations

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

GENERATOR1_PLAYER_TECH_VEHICLE_IDS = [1, 16, 2, 3, 12, 11, 10, 6, 15, 14, 4, 7, 5, 133, 134]
GENERATOR1_PLAYER_TECH_BUILDING_IDS = [63, 1, 11, 64, 28, 2, 3, 54]

VEHICLES_PLAYER_IDS = [1, 2, 3, 12, 11, 10, 6, 15, 14, 4, 7, 5, 133, 134]
VEHICLES_PLAYER_PROBABILITIES = [2, 2, 3, 5, 5, 2, 2, 3, 4, 4, 4, 2, 6, 6]
BUILDINGS_PLAYER_IDS = [63, 1, 11, 64, 28, 2, 3, 54]
BUILDINGS_PLAYER_PROBABILITIES = [3, 4, 4, 5, 3, 4, 3, 4]

VEHICLES_BY_FACTION = {
    FACTION_PLAYER: [1, 16, 2, 3, 12, 11, 10, 6, 15, 14, 4, 7, 5, 9, 133, 134],
    FACTION_SULGOGARS: [73, 71, 72, 74],
    FACTION_MYKONIANS: [65, 64, 66, 68, 63, 69, 70, 67],
    FACTION_TAERKASTEN: [32, 37, 33, 8, 36, 38, 131, 34, 35],
    FACTION_BLACK_SECT: [
        1, 16, 2, 3, 12, 11, 10, 6, 15, 14, 4, 7, 5, 9, 133, 134,
        73, 71, 72, 74, 65, 64, 66, 68, 63, 69, 70, 67,
        32, 37, 33, 8, 36, 38, 131, 34, 35,
        22, 26, 24, 28, 25, 31, 130, 27, 30, 29,
    ],
    FACTION_GHORKOVS: [22, 26, 24, 28, 25, 23, 31, 130, 27, 30, 29],
    FACTION_TUTOR: [142],
}

BUILDINGS_BY_FACTION = {
    FACTION_PLAYER: BUILDINGS_PLAYER_IDS,
    FACTION_SULGOGARS: [10],
    FACTION_MYKONIANS: [10, 13, 72],
    FACTION_TAERKASTEN: [53, 17, 31, 73],
    FACTION_BLACK_SECT: [63, 1, 11, 64, 28, 2, 3, 54, 10, 13, 72, 53, 17, 31, 73, 18, 52, 12, 30, 71],
    FACTION_GHORKOVS: [52, 12, 30, 71],
    FACTION_TUTOR: [],
}

HOST_VEHICLE_BY_FACTION = {
    FACTION_PLAYER: 56,
    FACTION_SULGOGARS: 61,
    FACTION_MYKONIANS: 58,
    FACTION_TAERKASTEN: 60,
    FACTION_BLACK_SECT: 62,
    FACTION_GHORKOVS: 57,
    FACTION_TUTOR: 132,
}

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
    63: 201, 1: 201, 11: 201, 64: 201,
    28: 205, 2: 200, 3: 204, 54: 204,
    10: 15, 13: 239, 72: 240,
    53: 15, 17: 15, 31: 207, 73: 240,
    18: 204, 52: 15, 12: 15, 30: 207, 71: 240,
    35: TYP_SUPERITEM,
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

GENERATOR2_FACTIONS = ["sul", "myk", "tae", "bla", "gho"]
GENERATOR2_FACTION_IDS = {"res": 1, "sul": 2, "myk": 3, "tae": 4, "bla": 5, "gho": 6}
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
