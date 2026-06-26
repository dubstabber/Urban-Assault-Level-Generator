"""Generator2 orchestration service."""

from __future__ import annotations

from time import time

from .context import _Level
from .map_builder import Generator2MapBuilderMixin
from .placement import Generator2PlacementMixin
from .profiles import Generator2ProfileMixin
from .renderer import Generator2RendererMixin
from ..constants import GENERATOR2_CAMPAIGN_LEVEL_IDS, GENERATOR2_LEVELS, level_filename
from ..models import GeneratedCampaign, GeneratedLevel
from ..rng import MSVCRTRandom


class Generator2(
    Generator2ProfileMixin,
    Generator2PlacementMixin,
    Generator2MapBuilderMixin,
    Generator2RendererMixin,
):
    """PHP Generator2 implementation."""

    campaign_level_ids = tuple(GENERATOR2_CAMPAIGN_LEVEL_IDS)

    def generate_single(self, seed: int = 0, level_id: int = 1) -> GeneratedLevel:
        if level_id not in GENERATOR2_LEVELS:
            raise ValueError(f"unknown Generator2 level id: {level_id}")
        seed = self._normalize_seed(seed)
        rng = MSVCRTRandom(seed)
        return self._generate_level(level_id, rng, seed)

    def generate_campaign(self, seed: int = 0, campaign_profile: str = "original") -> GeneratedCampaign:
        campaign_profile = self._normalize_campaign_profile(campaign_profile)
        seed = self._normalize_seed(seed)
        rng = MSVCRTRandom(seed)
        levels = [
            self._generate_level(level_id, rng, seed, campaign_profile=campaign_profile)
            for level_id in self._campaign_level_ids(campaign_profile)
        ]
        return GeneratedCampaign(seed=seed, levels=levels)

    def _generate_level(
        self,
        level_id: int,
        rng: MSVCRTRandom,
        seed: int,
        *,
        campaign_profile: str = "original",
    ) -> GeneratedLevel:
        level = _Level(level_id=level_id, rng=rng, seed=seed)
        self._apply_campaign_profile(level, campaign_profile)
        self._choose_map_size(level)
        level.tileset = rng.rand_range(1, 6)
        self._create_gate(level)
        self._create_player_station(level)
        self._create_enemy_stations(level)
        self._create_bombs(level)
        self._create_squads(level)
        for map_type in ("typ", "own", "hgt", "blg"):
            self._make_map(level, map_type)
        self._apply_special_map_rules(level)
        text = self._write_level(level)
        return GeneratedLevel(
            filename=level_filename(level_id),
            level_id=level_id,
            seed=seed,
            width=level.width,
            height=level.height,
            tileset=level.tileset,
            text=text,
            maps=level.maps,
            metadata={"generator": "generator2", "campaign_profile": campaign_profile},
        )

    @staticmethod
    def _normalize_seed(seed: int) -> int:
        return int(seed) if seed else int(time())
