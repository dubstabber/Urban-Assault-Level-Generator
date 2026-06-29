"""Runtime access to the baked Generator3 skeleton corpus."""

from __future__ import annotations

from dataclasses import dataclass
from functools import cache
from typing import Any

from ..data import gen3_corpus
from ..models import MapRows
from .corpus_builder import build_corpus, write_corpus

# Sector owners that are never treated as a remappable faction.
_NON_FACTION_OWNERS = {0, 7}


@dataclass(frozen=True)
class Skeleton:
    """One parsed original level, ready to be remixed."""

    record: dict[str, Any]

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
    def present_owners(self) -> list[int]:
        return [int(owner) for owner in self.record["present_owners"]]

    @property
    def enemy_owners(self) -> list[int]:
        skip = _NON_FACTION_OWNERS | {self.player_owner}
        return [owner for owner in self.present_owners if owner not in skip]

    def maps(self) -> dict[str, MapRows]:
        """Decode the four hex map blocks into fresh integer rows."""

        return {
            name: [[int(token, 16) for token in row.split()] for row in rows]
            for name, rows in self.record["maps"].items()
        }


def _load_records() -> list[dict[str, Any]]:
    """Load the baked corpus, auto-building it in a source checkout if absent."""

    try:
        return gen3_corpus()["skeletons"]
    except FileNotFoundError:
        corpus = build_corpus()
        try:
            write_corpus(corpus)
        except OSError:
            pass  # read-only install: keep the in-memory corpus only
        return corpus["skeletons"]


@cache
def _skeletons() -> tuple[Skeleton, ...]:
    return tuple(Skeleton(record) for record in _load_records())


def skeletons_for_source(source: str) -> list[Skeleton]:
    """Return skeletons for a corpus source (``vanilla`` / ``metropolisDawn``)."""

    matches = [skeleton for skeleton in _skeletons() if skeleton.source == source]
    if not matches:
        raise ValueError(f"no Generator3 skeletons for source {source!r}")
    return matches


def skeleton_by_name(name: str, source: str | None = None) -> Skeleton | None:
    target = name.strip().upper()
    for skeleton in _skeletons():
        if skeleton.name == target and (source is None or skeleton.source == source):
            return skeleton
    return None
