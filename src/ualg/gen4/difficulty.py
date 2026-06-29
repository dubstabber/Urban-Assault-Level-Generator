"""Generator4 difficulty mode helpers."""

from __future__ import annotations

NORMAL_MODE = "normal"
HARD_MODE = "hard"
EXTREMELY_HARD_MODE = "extremely-hard"

GENERATOR4_DIFFICULTY_MODES = (NORMAL_MODE, HARD_MODE, EXTREMELY_HARD_MODE)

_DIFFICULTY_ALIASES = {
    "": NORMAL_MODE,
    NORMAL_MODE: NORMAL_MODE,
    HARD_MODE: HARD_MODE,
    "extreme": EXTREMELY_HARD_MODE,
    "extreme hard": EXTREMELY_HARD_MODE,
    "extreme-hard": EXTREMELY_HARD_MODE,
    "extremely hard": EXTREMELY_HARD_MODE,
    "extremely-hard": EXTREMELY_HARD_MODE,
    "extremely_hard": EXTREMELY_HARD_MODE,
}


def normalize_difficulty_mode(mode: str | None) -> str:
    normalized = _DIFFICULTY_ALIASES.get((mode or NORMAL_MODE).strip().lower().replace("_", "-"))
    if normalized is None:
        choices = ", ".join(GENERATOR4_DIFFICULTY_MODES)
        raise ValueError(f"Unknown Generator4 difficulty mode {mode!r}. Choose one of: {choices}.")
    return normalized


def is_hard_or_harder(mode: str | None) -> bool:
    return normalize_difficulty_mode(mode) in {HARD_MODE, EXTREMELY_HARD_MODE}


def is_extremely_hard(mode: str | None) -> bool:
    return normalize_difficulty_mode(mode) == EXTREMELY_HARD_MODE
