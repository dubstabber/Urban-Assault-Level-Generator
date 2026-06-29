"""Light playability checks for remixed levels.

Based on the failure modes listed in the Levelbuilder troubleshooting section
(intact energy-wall border, host/squad limits, valid host coordinates).
"""

from __future__ import annotations

from .context import _Gen3Level

_MAX_HOSTS = 7
_MAX_SQUADS = 100
_MAX_SQUAD_UNITS = 32

_BORDER_CORNERS = {
    "top_left": 0xF8,
    "top_right": 0xF9,
    "bottom_left": 0xFB,
    "bottom_right": 0xFA,
}


def validate_level(level: _Gen3Level) -> list[str]:
    problems: list[str] = []

    rows = level.maps.get("typ", [])
    if rows:
        if rows[0][0] != _BORDER_CORNERS["top_left"] or rows[0][-1] != _BORDER_CORNERS["top_right"]:
            problems.append("typ_map top border corner altered")
        if rows[-1][0] != _BORDER_CORNERS["bottom_left"] or rows[-1][-1] != _BORDER_CORNERS["bottom_right"]:
            problems.append("typ_map bottom border corner altered")

    if not level.robos:
        problems.append("level has no host stations")
    if len(level.robos) > _MAX_HOSTS:
        problems.append(f"{len(level.robos)} host stations exceeds limit of {_MAX_HOSTS}")
    for robo in level.robos:
        if robo.get("pos_x") is None or robo.get("pos_y") is None or robo.get("pos_z") is None:
            problems.append("host station missing world coordinates")
            break

    if len(level.squads) > _MAX_SQUADS:
        problems.append(f"{len(level.squads)} squads exceeds limit of {_MAX_SQUADS}")
    for squad in level.squads:
        if int(squad.get("num", 0)) > _MAX_SQUAD_UNITS:
            problems.append("squad exceeds 32 units")
            break

    return problems
