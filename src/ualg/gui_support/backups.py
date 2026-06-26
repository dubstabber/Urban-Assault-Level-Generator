"""Backup helpers for generated LDF files."""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path


def backup_existing_file(path: str | Path, timestamp: str | None = None) -> Path | None:
    source = Path(path)
    if not source.is_file():
        return None
    stamp = timestamp or _timestamp()
    target = _unique_path(source.with_name(f"{source.name}.bak_{stamp}"))
    shutil.copy2(source, target)
    return target


def backup_campaign_ldfs(directory: str | Path, timestamp: str | None = None) -> tuple[Path | None, list[Path]]:
    source_dir = Path(directory)
    if not source_dir.is_dir():
        return None, []

    ldf_files = sorted(path for path in source_dir.iterdir() if path.is_file() and path.suffix.lower() == ".ldf")
    if not ldf_files:
        return None, []

    stamp = timestamp or _timestamp()
    backup_dir = _unique_path(source_dir / f"Backup_{stamp}")
    backup_dir.mkdir(parents=True, exist_ok=False)
    moved: list[Path] = []
    for source in ldf_files:
        target = backup_dir / source.name
        shutil.move(str(source), str(target))
        moved.append(target)
    return backup_dir, moved


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    for index in range(2, 1000):
        candidate = path.with_name(f"{path.name}_{index}")
        if not candidate.exists():
            return candidate
    raise RuntimeError(f"could not create a unique backup path for {path}")
