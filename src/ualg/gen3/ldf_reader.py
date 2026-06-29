"""Structured reader for hand-made Urban Assault LDF level files.

``ldf.parse_maps`` already extracts the four map blocks from generated text.
This module adds a full block reader for the *gameplay* structure of authored
levels (header, beam gates, host stations, predefined squads, bombs, upgrade
sectors, prototype enables) so the corpus builder can bake the originals into
a reusable dataset.

The grammar is line oriented. Block openers are:

* ``begin_<name>`` -- closed by ``end``
* ``begin_action`` -- closed by ``end_action``
* ``modify_vehicle`` / ``modify_weapon`` / ``modify_building`` -- closed by ``end``

``begin_gem`` may nest a ``begin_action`` body which in turn nests
``modify_*`` blocks. Those bodies are preserved verbatim rather than fully
modelled, because Remix re-emits them unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..ldf import parse_maps
from ..models import MapRows

# Keys in begin_level worth preserving when re-emitting a remixed header.
HEADER_KEYS = (
    "set",
    "sky",
    "title_default",
    "title_deutsch",
    "title_english",
    "ambiencetrack",
    "event_loop",
    "movie",
    "win_movie",
    "lose_movie",
)

# Block openers that are closed by a plain ``end``.
_END_OPENERS = {
    "begin_level",
    "begin_mbmap",
    "begin_dbmap",
    "begin_gate",
    "begin_robo",
    "begin_item",
    "begin_squad",
    "begin_enable",
    "begin_gem",
    "begin_maps",
    "modify_vehicle",
    "modify_weapon",
    "modify_building",
}


@dataclass
class ParsedLevel:
    """Structured view of one authored level."""

    name: str = ""
    source: str = ""
    tileset: int = 1
    width: int = 0
    height: int = 0
    player_owner: int = 1
    header: dict[str, Any] = field(default_factory=dict)
    mbmap: dict[str, Any] = field(default_factory=dict)
    dbmap: dict[str, Any] = field(default_factory=dict)
    gates: list[dict[str, Any]] = field(default_factory=list)
    robos: list[dict[str, Any]] = field(default_factory=list)
    items: list[dict[str, Any]] = field(default_factory=list)
    squads: list[dict[str, Any]] = field(default_factory=list)
    enables: list[dict[str, Any]] = field(default_factory=list)
    gems: list[dict[str, Any]] = field(default_factory=list)
    prototype: list[str] = field(default_factory=list)
    maps: dict[str, MapRows] = field(default_factory=dict)
    present_owners: list[int] = field(default_factory=list)


def _coerce(value: str) -> Any:
    # Drop trailing ``; inline comment`` then normalise whitespace. Only plain
    # decimal integers become ints -- Python's int() would otherwise read
    # underscore-separated tokens like ``4_00_20000`` as a number.
    text = value.split(";", 1)[0].strip()
    digits = text[1:] if text.startswith("-") else text
    if digits.isdigit():
        return int(text)
    return text


def _head(stripped: str) -> str:
    return stripped.split(None, 1)[0].lower() if stripped else ""


def _arg(stripped: str) -> str:
    parts = stripped.split(None, 1)
    return parts[1].strip() if len(parts) > 1 else ""


def _split_kv(stripped: str) -> tuple[str, Any] | None:
    """Parse ``key = value`` (tabs or spaces). Returns ``None`` for flag lines."""

    if "=" not in stripped:
        return None
    key, _, value = stripped.partition("=")
    return key.strip().lower(), _coerce(value)


def _read_kv_block(lines: list[str], start: int) -> tuple[list[tuple[str, Any]], list[str], int]:
    """Read ``key = value`` pairs until the closing ``end``.

    Returns the ordered pairs (repeats preserved), any bare flag tokens, and
    the index just past the ``end`` line.
    """

    pairs: list[tuple[str, Any]] = []
    flags: list[str] = []
    i = start
    n = len(lines)
    while i < n:
        stripped = lines[i].strip()
        i += 1
        if not stripped or stripped.startswith(";"):
            continue
        low = stripped.lower()
        if low == "end":
            break
        kv = _split_kv(stripped)
        if kv is None:
            flags.append(low.split(None, 1)[0])
        else:
            pairs.append(kv)
    return pairs, flags, i


def _read_raw_block(lines: list[str], start: int) -> tuple[list[str], int]:
    """Capture a balanced block verbatim (comments dropped), opener included."""

    collected = [lines[start].strip()]
    stack = [_head(lines[start].strip())]
    i = start + 1
    n = len(lines)
    while i < n and stack:
        stripped = lines[i].strip()
        i += 1
        if not stripped or stripped.startswith(";"):
            continue
        collected.append(stripped)
        head = _head(stripped)
        if head == "begin_action" or head in _END_OPENERS:
            stack.append(head)
        elif head == "end_action":
            while stack and stack[-1] != "begin_action":
                stack.pop()
            if stack:
                stack.pop()
        elif head == "end":
            stack.pop()
    return collected, i


def _first(pairs: list[tuple[str, Any]], key: str, default: Any = None) -> Any:
    for found_key, value in pairs:
        if found_key == key:
            return value
    return default


def _all(pairs: list[tuple[str, Any]], key: str) -> list[Any]:
    return [value for found_key, value in pairs if found_key == key]


def _keysec_pairs(pairs: list[tuple[str, Any]]) -> list[dict[str, int]]:
    keys: list[dict[str, int]] = []
    pending_x: int | None = None
    for key, value in pairs:
        if key == "keysec_x":
            pending_x = int(value)
        elif key == "keysec_y" and pending_x is not None:
            keys.append({"x": pending_x, "y": int(value)})
            pending_x = None
    return keys


def parse_ldf(text: str, *, name: str = "", source: str = "") -> ParsedLevel:
    """Parse decoded (UTF-8) LDF text into a :class:`ParsedLevel`."""

    lines = text.split("\n")
    level = ParsedLevel(name=name, source=source)
    i = 0
    n = len(lines)
    while i < n:
        stripped = lines[i].strip()
        if not stripped or stripped.startswith(";"):
            i += 1
            continue
        head = _head(stripped)
        if head == "begin_level":
            pairs, _flags, i = _read_kv_block(lines, i + 1)
            level.header = {key: _first(pairs, key) for key in HEADER_KEYS if _first(pairs, key) is not None}
            level.tileset = int(level.header.get("set", 1) or 1)
        elif head == "begin_mbmap":
            pairs, _flags, i = _read_kv_block(lines, i + 1)
            level.mbmap = {key: _first(pairs, key) for key in ("name", "size_x", "size_y") if _first(pairs, key) is not None}
        elif head == "begin_dbmap":
            pairs, _flags, i = _read_kv_block(lines, i + 1)
            level.dbmap = {key: _first(pairs, key) for key in ("name", "size_x", "size_y") if _first(pairs, key) is not None}
        elif head == "begin_gate":
            pairs, _flags, i = _read_kv_block(lines, i + 1)
            level.gates.append(
                {
                    "sec_x": _first(pairs, "sec_x"),
                    "sec_y": _first(pairs, "sec_y"),
                    "closed_bp": _first(pairs, "closed_bp", 5),
                    "opened_bp": _first(pairs, "opened_bp", 6),
                    "targets": [int(value) for value in _all(pairs, "target_level")],
                    "keysecs": _keysec_pairs(pairs),
                    "mb_status": _first(pairs, "mb_status"),
                }
            )
        elif head == "begin_robo":
            pairs, _flags, i = _read_kv_block(lines, i + 1)
            level.robos.append({key: value for key, value in pairs})
        elif head == "begin_item":
            pairs, _flags, i = _read_kv_block(lines, i + 1)
            item = {key: value for key, value in pairs if key not in ("keysec_x", "keysec_y")}
            item["keysecs"] = _keysec_pairs(pairs)
            level.items.append(item)
        elif head == "begin_squad":
            pairs, flags, i = _read_kv_block(lines, i + 1)
            squad = {key: value for key, value in pairs}
            squad["useable"] = "useable" in flags
            level.squads.append(squad)
        elif head == "begin_enable":
            owner = _coerce(_arg(stripped))
            pairs, _flags, i = _read_kv_block(lines, i + 1)
            level.enables.append(
                {
                    "owner": owner,
                    "vehicles": [int(value) for value in _all(pairs, "vehicle")],
                    "buildings": [int(value) for value in _all(pairs, "building")],
                }
            )
        elif head == "begin_gem":
            raw, end = _read_raw_block(lines, i)
            # Pull the simple scalar fields out of the verbatim body for placement.
            gem: dict[str, Any] = {"raw": raw}
            for line in raw[1:]:
                kv = _split_kv(line)
                if kv and kv[0] in ("sec_x", "sec_y", "building", "type"):
                    gem.setdefault(kv[0], kv[1])
            level.gems.append(gem)
            i = end
        elif head == "begin_maps":
            _raw, i = _read_raw_block(lines, i)
        elif head == "include":
            level.prototype.append(stripped)
            i += 1
        elif head in ("modify_vehicle", "modify_weapon", "modify_building"):
            raw, i = _read_raw_block(lines, i)
            level.prototype.extend(raw)
        else:
            i += 1

    parsed_maps = parse_maps(text)
    for map_name in ("typ_map", "own_map", "hgt_map", "blg_map"):
        if map_name in parsed_maps:
            width, height, rows = parsed_maps[map_name]
            level.maps[map_name[:3]] = rows
            level.width, level.height = width, height

    level.player_owner = _detect_player_owner(level)
    level.present_owners = _collect_owners(level)
    return level


# Host-station vehicle ids that identify the human player's robo across both
# data profiles (Resistance/Black-Sect style "host station" units).
_PLAYER_HOST_VEHICLE_IDS = {56, 60, 62, 176, 177, 178, 179}


def _detect_player_owner(level: ParsedLevel) -> int:
    for robo in level.robos:
        vehicle = robo.get("vehicle")
        owner = robo.get("owner")
        if owner is None:
            continue
        # A robo with no AI budget keys is the human player's host station.
        if vehicle in _PLAYER_HOST_VEHICLE_IDS and "con_budget" not in robo:
            return int(owner)
    for robo in level.robos:
        if "con_budget" not in robo and robo.get("owner") is not None:
            return int(robo["owner"])
    return 1


def _collect_owners(level: ParsedLevel) -> list[int]:
    owners: set[int] = set()
    for robo in level.robos:
        if robo.get("owner") is not None:
            owners.add(int(robo["owner"]))
    for squad in level.squads:
        if squad.get("owner") is not None:
            owners.add(int(squad["owner"]))
    own_rows = level.maps.get("own", [])
    for row in own_rows:
        owners.update(int(value) for value in row)
    return sorted(owners)
