"""Public Generator3 entrypoint.

Generator3 is the corpus-driven, authored-style generator. Phase 1 implements
*Remix* mode: it reuses a hand-made original level's terrain, entity positions
and balance numbers, swapping only faction identities, rosters and campaign
wiring according to the selected campaign profile.
"""

from __future__ import annotations

from .gen3.service import Generator3

__all__ = ["Generator3"]
