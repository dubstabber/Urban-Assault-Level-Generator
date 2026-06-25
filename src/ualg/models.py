"""Public result models."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

MapRows = list[list[int]]


@dataclass(slots=True)
class GeneratedLevel:
    filename: str
    level_id: int
    seed: int
    width: int
    height: int
    tileset: int
    text: str
    maps: dict[str, MapRows] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def write(self, path: str | Path) -> Path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(self.text, encoding="utf-8", newline="")
        return target


@dataclass(slots=True)
class GeneratedCampaign:
    seed: int
    levels: list[GeneratedLevel]
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def write(self, directory: str | Path) -> list[Path]:
        target_dir = Path(directory)
        target_dir.mkdir(parents=True, exist_ok=True)
        written: list[Path] = []
        for level in self.levels:
            written.append(level.write(target_dir / level.filename))
        return written
