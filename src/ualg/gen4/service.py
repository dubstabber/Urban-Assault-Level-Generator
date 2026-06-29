"""Generator4 orchestration service."""

from __future__ import annotations

from time import time

from ..campaign_profiles import CampaignProfile, ProfileRegistry
from ..constants import level_filename
from ..models import GeneratedCampaign, GeneratedLevel
from ..rng import MSVCRTRandom
from .builder import Generator4Builder
from .context import _Gen4Level
from .profiles import Generator4ProfileResolver
from .renderer import Generator4Renderer
from .rules import Archetype, archetype_for_level, archetype_for_source_level, archetypes_for_profile
from .validate import validate_level

_MAX_GENERATION_ATTEMPTS = 6


class Generator4:
    """Campaign-aware hybrid synthesis generator."""

    def __init__(self, profile_registry: ProfileRegistry | None = None) -> None:
        self.profiles = Generator4ProfileResolver(profile_registry)
        self.builder = Generator4Builder()
        self.renderer = Generator4Renderer()

    def generate_single(
        self,
        seed: int = 0,
        *,
        campaign_profile: str = "original",
        level_id: int | None = None,
        zero_enemy_radar_budgets: bool = False,
        zero_enemy_station_delays: bool = False,
    ) -> GeneratedLevel:
        profile_id = self.profiles.normalize_campaign_profile(campaign_profile)
        profile = self.profiles.get(profile_id)
        seed = self._normalize_seed(seed)
        rng = MSVCRTRandom(seed)
        archetype = (
            self._archetype_for_profile_level(profile_id, profile, level_id)
            if level_id is not None
            else rng.choice(self._archetypes_for_profile(profile_id, profile))
        )
        return self._generate_level(
            profile_id,
            profile,
            archetype,
            rng,
            seed,
            rewire_targets=False,
            zero_enemy_radar_budgets=zero_enemy_radar_budgets,
            zero_enemy_station_delays=zero_enemy_station_delays,
        )

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
        levels: list[GeneratedLevel] = []
        for level_id in profile.level_ids:
            archetype = self._archetype_for_profile_level(profile_id, profile, level_id)
            levels.append(
                self._generate_level(
                    profile_id,
                    profile,
                    archetype,
                    rng,
                    seed,
                    rewire_targets=True,
                    zero_enemy_radar_budgets=zero_enemy_radar_budgets,
                    zero_enemy_station_delays=zero_enemy_station_delays,
                )
            )
        return GeneratedCampaign(seed=seed, levels=levels)

    def _generate_level(
        self,
        profile_id: str,
        profile: CampaignProfile,
        archetype: Archetype,
        rng: MSVCRTRandom,
        seed: int,
        *,
        rewire_targets: bool,
        zero_enemy_radar_budgets: bool,
        zero_enemy_station_delays: bool,
    ) -> GeneratedLevel:
        last_level: _Gen4Level | None = None
        last_text = ""
        last_warnings: list[str] = []
        for _attempt in range(_MAX_GENERATION_ATTEMPTS):
            level = self._new_level(
                profile_id,
                profile,
                rng,
                seed,
                archetype,
                zero_enemy_radar_budgets,
                zero_enemy_station_delays,
            )
            self.builder.build(level)
            if rewire_targets:
                self._rewire_targets(level, profile)
            text = self.renderer.write(level)
            warnings = validate_level(level, text)
            if not warnings:
                return self._finalize(level, text, warnings)
            last_level, last_text, last_warnings = level, text, warnings
        assert last_level is not None
        return self._finalize(last_level, last_text, last_warnings)

    def _new_level(
        self,
        profile_id: str,
        profile: CampaignProfile,
        rng: MSVCRTRandom,
        seed: int,
        archetype: Archetype,
        zero_enemy_radar_budgets: bool,
        zero_enemy_station_delays: bool,
    ) -> _Gen4Level:
        return _Gen4Level(
            level_id=archetype.level_id,
            rng=rng,
            seed=seed,
            profile_id=profile_id,
            profile=profile,
            player_faction=int(profile.player_faction),
            archetype=archetype,
            zero_enemy_radar_budgets=zero_enemy_radar_budgets,
            zero_enemy_station_delays=zero_enemy_station_delays,
        )

    def _archetypes_for_profile(self, profile_id: str, profile: CampaignProfile) -> tuple[Archetype, ...]:
        try:
            return archetypes_for_profile(profile_id)
        except KeyError:
            return tuple(archetype_for_source_level(self.profiles.source_for(profile), level_id) for level_id in profile.level_ids)

    def _archetype_for_profile_level(self, profile_id: str, profile: CampaignProfile, level_id: int) -> Archetype:
        try:
            return archetype_for_level(profile_id, level_id)
        except KeyError:
            return archetype_for_source_level(self.profiles.source_for(profile), level_id)

    @staticmethod
    def _rewire_targets(level: _Gen4Level, profile: CampaignProfile) -> None:
        targets = list(profile.targets_by_level.get(level.level_id, ()))
        if not targets:
            return
        for gate in level.gates:
            gate["targets"] = list(targets)

    def _finalize(self, level: _Gen4Level, text: str, warnings: list[str]) -> GeneratedLevel:
        metadata = {
            "generator": "generator4",
            "campaign_profile": level.profile_id,
            "source": level.source,
            "level_archetype": level.archetype.name,
            "tech_phase": level.tech_phase,
            "warnings": warnings,
            "synth_method": level.synth_method,
        }
        return GeneratedLevel(
            filename=level_filename(level.level_id),
            level_id=level.level_id,
            seed=level.seed,
            width=level.width,
            height=level.height,
            tileset=level.tileset,
            text=text,
            maps=level.maps,
            metadata=metadata,
        )

    @staticmethod
    def _normalize_seed(seed: int) -> int:
        return int(seed) if seed else int(time())
