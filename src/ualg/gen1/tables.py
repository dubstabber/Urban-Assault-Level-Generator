"""Generator1 scenario and tech-upgrade tables."""

from __future__ import annotations

from typing import Any

from ..constants import (
    FACTION_BLACK_SECT,
    FACTION_GHORKOVS,
    FACTION_MYKONIANS,
    FACTION_SULGOGARS,
    FACTION_TAERKASTEN,
    FACTION_TUTOR,
)

CATEGORY_DIM_RANGES = {
    1: (6, 10, 6, 10),
    2: (8, 13, 10, 25),
    3: (12, 18, 12, 28),
    4: (5, 7, 15, 25),
    5: (19, 22, 19, 22),
    6: (20, 27, 20, 27),
    7: (20, 25, 12, 25),
    8: (40, 45, 3, 3),
    9: (20, 25, 20, 25),
    10: (29, 32, 29, 32),
    11: (38, 45, 32, 32),
    12: (20, 25, 20, 25),
}

CATEGORY_ENERGY_PARAMS: dict[int, dict[Any, Any]] = {
    1: {"player": 320000, FACTION_TUTOR: (40, 40, 4000)},
    2: {"player": 360000, FACTION_GHORKOVS: (200, 75, 1000)},
    3: {"player": 460000, FACTION_GHORKOVS: (250, 100, 1000), FACTION_TAERKASTEN: (250, 100, 1000)},
    4: {"player": 600000, FACTION_GHORKOVS: (375, 125, 1000)},
    5: {"player": 640000, FACTION_GHORKOVS: (390, 140, 1000), FACTION_MYKONIANS: (390, 140, 1000)},
    6: {"player": 730000, FACTION_GHORKOVS: (400, 150, 1000), FACTION_BLACK_SECT: (400, 150, 1000)},
    7: {
        "player": 820000,
        FACTION_GHORKOVS: (475, 170, 1000),
        FACTION_TAERKASTEN: (475, 170, 1000),
        FACTION_MYKONIANS: (475, 170, 1000),
        FACTION_SULGOGARS: (475, 170, 1000),
    },
    8: {"player": 870000, FACTION_SULGOGARS: (575, 190, 1000)},
    9: {
        "player": 910000,
        FACTION_SULGOGARS: (700, 210, 1000),
        FACTION_BLACK_SECT: (700, 210, 1000),
        FACTION_MYKONIANS: (700, 210, 1000),
        FACTION_TAERKASTEN: (700, 210, 1000),
    },
    10: {
        "player": 1000000,
        FACTION_GHORKOVS: (800, 210, 1000),
        FACTION_SULGOGARS: (800, 210, 1000),
        FACTION_BLACK_SECT: (800, 210, 1000),
        FACTION_TAERKASTEN: (800, 210, 1000),
    },
    11: {
        "player": 1000000,
        FACTION_GHORKOVS: (1000, 250, 1000),
        FACTION_SULGOGARS: (1000, 250, 1000),
        FACTION_MYKONIANS: (1000, 250, 1000),
        FACTION_BLACK_SECT: (1000, 250, 1000),
        FACTION_TAERKASTEN: (1000, 250, 1000),
    },
    12: {
        "player": 130000000,
        FACTION_SULGOGARS: (150, 300, 1000),
        FACTION_MYKONIANS: (150, 300, 1000),
        FACTION_TAERKASTEN: (150, 300, 1000),
        FACTION_GHORKOVS: (150, 300, 1000),
    },
}

TECH_UPGRADE_BUILDING_TYP_BY_ID = {
    60: 106,
    61: 113,
    4: 100,
    7: 73,
    15: 104,
    51: 101,
    50: 102,
    16: 103,
    65: 110,
}
TECH_UPGRADE_BUILDING_IDS = tuple(TECH_UPGRADE_BUILDING_TYP_BY_ID)
TECH_UPGRADE_BUILDING_IDS_BY_TYPE = {
    1: (15, 51, 60, 61),
    2: (50, 51),
    3: (4, 7, 65),
    4: (16,),
}
TECH_UPGRADE_BUILDING_TILESETS = {
    60: {5},
}
