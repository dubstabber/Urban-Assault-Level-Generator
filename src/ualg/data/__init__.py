"""Packaged Urban Assault reference data."""

from __future__ import annotations

import json
from functools import cache
from importlib import resources
from typing import Any


@cache
def load_json(name: str) -> dict[str, Any]:
    data_ref = resources.files(__name__).joinpath(name)
    return json.loads(data_ref.read_text(encoding="utf-8"))


@cache
def tileset_compatibility() -> dict[int, set[int]]:
    raw = load_json("UA_tileset_compat.json")["sets"]
    return {int(key): {int(value) for value in values} for key, values in raw.items()}


@cache
def ua_data() -> dict[str, Any]:
    return load_json("UAdata.json")
