"""Generator3: corpus-driven, authored-style level generator.

Generator3 differs from Generator1/Generator2 (both procedural random
scatter) by grounding output in the hand-made original levels shipped under
``original-levels/``. Phase 1 implements *Remix* mode: a real level supplies
the structure (terrain maps, entity positions, balance numbers) and the
campaign profile supplies the content (factions, rosters, gate wiring).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .service import Generator3

__all__ = ["Generator3"]


def __getattr__(name: str) -> Any:
    if name == "Generator3":
        from .service import Generator3

        return Generator3
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
