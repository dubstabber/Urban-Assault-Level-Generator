"""Generator1 orchestration service."""

from __future__ import annotations

from time import time

from .context import Generator1CustomOptions, _State
from .map_builder import Generator1MapBuilderMixin
from .profiles import Generator1ProfileMixin
from .renderer import Generator1RendererMixin
from .scenario import Generator1ScenarioMixin
from ..core.maps import filled_rows
from ..constants import (
    GENERATOR1_CAMPAIGN_FILENAMES,
    GENERATOR1_MD_CAMPAIGN_TARGETS_BY_PROFILE,
    level_id_from_filename,
)
from ..models import GeneratedCampaign, GeneratedLevel
from ..rng import MSVCRTRandom


class Generator1(
    Generator1ProfileMixin,
    Generator1ScenarioMixin,
    Generator1MapBuilderMixin,
    Generator1RendererMixin,
):
    """Random UA-derived generator with Godot-improved defaults."""

    campaign_filenames = tuple(GENERATOR1_CAMPAIGN_FILENAMES)

    def generate_single(
        self,
        seed: int = 0,
        difficulty: int = 5,
        skill: int = 0,
        improved: bool = True,
    ) -> GeneratedLevel:
        seed = self._normalize_seed(seed)
        state = _State(rng=MSVCRTRandom(seed), seed=seed, difficulty=difficulty, improved=improved)
        state.scenario_category = self.category_for_skill(skill) if skill else 0
        state.emit_player_enablement = True
        state.gate_target_level_id = 0
        return self._generate(state, "level_01.ldf")

    def generate_campaign(
        self,
        seed: int = 0,
        difficulty: int = 5,
        improved: bool = True,
        campaign_profile: str = "original",
    ) -> GeneratedCampaign:
        campaign_profile = self._normalize_campaign_profile(campaign_profile)
        seed = self._normalize_seed(seed)
        rng = MSVCRTRandom(seed)
        filenames = self._campaign_filenames(campaign_profile)
        player_tech_vehicle_ids = self._player_tech_vehicle_ids(campaign_profile)
        player_tech_building_ids = self._player_tech_building_ids(campaign_profile)
        vehicle_flags = [False] * len(player_tech_vehicle_ids)
        building_flags = [False] * len(player_tech_building_ids)
        if len(vehicle_flags) > 2:
            vehicle_flags[2] = True
        levels: list[GeneratedLevel] = []
        for i, filename in enumerate(filenames):
            state = _State(rng=rng, seed=rng.state, difficulty=difficulty, improved=improved)
            state.level_index = i + 1
            state.level_id = level_id_from_filename(filename)
            self._apply_campaign_profile(state, campaign_profile)
            state.generator1_campaign_mode = True
            state.emit_player_enablement = False
            state.player_tech_vehicle_ids = list(player_tech_vehicle_ids)
            state.player_tech_building_ids = list(player_tech_building_ids)
            state.player_vehicle_flags = vehicle_flags
            state.player_building_flags = building_flags
            state.scenario_category = self.category_for_campaign_index(state.level_index)
            if campaign_profile.startswith("md-"):
                state.gate_target_level_ids = list(
                    GENERATOR1_MD_CAMPAIGN_TARGETS_BY_PROFILE[campaign_profile].get(state.level_id, [])
                )
                state.gate_target_level_id = state.gate_target_level_ids[0] if state.gate_target_level_ids else 0
            elif i + 1 < len(filenames):
                state.gate_target_level_id = level_id_from_filename(filenames[i + 1])
            else:
                state.gate_target_level_id = 0
            levels.append(self._generate(state, filename))
            vehicle_flags = state.player_vehicle_flags
            building_flags = state.player_building_flags
        return GeneratedCampaign(seed=seed, levels=levels)

    def generate_custom(self, options: Generator1CustomOptions) -> GeneratedLevel:
        seed = self._normalize_seed(options.seed)
        state = _State(rng=MSVCRTRandom(seed), seed=seed, difficulty=options.difficulty, improved=options.improved)
        state.emit_player_enablement = True
        self._apply_custom_options(state, options)
        return self._generate(state, "custom_level.ldf", apply_scenario=not self._has_custom_scenario(options))

    @staticmethod
    def _normalize_seed(seed: int) -> int:
        return int(seed) if seed else int(time())

    def _generate(self, state: _State, filename: str, apply_scenario: bool = True) -> GeneratedLevel:
        if apply_scenario:
            self._apply_scenario(state)
        self._assign_player_host_vehicle(state)
        if state.width <= 0 or state.height <= 0:
            self._choose_map_size(state)
        self._generate_height_map(state)
        state.tileset = state.rng.rand_range(1, 6)
        self._init_typ_map(state)
        self._init_own_map(state)
        state.maps["blg"] = filled_rows(state.width, state.height)
        self._place_player_base(state)
        self._place_hosts_and_ambient(state)
        self._seed_superitems(state)
        self._repair_building_ownership(state)
        text = self._write_level(state)
        return GeneratedLevel(
            filename=filename,
            level_id=state.level_id,
            seed=state.seed,
            width=state.width,
            height=state.height,
            tileset=state.tileset,
            text=text,
            maps=state.maps,
            metadata={
                "generator": "generator1",
                "scenario_category": state.scenario_category,
                "player_host": (state.player_host_x, state.player_host_y),
                "base": (state.base_x, state.base_y),
            },
        )
