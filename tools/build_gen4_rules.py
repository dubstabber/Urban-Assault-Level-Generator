#!/usr/bin/env python3
"""Bake campaign-aware Generator4 rules into ``src/ualg/data/gen4_rules.json``."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from ualg.gen4.rules_builder import build_rules, write_rules  # noqa: E402


def main() -> int:
    rules = build_rules(REPO_ROOT)
    path = write_rules(rules)
    count = sum(len(profile["levels"]) for profile in rules["profiles"].values())
    size_kb = path.stat().st_size / 1024
    print(f"Wrote {count} Generator4 rule records to {path} ({size_kb:.0f} KiB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
