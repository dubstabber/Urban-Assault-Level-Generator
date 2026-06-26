"""Tk-free workflow helpers for the desktop GUI."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

from ..generator1 import Generator1, Generator1CustomOptions
from ..generator2 import Generator2
from ..models import GeneratedCampaign, GeneratedLevel
from .backups import backup_campaign_ldfs, backup_existing_file


@dataclass(slots=True)
class LevelGenerationResult:
    level: GeneratedLevel
    written: Path
    backup_path: Path | None = None


@dataclass(slots=True)
class CampaignGenerationResult:
    campaign: GeneratedCampaign
    written: list[Path]
    directory: Path
    campaign_profile: str
    backup_dir: Path | None = None
    moved: list[Path] = field(default_factory=list)


@dataclass(slots=True)
class BackupCreationResult:
    created: list[Path]


def generate_generator1_single(
    target: str | Path,
    *,
    seed: int,
    difficulty: int,
    skill: int,
    improved: bool,
) -> LevelGenerationResult:
    target_path = Path(target)
    backup_path = backup_existing_file(target_path)
    level = Generator1().generate_single(seed=seed, difficulty=difficulty, skill=skill, improved=improved)
    written = level.write(target_path)
    return LevelGenerationResult(level=level, written=written, backup_path=backup_path)


def generate_generator1_custom(target: str | Path, options: Generator1CustomOptions) -> LevelGenerationResult:
    target_path = Path(target)
    backup_path = backup_existing_file(target_path)
    level = Generator1().generate_custom(options)
    written = level.write(target_path)
    return LevelGenerationResult(level=level, written=written, backup_path=backup_path)


def generate_generator1_campaign(
    directory: str | Path,
    *,
    seed: int,
    campaign_profile: str,
) -> CampaignGenerationResult:
    target_dir = Path(directory)
    backup_dir, moved = backup_campaign_ldfs(target_dir)
    campaign = Generator1().generate_campaign(
        seed=seed,
        difficulty=5,
        improved=True,
        campaign_profile=campaign_profile,
    )
    written = campaign.write(target_dir)
    return CampaignGenerationResult(
        campaign=campaign,
        written=written,
        directory=target_dir,
        campaign_profile=campaign_profile,
        backup_dir=backup_dir,
        moved=moved,
    )


def generate_generator2_single(
    target: str | Path,
    *,
    seed: int,
    level_id: int,
    zero_enemy_station_delays: bool = False,
) -> LevelGenerationResult:
    target_path = Path(target)
    backup_path = backup_existing_file(target_path)
    level = Generator2().generate_single(
        seed=seed,
        level_id=level_id,
        zero_enemy_station_delays=zero_enemy_station_delays,
    )
    written = level.write(target_path)
    return LevelGenerationResult(level=level, written=written, backup_path=backup_path)


def generate_generator2_campaign(
    directory: str | Path,
    *,
    seed: int,
    campaign_profile: str,
    zero_enemy_station_delays: bool = False,
) -> CampaignGenerationResult:
    target_dir = Path(directory)
    backup_dir, moved = backup_campaign_ldfs(target_dir)
    campaign = Generator2().generate_campaign(
        seed=seed,
        campaign_profile=campaign_profile,
        zero_enemy_station_delays=zero_enemy_station_delays,
    )
    written = campaign.write(target_dir)
    return CampaignGenerationResult(
        campaign=campaign,
        written=written,
        directory=target_dir,
        campaign_profile=campaign_profile,
        backup_dir=backup_dir,
        moved=moved,
    )


def create_configured_backups(
    level_paths: Iterable[str | Path],
    campaign_directories: Iterable[str | Path],
) -> BackupCreationResult:
    created: list[Path] = []
    seen_files: set[Path] = set()
    for raw_path in level_paths:
        path = _configured_file_path(raw_path)
        if path is None or path in seen_files:
            continue
        seen_files.add(path)
        backup_path = backup_existing_file(path)
        if backup_path is not None:
            created.append(backup_path)

    seen_dirs: set[Path] = set()
    for raw_directory in campaign_directories:
        directory = _configured_directory_path(raw_directory)
        if directory is None or directory in seen_dirs:
            continue
        seen_dirs.add(directory)
        backup_dir, moved = backup_campaign_ldfs(directory)
        if backup_dir is not None:
            created.append(backup_dir)
            created.extend(moved)

    return BackupCreationResult(created=created)


def _configured_file_path(raw_path: str | Path) -> Path | None:
    if isinstance(raw_path, str) and not raw_path.strip():
        return None
    return Path(raw_path)


def _configured_directory_path(raw_directory: str | Path) -> Path | None:
    if isinstance(raw_directory, str):
        directory_text = raw_directory.strip()
        if not directory_text:
            return None
        return Path(directory_text)
    return Path(raw_directory)
