"""Generator3 orchestration service (Phase 1: Remix mode)."""

from __future__ import annotations

from time import time

from ..campaign_profiles import CampaignProfile, ProfileRegistry
from ..constants import level_filename
from ..models import GeneratedCampaign, GeneratedLevel
from ..rng import MSVCRTRandom
from .context import _Gen3Level
from .corpus import Skeleton, skeleton_by_name, skeletons_for_source
from .profiles import Generator3ProfileResolver
from .remix import Generator3RemixBuilder
from .renderer import Generator3Renderer
from .validate import validate_level


class Generator3:
    """Corpus-driven, authored-style level generator (Remix mode)."""

    def __init__(self, profile_registry: ProfileRegistry | None = None) -> None:
        self.profiles = Generator3ProfileResolver(profile_registry)
        self.remix = Generator3RemixBuilder()
        self.renderer = Generator3Renderer()

    def generate_single(
        self,
        seed: int = 0,
        *,
        campaign_profile: str = "original",
        skeleton: str | None = None,
        level_id: int | None = None,
        zero_enemy_radar_budgets: bool = False,
        zero_enemy_station_delays: bool = False,
    ) -> GeneratedLevel:
        profile_id = self.profiles.normalize_campaign_profile(campaign_profile)
        profile = self.profiles.get(profile_id)
        seed = self._normalize_seed(seed)
        rng = MSVCRTRandom(seed)
        source = self.profiles.source_for(profile)
        chosen = self._select_skeleton(rng, source, skeleton, level_id)
        return self._remix(profile_id, profile, chosen, rng, seed, rewire_targets=False,
                           zero_enemy_radar_budgets=zero_enemy_radar_budgets,
                           zero_enemy_station_delays=zero_enemy_station_delays)

    def generate_campaign(
        self,
        seed: int = 0,
        campaign_profile: str = "original",
        *,
        zero_enemy_radar_budgets: bool = False,
        zero_enemy_station_delays: bool = False,
    ) -> GeneratedCampaign:
        profile_id = self.profiles.normalize_campaign_profile(campaign_profile)
        profile = self.profiles.get(profile_id)
        seed = self._normalize_seed(seed)
        rng = MSVCRTRandom(seed)
        source = self.profiles.source_for(profile)
        levels = []
        for level_id in profile.level_ids:
            chosen = skeleton_by_name(level_filename(level_id).split(".")[0], source) or rng.choice(
                skeletons_for_source(source)
            )
            levels.append(
                self._remix(profile_id, profile, chosen, rng, seed, rewire_targets=True,
                            zero_enemy_radar_budgets=zero_enemy_radar_budgets,
                            zero_enemy_station_delays=zero_enemy_station_delays,
                            level_id=level_id)
            )
        return GeneratedCampaign(seed=seed, levels=levels)

    def _select_skeleton(
        self,
        rng: MSVCRTRandom,
        source: str,
        skeleton: str | None,
        level_id: int | None,
    ) -> Skeleton:
        if skeleton:
            found = skeleton_by_name(skeleton, source) or skeleton_by_name(skeleton)
            if found is None:
                raise ValueError(f"unknown Generator3 skeleton: {skeleton!r}")
            return found
        if level_id is not None:
            name = level_filename(level_id).split(".")[0]
            found = skeleton_by_name(name, source)
            if found is None:
                raise ValueError(f"no skeleton for level id {level_id} in {source!r} corpus")
            return found
        return rng.choice(skeletons_for_source(source))

    def _remix(
        self,
        profile_id: str,
        profile: CampaignProfile,
        skeleton: Skeleton,
        rng: MSVCRTRandom,
        seed: int,
        *,
        rewire_targets: bool,
        zero_enemy_radar_budgets: bool,
        zero_enemy_station_delays: bool,
        level_id: int | None = None,
    ) -> GeneratedLevel:
        resolved_level_id = level_id if level_id is not None else _level_id_from_name(skeleton.name)
        level = _Gen3Level(
            level_id=resolved_level_id,
            rng=rng,
            seed=seed,
            profile_id=profile_id,
            profile=profile,
            skeleton=skeleton,
            player_faction=int(profile.player_faction),
            zero_enemy_radar_budgets=zero_enemy_radar_budgets,
            zero_enemy_station_delays=zero_enemy_station_delays,
        )
        self.remix.build(level, self.profiles.enemy_factions(profile))
        if rewire_targets:
            targets = list(profile.targets_by_level.get(resolved_level_id, ()))
            if targets:
                for gate in level.gates:
                    gate["targets"] = list(targets)

        text = self.renderer.write(level)
        warnings = validate_level(level)
        return GeneratedLevel(
            filename=level_filename(resolved_level_id),
            level_id=resolved_level_id,
            seed=seed,
            width=level.width,
            height=level.height,
            tileset=level.tileset,
            text=text,
            maps=level.maps,
            metadata={
                "generator": "generator3",
                "mode": "remix",
                "campaign_profile": profile_id,
                "skeleton": skeleton.name,
                "faction_remap": dict(level.faction_remap),
                "warnings": warnings,
            },
        )

    @staticmethod
    def _normalize_seed(seed: int) -> int:
        return int(seed) if seed else int(time())


def _level_id_from_name(name: str) -> int:
    digits = "".join(ch for ch in name if ch.isdigit())
    return int(digits[:2]) if len(digits) >= 2 else 0
