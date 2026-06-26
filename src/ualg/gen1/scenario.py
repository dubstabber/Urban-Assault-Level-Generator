"""Generator1 scenario and custom-option setup."""

from __future__ import annotations

from .context import Generator1CustomOptions, _State
from .tables import CATEGORY_DIM_RANGES, CATEGORY_ENERGY_PARAMS
from ..constants import (
    FACTION_BLACK_SECT,
    FACTION_GHORKOVS,
    FACTION_MYKONIANS,
    FACTION_PLAYER,
    FACTION_SULGOGARS,
    FACTION_TAERKASTEN,
    FACTION_TUTOR,
)


class Generator1ScenarioPlanner:
    @staticmethod
    def category_for_skill(skill: int) -> int:
        return max(1, min(11, int(skill)))

    @staticmethod
    def category_for_campaign_index(level_index: int) -> int:
        if level_index <= 2:
            return 1
        if level_index <= 8:
            return 2
        if level_index <= 11:
            return 3
        if level_index <= 15:
            return 4
        if level_index <= 20:
            return 5
        if level_index <= 25:
            return 6
        if level_index <= 29:
            return 7
        if level_index == 30:
            return 8
        if level_index <= 36:
            return 9
        if level_index <= 42:
            return 10
        if level_index == 43:
            return 11
        if level_index == 44:
            return 12
        return 1

    def _apply_custom_options(self, state: _State, options: Generator1CustomOptions) -> None:
        state.faction_enables[state.player_faction] = True
        state.gate_target_level_id = max(0, int(options.gate_target_level_id))
        state.gate_key_count_override = _clamp_optional(options.gate_key_count, 0, 16)
        state.win_movie = bool(options.win_movie)
        state.lose_movie = bool(options.lose_movie)
        state.superitem_countdown_overrides = {
            int(index): max(0, int(value))
            for index, value in options.superitem_countdowns.items()
            if int(index) in (1, 2)
        }
        state.forced_enabled_vehicles = {
            int(faction): list(dict.fromkeys(int(vehicle) for vehicle in vehicles))
            for faction, vehicles in options.enabled_vehicles.items()
        }
        state.forced_enabled_buildings = {
            int(faction): list(dict.fromkeys(int(building) for building in buildings))
            for faction, buildings in options.enabled_buildings.items()
        }

        if options.width is not None and options.height is not None:
            state.width = max(4, min(45, int(options.width)))
            state.height = max(3, min(32, int(options.height)))
            state.min_width = state.max_width = state.width
            state.min_height = state.max_height = state.height

        if options.player_energy is not None:
            state.player_energy = max(1, int(options.player_energy))

        if options.superitem_flags is not None:
            flags = list(options.superitem_flags[:2])
            state.superitem_flags = (flags + [False, False])[:2]
        elif options.random_superitems:
            count = state.rng.rand_mod(3)
            state.superitem_flags = [index < count for index in range(2)]

        for faction, present_slots in options.ai_slot_present.items():
            faction = int(faction)
            if not 0 <= faction < len(state.ai_slot_present):
                continue
            any_present = False
            for slot, present in enumerate(present_slots[:3]):
                state.ai_slot_present[faction][slot] = bool(present)
                any_present = any_present or bool(present)
            if any_present:
                state.faction_enables[faction] = True

        for faction, energy_slots in options.ai_slot_energy.items():
            faction = int(faction)
            if not 0 <= faction < len(state.ai_slot_energy):
                continue
            for slot, energy in enumerate(energy_slots[:3]):
                if energy:
                    state.ai_slot_energy[faction][slot] = max(1, int(energy))

        for faction, vehicle_id in options.ai_host_vehicle_id.items():
            faction = int(faction)
            if 0 <= faction < len(state.ai_host_vehicle_id):
                state.ai_host_vehicle_id[faction] = int(vehicle_id)

        for faction, vehicle_slots in options.ai_slot_host_vehicle_id.items():
            faction = int(faction)
            if not 0 <= faction < len(state.ai_slot_host_vehicle_id):
                continue
            for slot, vehicle_id in enumerate(vehicle_slots[:3]):
                if vehicle_id:
                    state.ai_slot_host_vehicle_id[faction][slot] = int(vehicle_id)

    @staticmethod
    def _has_custom_scenario(options: Generator1CustomOptions) -> bool:
        return bool(
            options.ai_slot_present
            or options.ai_slot_energy
            or options.player_energy is not None
            or options.superitem_flags is not None
            or options.random_superitems
        )

    def _apply_scenario(self, state: _State) -> None:
        state.faction_enables[state.player_faction] = True
        if state.scenario_category:
            self._apply_category(state)
            return

        if state.difficulty <= 2:
            state.min_width, state.max_width, state.min_height, state.max_height = 8, 10, 8, 10
            state.player_energy = 400000
            self._set_presence_slots(state, FACTION_SULGOGARS, 1)
            chances = (0.10, 0.0)
        elif state.difficulty <= 5:
            state.min_width, state.max_width, state.min_height, state.max_height = 10, 14, 10, 14
            state.player_energy = 500000
            for faction in (FACTION_SULGOGARS, FACTION_MYKONIANS, FACTION_TAERKASTEN):
                self._set_presence_slots(state, faction, 1)
            chances = (0.30, 0.10)
        elif state.difficulty <= 8:
            state.min_width, state.max_width, state.min_height, state.max_height = 12, 18, 12, 18
            state.player_energy = 600000
            for faction in (FACTION_SULGOGARS, FACTION_MYKONIANS, FACTION_TAERKASTEN, FACTION_BLACK_SECT, FACTION_GHORKOVS):
                self._set_presence_slots(state, faction, 1)
            chances = (0.50, 0.30)
        else:
            state.min_width, state.max_width, state.min_height, state.max_height = 14, 20, 14, 20
            state.player_energy = 800000
            for faction in (FACTION_SULGOGARS, FACTION_MYKONIANS, FACTION_TAERKASTEN, FACTION_BLACK_SECT, FACTION_GHORKOVS):
                self._set_presence_slots(state, faction, 1)
            chances = (0.70, 0.50)
        state.superitem_flags[0] = state.rng.rand_float() < chances[0]
        state.superitem_flags[1] = state.rng.rand_float() < chances[1]

    def apply_custom_options(self, state: _State, options: Generator1CustomOptions) -> None:
        self._apply_custom_options(state, options)

    def has_custom_scenario(self, options: Generator1CustomOptions) -> bool:
        return self._has_custom_scenario(options)

    def apply_scenario(self, state: _State) -> None:
        self._apply_scenario(state)

    def _apply_category(self, state: _State) -> None:
        category = max(1, min(12, state.scenario_category))
        state.scenario_category = category
        state.faction_enables = [False] * 8
        state.faction_enables[state.player_faction] = True
        state.superitem_flags = [False, False]
        match category:
            case 1:
                self._set_presence_slots(state, FACTION_TUTOR, 3)
            case 2:
                self._set_presence_slots(state, FACTION_GHORKOVS, 1)
            case 3:
                self._set_presence_slots(state, FACTION_GHORKOVS, 1)
                self._set_presence_slots(state, FACTION_TAERKASTEN, 1)
            case 4:
                self._set_presence_slots(state, FACTION_GHORKOVS, 2)
                state.superitem_flags[0] = True
            case 5:
                self._set_presence_slots(state, FACTION_GHORKOVS, 1)
                self._set_presence_slots(state, FACTION_MYKONIANS, 1)
                state.superitem_flags[0] = True
            case 6:
                self._set_presence_slots(state, FACTION_GHORKOVS, 2)
                self._set_presence_slots(state, FACTION_BLACK_SECT, 1)
            case 7:
                for faction in (FACTION_SULGOGARS, FACTION_MYKONIANS, FACTION_TAERKASTEN, FACTION_GHORKOVS):
                    self._set_presence_slots(state, faction, 1)
            case 8:
                self._set_presence_slots(state, FACTION_SULGOGARS, 3)
            case 9:
                for faction in (FACTION_SULGOGARS, FACTION_BLACK_SECT, FACTION_MYKONIANS, FACTION_TAERKASTEN):
                    self._set_presence_slots(state, faction, 1)
                state.superitem_flags[0] = True
            case 10:
                self._set_presence_slots(state, FACTION_GHORKOVS, 2)
                for faction in (FACTION_SULGOGARS, FACTION_BLACK_SECT, FACTION_TAERKASTEN):
                    self._set_presence_slots(state, faction, 1)
                state.superitem_flags[0] = True
            case 11:
                for faction in (FACTION_GHORKOVS, FACTION_SULGOGARS, FACTION_MYKONIANS, FACTION_TAERKASTEN):
                    self._set_presence_slots(state, faction, 1)
                self._set_presence_slots(state, FACTION_BLACK_SECT, 2)
                state.superitem_flags = [True, True]
                state.win_movie = True
                state.lose_movie = True
            case 12:
                for faction in (FACTION_GHORKOVS, FACTION_SULGOGARS, FACTION_MYKONIANS, FACTION_TAERKASTEN):
                    self._set_presence_slots(state, faction, 1)
                state.force_player_base_model = True
        state.min_width, state.max_width, state.min_height, state.max_height = CATEGORY_DIM_RANGES[category]
        state.player_energy = int(CATEGORY_ENERGY_PARAMS[category]["player"])
        self._assign_slot_energies(state)
        ghorkov_enemy = self._enemy_faction(state, FACTION_GHORKOVS)
        if ghorkov_enemy == FACTION_GHORKOVS:
            if category in (2, 3, 4):
                state.ai_host_vehicle_id[ghorkov_enemy] = 59
            elif category in (5, 6, 7, 10, 11, 12):
                state.ai_host_vehicle_id[ghorkov_enemy] = 57

    def _set_presence_slots(self, state: _State, faction: int, count: int) -> None:
        faction = self._enemy_faction(state, faction)
        state.faction_enables[faction] = True
        for slot in range(max(0, min(3, count))):
            state.ai_slot_present[faction][slot] = True

    def _assign_slot_energies(self, state: _State) -> None:
        params = CATEGORY_ENERGY_PARAMS.get(state.scenario_category, {})
        for source_faction in range(1, 8):
            if source_faction not in params:
                continue
            faction = self._enemy_faction(state, source_faction)
            if faction == state.player_faction:
                continue
            base_k, range_k, scale = params[source_faction]
            for slot in range(3):
                if state.ai_slot_present[faction][slot]:
                    state.ai_slot_energy[faction][slot] = scale * (state.rng.rand_mod(range_k) + base_k)

    @staticmethod
    def _enemy_faction(state: _State, faction: int) -> int:
        if faction == state.player_faction and state.player_faction != FACTION_PLAYER:
            return FACTION_PLAYER
        return faction

    @staticmethod
    def _enemy_factions(state: _State) -> list[int]:
        return [faction for faction in range(1, 8) if faction != state.player_faction]

    def enemy_faction(self, state: _State, faction: int) -> int:
        return self._enemy_faction(state, faction)

    def enemy_factions(self, state: _State) -> list[int]:
        return self._enemy_factions(state)


def _clamp_optional(value: int | None, minimum: int, maximum: int) -> int | None:
    if value is None:
        return None
    return max(minimum, min(maximum, int(value)))
