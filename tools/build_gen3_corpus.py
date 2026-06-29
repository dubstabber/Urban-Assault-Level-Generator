#!/usr/bin/env python3
"""Bake the hand-made original levels into ``src/ualg/data/gen3_corpus.json``.

This file is committed so Generator3 can run from an installed package without
the raw levels. Generator3 also auto-builds it on demand in a source checkout
if the baked file is missing, so running this script is only needed to refresh
the corpus explicitly.

Run from anywhere::

    python tools/build_gen3_corpus.py

Re-run whenever ``original-levels/`` changes.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from ualg.gen3.corpus_builder import build_corpus, write_corpus  # noqa: E402


def main() -> int:
    corpus = build_corpus(REPO_ROOT)
    path = write_corpus(corpus)
    size_kb = path.stat().st_size / 1024
    print(f"Wrote {len(corpus['skeletons'])} skeletons to {path} ({size_kb:.0f} KiB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
