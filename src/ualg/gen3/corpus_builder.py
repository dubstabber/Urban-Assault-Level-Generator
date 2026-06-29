"""Build the Generator3 skeleton corpus from the raw ``original-levels/`` tree.

The baked ``gen3_corpus.json`` is *not* committed (it is derived from the
game's original level files, which are themselves gitignored). Instead it is a
local build artifact: ``tools/build_gen3_corpus.py`` writes it explicitly, and
:func:`ualg.gen3.corpus` auto-builds it on demand in a source checkout.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .ldf_reader import ParsedLevel, parse_ldf

# src/ualg/gen3/corpus_builder.py -> repo root is three levels up from src/ualg.
_PACKAGE_ROOT = Path(__file__).resolve().parent.parent
_REPO_ROOT = _PACKAGE_ROOT.parent.parent
CORPUS_FILENAME = "gen3_corpus.json"
OUTPUT_PATH = _PACKAGE_ROOT / "data" / CORPUS_FILENAME

_CORPORA = {
    "vanilla": "LEVELS-vanilla",
    "metropolisDawn": "LEVELS-metropolis-dawn",
}


def original_levels_dir(repo_root: Path | None = None) -> Path:
    return (repo_root or _REPO_ROOT) / "original-levels"


def _rows_to_hex(rows: list[list[int]]) -> list[str]:
    return [" ".join(f"{value & 0xFF:02x}" for value in row) for row in rows]


def _level_record(level: ParsedLevel) -> dict[str, Any]:
    return {
        "name": level.name,
        "source": level.source,
        "tileset": level.tileset,
        "width": level.width,
        "height": level.height,
        "player_owner": level.player_owner,
        "present_owners": level.present_owners,
        "header": level.header,
        "mbmap": level.mbmap,
        "dbmap": level.dbmap,
        "gates": level.gates,
        "robos": level.robos,
        "items": level.items,
        "squads": level.squads,
        "enables": level.enables,
        "gems": level.gems,
        "prototype": level.prototype,
        "maps": {name: _rows_to_hex(rows) for name, rows in level.maps.items()},
    }


def build_corpus(repo_root: Path | None = None) -> dict[str, Any]:
    """Parse every original level into a corpus mapping."""

    levels_dir = original_levels_dir(repo_root)
    if not levels_dir.is_dir():
        raise FileNotFoundError(
            f"original-levels directory not found at {levels_dir}. "
            f"Generator3 needs the raw levels to build {CORPUS_FILENAME}."
        )

    skeletons: list[dict[str, Any]] = []
    for source, subdir in _CORPORA.items():
        directory = levels_dir / subdir
        if not directory.is_dir():
            continue
        for path in sorted(p for p in directory.iterdir() if p.suffix.lower() == ".ldf"):
            text = path.read_text(encoding="latin-1").replace("\r\n", "\n").replace("\r", "\n")
            level = parse_ldf(text, name=path.stem.upper(), source=source)
            if "typ" in level.maps:
                skeletons.append(_level_record(level))
    if not skeletons:
        raise FileNotFoundError(f"no original levels parsed under {levels_dir}.")
    return {"version": 1, "skeletons": skeletons}


def write_corpus(corpus: dict[str, Any], output: Path | None = None) -> Path:
    target = output or OUTPUT_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(corpus, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return target
