"""Generator1 map generation and entity placement."""

from __future__ import annotations

from .context import _State
from ..core.maps import filled_rows
from ..constants import (
    BLG_PLAYER_BASE,
    BLG_SUPERITEM,
    BUILDING_TYP_BY_ID,
    FACTION_PLAYER,
    HOST_BUILDING_BY_FACTION,
    TYP_BORDER_BOTTOM,
    TYP_BORDER_BOTTOM_LEFT,
    TYP_BORDER_BOTTOM_RIGHT,
    TYP_BORDER_LEFT,
    TYP_BORDER_RIGHT,
    TYP_BORDER_TOP,
    TYP_BORDER_TOP_LEFT,
    TYP_BORDER_TOP_RIGHT,
    TYP_GATE_CLOSED_1,
    TYP_GATE_CLOSED_2,
    TYP_MAP_INTERIOR_LOOKUP,
    TYP_PLAYER_BASE,
    TYP_SUPERITEM,
    sector_to_world_x,
    sector_to_world_z,
)
from ..data import tileset_compatibility


class Generator1MapBuilderMixin:
    def _choose_map_size(self, state: _State) -> None:
        state.width = state.rng.rand_range(state.min_width, state.max_width)
        state.height = state.rng.rand_range(state.min_height, state.max_height)

    def _generate_height_map(self, state: _State) -> None:
        rows = filled_rows(state.width, state.height, 128)
        for x in range(1, state.width):
            rows[0][x] = max(4, min(247, rows[0][x - 1] + state.rng.rand_variation(4)))
        for y in range(1, state.height):
            rows[y][0] = max(4, min(247, rows[y - 1][0] + state.rng.rand_variation(4)))
        for y in range(1, state.height):
            for x in range(1, state.width):
                up = rows[y - 1][x]
                left = rows[y][x - 1]
                lo = min(up, left) + 4
                hi = max(up, left) - 4
                rows[y][x] = max(4, min(247, state.rng.rand_range(hi, lo)))
        state.maps["hgt"] = rows

    def _init_typ_map(self, state: _State) -> None:
        compat = tileset_compatibility()[state.tileset] if state.improved else set(TYP_MAP_INTERIOR_LOOKUP)
        candidates = [value for value in TYP_MAP_INTERIOR_LOOKUP if value in compat] or TYP_MAP_INTERIOR_LOOKUP
        rows = filled_rows(state.width, state.height)
        for y in range(1, state.height - 1):
            for x in range(1, state.width - 1):
                rows[y][x] = state.rng.choice(candidates)
        for x in range(state.width):
            rows[0][x] = TYP_BORDER_TOP
            rows[state.height - 1][x] = TYP_BORDER_BOTTOM
        for y in range(state.height):
            rows[y][0] = TYP_BORDER_LEFT
            rows[y][state.width - 1] = TYP_BORDER_RIGHT
        rows[0][0] = TYP_BORDER_TOP_LEFT
        rows[0][state.width - 1] = TYP_BORDER_TOP_RIGHT
        rows[state.height - 1][0] = TYP_BORDER_BOTTOM_LEFT
        rows[state.height - 1][state.width - 1] = TYP_BORDER_BOTTOM_RIGHT
        state.maps["typ"] = rows

    def _init_own_map(self, state: _State) -> None:
        owners = [0, state.player_faction] + [
            faction for faction in self._enemy_factions(state) if state.faction_enables[faction]
        ]
        rows = filled_rows(state.width, state.height)
        for y in range(1, state.height - 1):
            for x in range(1, state.width - 1):
                rows[y][x] = state.rng.choice(owners)
        state.maps["own"] = rows

    def _place_player_base(self, state: _State) -> None:
        x = state.rng.rand_range(1, state.width - 2)
        y = state.rng.rand_range(1, state.height - 2)
        state.base_x, state.base_y = x, y
        state.set("typ", x, y, TYP_PLAYER_BASE)
        state.set("blg", x, y, BLG_PLAYER_BASE)
        state.set("own", x, y, state.player_faction)
        self._reserve_sector(state, x, y)

    def _place_hosts_and_ambient(self, state: _State) -> None:
        self._place_player_host(state)
        for faction in self._enemy_factions(state):
            for slot in range(3):
                if state.ai_slot_present[faction][slot]:
                    self._place_ai_host(state, faction, slot)
        density = 0.4 + min(0.6, state.difficulty * 0.06)
        attempts = int((state.width * state.height) * density / 18)
        for _ in range(max(1, min(10, attempts))):
            sector = self._find_empty_sector(state)
            if not sector:
                continue
            x, y = sector
            owner = self._pick_present_faction(state)
            candidates = state.buildings_by_faction.get(owner) or []
            if not candidates:
                continue
            building = state.rng.choice(candidates)
            state.set("blg", x, y, building)
            state.set("typ", x, y, BUILDING_TYP_BY_ID.get(building, state.get("typ", x, y)))
            state.set("own", x, y, owner)
            self._reserve_sector(state, x, y)

    def _place_player_host(self, state: _State) -> None:
        x, y = self._find_empty_sector(state) or (state.base_x, state.base_y)
        state.player_host_x, state.player_host_y = x, y
        if state.force_player_base_model:
            building = 64
        else:
            building = state.rng.choice(HOST_BUILDING_BY_FACTION.get(state.player_faction, HOST_BUILDING_BY_FACTION[FACTION_PLAYER]))
        self._write_host_cell(state, x, y, state.player_faction, building)

    def _place_ai_host(self, state: _State, faction: int, slot: int) -> None:
        sector = self._find_empty_sector(state, avoid=(state.base_x, state.base_y))
        if not sector:
            return
        x, y = sector
        building = state.rng.choice(HOST_BUILDING_BY_FACTION.get(faction, [12]))
        self._write_host_cell(state, x, y, faction, building)
        state.ai_slot_world[faction][slot] = (sector_to_world_x(x), sector_to_world_z(y))

    def _write_host_cell(self, state: _State, x: int, y: int, owner: int, building: int) -> None:
        state.set("blg", x, y, building)
        state.set("typ", x, y, BUILDING_TYP_BY_ID.get(building, 201))
        state.set("own", x, y, owner)
        self._reserve_sector(state, x, y)

    def _find_empty_sector(self, state: _State, avoid: tuple[int, int] | None = None) -> tuple[int, int] | None:
        max_attempts = max(10, state.width_interior * state.height_interior * 3)
        for _ in range(max_attempts):
            x = state.rng.rand_range(1, state.width - 2)
            y = state.rng.rand_range(1, state.height - 2)
            if avoid and (x, y) == avoid:
                continue
            if self._sector_is_available(state, x, y):
                return x, y
        for y in range(1, state.height - 1):
            for x in range(1, state.width - 1):
                if (not avoid or (x, y) != avoid) and self._sector_is_available(state, x, y):
                    return x, y
        return None

    @staticmethod
    def _reserve_sector(state: _State, x: int, y: int) -> None:
        state.reserved_sectors.add((x, y))

    @staticmethod
    def _sector_is_available(state: _State, x: int, y: int) -> bool:
        return state.interior(x, y) and state.get("blg", x, y) == 0 and (x, y) not in state.reserved_sectors

    def _pick_present_faction(self, state: _State) -> int:
        factions = [state.player_faction] + [
            faction for faction in self._enemy_factions(state) if state.faction_enables[faction]
        ]
        return state.rng.choice(factions)

    def _seed_superitems(self, state: _State) -> None:
        for index, enabled in enumerate(state.superitem_flags, start=1):
            if not enabled:
                continue
            sector = self._find_empty_sector(state)
            if not sector:
                continue
            x, y = sector
            state.set("typ", x, y, TYP_SUPERITEM)
            state.set("blg", x, y, BLG_SUPERITEM)
            self._reserve_sector(state, x, y)
            countdown = self._superitem_countdown(state, index)
            keys = self._superitem_keys(state, index)
            state.superitems.append({"x": x, "y": y, "countdown": countdown, "keys": keys})

    def _superitem_countdown(self, state: _State, index: int) -> int:
        if index in state.superitem_countdown_overrides:
            return state.superitem_countdown_overrides[index]
        if index == 1:
            value = state.rng.rand_mod(900) * 1000
            value = max(value, 180000)
            if state.difficulty > 5:
                value = max(value, 420000)
            return value
        value = state.rng.rand_mod(2700) * 1000
        value = max(value, 600000)
        if state.difficulty > 6:
            value = max(value, 1200000)
        return value

    def _superitem_keys(self, state: _State, item_index: int) -> list[tuple[int, int]]:
        if item_index == 2 and state.last_superitem_key_count:
            key_count = state.last_superitem_key_count
        else:
            key_count = min(16, self._normalize_superitem_key_count(1 + state.rng.rand_mod(63)))
            state.last_superitem_key_count = key_count
        keys: list[tuple[int, int]] = []
        attempts = max(key_count * 4, state.width_interior * state.height_interior)
        while len(keys) < key_count and attempts > 0:
            attempts -= 1
            sector = self._find_empty_sector(state)
            if not sector:
                break
            x, y = sector
            keys.append((x, y))
            self._mark_stoudson_key_sector(state, x, y)
            self._reserve_sector(state, x, y)
        return keys

    def _mark_stoudson_key_sector(self, state: _State, x: int, y: int) -> None:
        state.set("typ", x, y, TYP_GATE_CLOSED_1 if state.rng.rand_mod(2) else TYP_GATE_CLOSED_2)

    def _seed_beam_gate_keys(self, state: _State) -> None:
        if state.gate_keys:
            return
        key_count = self._gate_key_count(state)
        for _ in range(key_count):
            sector = self._find_empty_sector(state, avoid=(state.base_x, state.base_y))
            if not sector:
                break
            x, y = sector
            state.gate_keys.append((x, y))
            self._reserve_sector(state, x, y)

    def _gate_key_count(self, state: _State) -> int:
        if state.gate_key_count_override is not None:
            return min(state.width_interior * state.height_interior, state.gate_key_count_override)
        area = state.width_interior * state.height_interior
        if area < 17:
            return min(2, area)
        return min(16, self._normalize_superitem_key_count(1 + state.rng.rand_mod(63)))

    @staticmethod
    def _normalize_superitem_key_count(prelim: int) -> int:
        for limit, value in ((2, 15), (3, 14), (5, 13), (7, 12), (10, 11), (13, 10), (17, 9),
                             (21, 8), (26, 7), (31, 6), (37, 5), (44, 4), (52, 3)):
            if prelim <= limit:
                return value
        return 2

    def _repair_building_ownership(self, state: _State) -> None:
        for y in range(1, state.height - 1):
            for x in range(1, state.width - 1):
                if state.get("blg", x, y) and state.get("own", x, y) in (0, 7):
                    state.set("own", x, y, self._pick_present_faction(state))
