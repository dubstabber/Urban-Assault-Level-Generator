from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from ualg.constants import (
    TILESET6_BOMB_DIAGONAL_KEY_TYP_BY_OFFSET,
    TYP_BEAM_GATE_NO_ROAD,
    TYP_BEAM_GATE_WITH_ROAD,
    TYP_BOMB_STANDARD,
    TYP_GATE_CLOSED_1,
    TYP_GATE_CLOSED_2,
    TYP_TILESET6_BOMB,
)
from ualg.data import gen4_rules
from ualg.gen3.ldf_reader import parse_ldf
from ualg.gen4.builder import Generator4Builder
from ualg.gen4.infrastructure import station_info_by_building
from ualg.gen4.passability import route_blockers
from ualg.gen4.rules_builder import build_rules
from ualg.generator4 import Generator4
from ualg.ldf import parse_maps

_SCOUT_VEHICLES = {9, 29, 35, 67, 74}


def _world_cell(entity: dict[str, object]) -> tuple[int, int]:
    return (
        round((int(entity["pos_x"]) - 1) / 1200 - 0.5),
        round((-(int(entity["pos_z"]) - 1)) / 1200 - 0.5),
    )


def _station_cells(level) -> list[tuple[int, int, str, int]]:
    info = station_info_by_building()
    cells: list[tuple[int, int, str, int]] = []
    for y, row in enumerate(level.maps["blg"]):
        for x, building in enumerate(row):
            station = info.get(int(building))
            if station is not None:
                cells.append((x, y, station.category, int(level.maps["own"][y][x])))
    return cells


def _min_chebyshev_distance(cells: list[tuple[int, int]]) -> int | None:
    if len(cells) < 2:
        return None
    return min(
        max(abs(ax - bx), abs(ay - by))
        for index, (ax, ay) in enumerate(cells)
        for bx, by in cells[index + 1 :]
    )


class RulesTests(unittest.TestCase):
    def test_baked_rules_available(self) -> None:
        rules = gen4_rules()

        self.assertEqual(rules["version"], 2)
        self.assertEqual(len(rules["profiles"]["original"]["levels"]), 44)
        self.assertEqual(len(rules["profiles"]["md-ghorkov"]["levels"]), 16)
        self.assertEqual(len(rules["profiles"]["md-taerkasten"]["levels"]), 15)
        record = next(r for r in rules["profiles"]["original"]["levels"] if r["level_id"] == 52)
        self.assertIn("terrain_profile", record)
        self.assertIn("infrastructure_profile", record)
        self.assertIn("infrastructure_placements", record)

    def test_rules_builder_is_deterministic(self) -> None:
        built = build_rules(ROOT)
        baked = gen4_rules()

        self.assertEqual(
            json.dumps(built, sort_keys=True, separators=(",", ":")),
            json.dumps(baked, sort_keys=True, separators=(",", ":")),
        )

    def test_known_first_unlocks_extracted(self) -> None:
        expected = {
            ("original", 2): [("vehicle", 2)],
            ("original", 3): [("vehicle", 1)],
            ("original", 4): [("vehicle", 6)],
            ("original", 5): [("vehicle", 9)],
            ("original", 12): [("vehicle", 15)],
            ("original", 20): [("vehicle", 3)],
            ("original", 21): [("building", 63)],
            ("original", 30): [("building", 28)],
            ("original", 31): [("vehicle", 10)],
            ("original", 40): [("vehicle", 14)],
            ("original", 41): [("building", 1), ("vehicle", 4)],
            ("original", 42): [("vehicle", 5)],
            ("original", 43): [("vehicle", 134)],
            ("original", 52): [("building", 3)],
            ("original", 53): [("vehicle", 7)],
            ("original", 54): [("vehicle", 12)],
            ("original", 62): [("vehicle", 11), ("building", 54)],
            ("original", 63): [("building", 2), ("building", 11)],
            ("original", 70): [("building", 64)],
            ("md-ghorkov", 7): [("vehicle", 29)],
            ("md-ghorkov", 14): [("vehicle", 28)],
            ("md-ghorkov", 17): [("vehicle", 22)],
            ("md-ghorkov", 19): [("building", 52)],
            ("md-ghorkov", 28): [("vehicle", 26)],
            ("md-ghorkov", 35): [("vehicle", 23)],
            ("md-ghorkov", 37): [("vehicle", 25)],
            ("md-ghorkov", 39): [("building", 12)],
            ("md-ghorkov", 46): [("vehicle", 130)],
            ("md-ghorkov", 48): [("building", 30)],
            ("md-ghorkov", 56): [("vehicle", 27)],
            ("md-ghorkov", 58): [("vehicle", 31)],
            ("md-ghorkov", 67): [("building", 71)],
            ("md-taerkasten", 6): [("vehicle", 35)],
            ("md-taerkasten", 8): [("vehicle", 33)],
            ("md-taerkasten", 13): [("vehicle", 38)],
            ("md-taerkasten", 16): [("vehicle", 37)],
            ("md-taerkasten", 18): [("vehicle", 144)],
            ("md-taerkasten", 29): [("building", 53)],
            ("md-taerkasten", 36): [("building", 74)],
            ("md-taerkasten", 38): [("vehicle", 131)],
            ("md-taerkasten", 45): [("building", 73)],
            ("md-taerkasten", 47): [("vehicle", 36)],
            ("md-taerkasten", 55): [("vehicle", 143), ("building", 17)],
            ("md-taerkasten", 65): [("vehicle", 34)],
            ("md-taerkasten", 68): [("vehicle", 8)],
        }
        rules = gen4_rules()

        for (profile, level_id), unlocks in expected.items():
            with self.subTest(profile=profile, level_id=level_id):
                record = next(r for r in rules["profiles"][profile]["levels"] if r["level_id"] == level_id)
                self.assertEqual([(u["kind"], u["id"]) for u in record["new_unlocks"]], unlocks)

    def test_station_building_categories_are_known(self) -> None:
        categories = {building: info.category for building, info in station_info_by_building().items()}

        self.assertEqual(categories[63], "power")
        self.assertEqual(categories[30], "flak")
        self.assertEqual(categories[73], "radar")

    def test_infrastructure_profiles_extracted_for_station_heavy_levels(self) -> None:
        rules = gen4_rules()
        expected = [
            ("original", 15),
            ("original", 52),
            ("original", 63),
            ("md-ghorkov", 79),
            ("md-taerkasten", 78),
        ]

        for profile, level_id in expected:
            with self.subTest(profile=profile, level_id=level_id):
                record = next(r for r in rules["profiles"][profile]["levels"] if r["level_id"] == level_id)
                counts = record["infrastructure_profile"]["counts"]
                self.assertGreater(counts["power"], 0)
                self.assertGreater(counts["flak"], 0)
                self.assertGreater(counts["radar"], 0)
                self.assertEqual(sum(counts.values()), len(record["infrastructure_placements"]))

    def test_terrain_profiles_classify_flat_and_varied_levels(self) -> None:
        rules = gen4_rules()

        for level_id in (3, 25, 26):
            with self.subTest(level_id=level_id):
                record = next(r for r in rules["profiles"]["original"]["levels"] if r["level_id"] == level_id)
                self.assertLessEqual(record["terrain_profile"]["range"], 1)
                self.assertLessEqual(record["terrain_profile"]["unique_count"], 2)

        for level_id in (52, 63, 61, 51, 62):
            with self.subTest(level_id=level_id):
                record = next(r for r in rules["profiles"]["original"]["levels"] if r["level_id"] == level_id)
                self.assertGreaterEqual(record["terrain_profile"]["range"], 10)
                self.assertGreaterEqual(record["terrain_profile"]["unique_count"], 10)


class GenerationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.generator = Generator4()

    def test_single_is_deterministic(self) -> None:
        a = self.generator.generate_single(seed=12345, campaign_profile="original", level_id=2)
        b = self.generator.generate_single(seed=12345, campaign_profile="original", level_id=2)

        self.assertEqual(a.text, b.text)
        self.assertEqual(a.metadata["generator"], "generator4")
        self.assertEqual(a.metadata["rules_version"], 2)
        self.assertEqual(a.metadata["level_archetype"], "L0202")
        self.assertEqual(a.metadata["warnings"], [])

    def test_seed_changes_output(self) -> None:
        a = self.generator.generate_single(seed=1, campaign_profile="original", level_id=2)
        b = self.generator.generate_single(seed=2, campaign_profile="original", level_id=2)

        self.assertNotEqual(a.text, b.text)

    def test_maps_round_trip(self) -> None:
        level = self.generator.generate_single(seed=2026, campaign_profile="original", level_id=2)
        parsed = parse_maps(level.text)

        self.assertEqual(set(parsed), {"typ_map", "own_map", "hgt_map", "blg_map"})
        for _name, (width, height, rows) in parsed.items():
            self.assertEqual((width, height), (level.width, level.height))
            self.assertEqual(len(rows), height)

    def test_enemy_enables_are_source_subsets_and_squads_are_legal(self) -> None:
        level = self.generator.generate_single(seed=7, campaign_profile="md-taerkasten", level_id=78)
        parsed = parse_ldf(level.text)
        rules = gen4_rules()
        record = next(r for r in rules["profiles"]["md-taerkasten"]["levels"] if r["level_id"] == 78)
        source = {
            int(owner): {
                "vehicles": set(data["vehicles"]),
                "buildings": set(data["buildings"]),
            }
            for owner, data in record["enemy_enables"].items()
        }
        legal = {int(enable["owner"]): set(enable["vehicles"]) for enable in parsed.enables}
        player = int(self.generator.profiles.get("md-taerkasten").player_faction)

        for enable in parsed.enables:
            owner = int(enable["owner"])
            if owner == player:
                continue
            self.assertLessEqual(set(enable["vehicles"]), source[owner]["vehicles"])
            self.assertLessEqual(set(enable["buildings"]), source[owner]["buildings"])
        for squad in parsed.squads:
            owner = int(squad["owner"])
            if owner in {0, 7, player}:
                continue
            self.assertIn(int(squad["vehicle"]), legal[owner])

    def test_campaigns_valid_for_all_profiles(self) -> None:
        for profile in ("original", "md-ghorkov", "md-taerkasten"):
            with self.subTest(profile=profile):
                campaign = self.generator.generate_campaign(seed=2026, campaign_profile=profile)
                self.assertTrue(campaign.ok)
                self.assertTrue(campaign.levels)
                self.assertTrue(all(level.metadata["warnings"] == [] for level in campaign.levels))

    def test_infrastructure_generated_for_station_archetypes(self) -> None:
        level = self.generator.generate_single(seed=2026, campaign_profile="original", level_id=15)
        counts = level.metadata["infrastructure_profile"]["generated_counts"]

        self.assertGreater(counts["power"], 0)
        self.assertGreater(counts["flak"], 0)
        self.assertGreater(counts["radar"], 0)

    def test_nonflat_archetype_generates_varied_terrain(self) -> None:
        level = self.generator.generate_single(seed=2026, campaign_profile="original", level_id=52)
        terrain = level.metadata["terrain_profile"]

        self.assertGreaterEqual(terrain["generated_unique_heights"], terrain["source_unique_heights"] // 2)
        self.assertGreaterEqual(terrain["generated_height_range"], terrain["source_height_range"] // 2)

    def test_station_heavy_map_counts_are_capped_and_scattered(self) -> None:
        level = self.generator.generate_single(seed=2026, campaign_profile="md-ghorkov", level_id=79)
        counts = level.metadata["infrastructure_profile"]["generated_counts"]
        cells = _station_cells(level)

        self.assertLessEqual(counts["power"], 8)
        self.assertLessEqual(counts["flak"], 24)
        self.assertGreaterEqual(_min_chebyshev_distance([(x, y) for x, y, category, _owner in cells if category == "flak"]), 4)
        self.assertGreaterEqual(_min_chebyshev_distance([(x, y) for x, y, category, _owner in cells if category == "power"]), 3)

    def test_bomb_defense_level_gives_player_flak_without_overfilling_power(self) -> None:
        level = self.generator.generate_single(seed=2026, campaign_profile="original", level_id=52)
        cells = _station_cells(level)

        player_flak = [(x, y) for x, y, category, owner in cells if category == "flak" and owner == 1]
        self.assertGreaterEqual(len(player_flak), 3)
        self.assertLessEqual(level.metadata["infrastructure_profile"]["generated_counts"]["power"], 5)

    def test_enemy_radar_is_away_from_owner_base(self) -> None:
        level = self.generator.generate_single(seed=2026, campaign_profile="md-taerkasten", level_id=78)
        parsed = parse_ldf(level.text)
        hosts_by_owner: dict[int, list[tuple[int, int]]] = {}
        for robo in parsed.robos:
            hosts_by_owner.setdefault(int(robo["owner"]), []).append(_world_cell(robo))

        player = int(self.generator.profiles.get("md-taerkasten").player_faction)
        for x, y, category, owner in _station_cells(level):
            if category != "radar" or owner == player:
                continue
            nearest = min(abs(x - hx) + abs(y - hy) for hx, hy in hosts_by_owner[owner])
            self.assertGreaterEqual(nearest, 6)

    def test_enemy_scout_radar_unit_spawns_near_player_base_when_legal(self) -> None:
        level = self.generator.generate_single(seed=2026, campaign_profile="original", level_id=2)
        parsed = parse_ldf(level.text)
        player = next(robo for robo in parsed.robos if "con_budget" not in robo)
        px, py = _world_cell(player)

        scout_distances = [
            abs(_world_cell(squad)[0] - px) + abs(_world_cell(squad)[1] - py)
            for squad in parsed.squads
            if int(squad["owner"]) != 1 and int(squad["vehicle"]) in _SCOUT_VEHICLES
        ]
        self.assertTrue(scout_distances)
        self.assertLessEqual(min(scout_distances), 5)

    def test_hard_mode_reduces_player_territory_and_starting_stations(self) -> None:
        normal = self.generator.generate_single(seed=2026, campaign_profile="original", level_id=52)
        hard = self.generator.generate_single(seed=2026, campaign_profile="original", level_id=52, difficulty_mode="hard")

        normal_player_cells = sum(1 for row in normal.maps["own"] for owner in row if int(owner) == 1)
        hard_player_cells = sum(1 for row in hard.maps["own"] for owner in row if int(owner) == 1)
        hard_hosts = {_world_cell(robo) for robo in parse_ldf(hard.text).robos}
        hard_stations = _station_cells(hard)
        player_power = [
            (x, y)
            for x, y, category, owner in hard_stations
            if category == "power" and owner == 1 and (x, y) not in hard_hosts
        ]
        player_flak = [(x, y) for x, y, category, owner in hard_stations if category == "flak" and owner == 1]

        self.assertEqual(hard.metadata["difficulty_mode"], "hard")
        self.assertLess(hard_player_cells, normal_player_cells)
        self.assertLessEqual(hard_player_cells, 8)
        self.assertEqual(player_power, [])
        self.assertLessEqual(len(player_flak), 1)

    def test_hard_mode_raises_enemy_host_energy(self) -> None:
        normal = parse_ldf(self.generator.generate_single(seed=2026, campaign_profile="original", level_id=2).text)
        hard = parse_ldf(
            self.generator.generate_single(seed=2026, campaign_profile="original", level_id=2, difficulty_mode="hard").text
        )

        normal_enemy_energy = [int(robo["energy"]) for robo in normal.robos if int(robo["owner"]) != 1]
        hard_enemy_energy = [int(robo["energy"]) for robo in hard.robos if int(robo["owner"]) != 1]

        self.assertEqual(len(hard_enemy_energy), len(normal_enemy_energy))
        for hard_energy, normal_energy in zip(hard_enemy_energy, normal_enemy_energy, strict=True):
            self.assertGreaterEqual(hard_energy, normal_energy)
            self.assertGreaterEqual(hard_energy, 800000)

    def test_extremely_hard_lowers_player_energy_and_expands_enemy_enables(self) -> None:
        normal = parse_ldf(self.generator.generate_single(seed=2026, campaign_profile="original", level_id=2).text)
        extreme_level = self.generator.generate_single(
            seed=2026,
            campaign_profile="original",
            level_id=2,
            difficulty_mode="extremely-hard",
        )
        extreme = parse_ldf(extreme_level.text)

        normal_player = next(robo for robo in normal.robos if int(robo["owner"]) == 1)
        extreme_player = next(robo for robo in extreme.robos if int(robo["owner"]) == 1)
        normal_enemy_enable_count = sum(len(enable.get("vehicles", [])) for enable in normal.enables if int(enable["owner"]) != 1)
        extreme_enemy_enable_count = sum(len(enable.get("vehicles", [])) for enable in extreme.enables if int(enable["owner"]) != 1)

        self.assertEqual(extreme_level.metadata["difficulty_mode"], "extremely-hard")
        self.assertLess(int(extreme_player["energy"]), int(normal_player["energy"]))
        self.assertGreater(extreme_enemy_enable_count, normal_enemy_enable_count)

    def test_extremely_hard_can_add_extra_enemy_host_station(self) -> None:
        normal = parse_ldf(self.generator.generate_single(seed=3, campaign_profile="original", level_id=2).text)
        extreme = parse_ldf(
            self.generator.generate_single(
                seed=3,
                campaign_profile="original",
                level_id=2,
                difficulty_mode="extremely-hard",
            ).text
        )

        self.assertGreater(len(extreme.robos), len(normal.robos))
        self.assertGreater(
            sum(1 for robo in extreme.robos if int(robo["owner"]) != 1),
            sum(1 for robo in normal.robos if int(robo["owner"]) != 1),
        )

    def test_campaign_rewires_gate_targets(self) -> None:
        campaign = self.generator.generate_campaign(seed=5, campaign_profile="md-ghorkov")
        profile = self.generator.profiles.get("md-ghorkov")
        level7 = next(level for level in campaign.levels if level.level_id == 7)

        for target in profile.targets_by_level[7]:
            self.assertIn(f"target_level\t=\t{target}", level7.text)

    def test_zero_options_apply_to_enemy_hosts(self) -> None:
        level = self.generator.generate_single(
            seed=2026,
            campaign_profile="original",
            level_id=2,
            zero_enemy_radar_budgets=True,
            zero_enemy_station_delays=True,
        )
        parsed = parse_ldf(level.text)

        for robo in parsed.robos:
            if "con_budget" not in robo:
                self.assertNotIn("rad_budget", robo)
                continue
            self.assertEqual(robo.get("rad_budget"), 0)
            for key, value in robo.items():
                if key.endswith("_delay"):
                    self.assertEqual(value, 0)

    def test_unknown_profile_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.generator.generate_single(seed=1, campaign_profile="nope")


class MapOverrideTests(unittest.TestCase):
    def test_beam_gate_keysecs_do_not_force_typ_map(self) -> None:
        level = SimpleNamespace(gates=[{"sec_x": 2, "sec_y": 2, "keysecs": [{"x": 1, "y": 1}]}])
        typ = [[0 for _ in range(4)] for _ in range(4)]
        blg = [[0 for _ in range(4)] for _ in range(4)]

        Generator4Builder()._apply_gate_tiles(level, typ, blg)

        self.assertEqual(typ[2][2], TYP_BEAM_GATE_WITH_ROAD)
        self.assertEqual(typ[1][1], 0)

    def test_beam_gate_blueprints_choose_matching_typ_map_cells(self) -> None:
        level = SimpleNamespace(
            gates=[
                {"sec_x": 1, "sec_y": 1, "closed_bp": 25, "opened_bp": 26, "keysecs": []},
                {"sec_x": 2, "sec_y": 2, "closed_bp": 5, "opened_bp": 6, "keysecs": []},
            ]
        )
        typ = [[0 for _ in range(4)] for _ in range(4)]
        blg = [[0 for _ in range(4)] for _ in range(4)]

        Generator4Builder()._apply_gate_tiles(level, typ, blg)

        self.assertEqual(typ[1][1], TYP_BEAM_GATE_NO_ROAD)
        self.assertEqual(typ[2][2], TYP_BEAM_GATE_WITH_ROAD)

    def test_standard_bomb_blueprints_use_245(self) -> None:
        level = SimpleNamespace(
            source="vanilla",
            items=[
                {
                    "sec_x": 2,
                    "sec_y": 2,
                    "inactive_bp": 35,
                    "active_bp": 36,
                    "trigger_bp": 37,
                    "keysecs": [],
                }
            ]
        )
        typ = [[0 for _ in range(4)] for _ in range(4)]
        blg = [[0 for _ in range(4)] for _ in range(4)]

        Generator4Builder()._apply_item_tiles(level, typ, blg)

        self.assertEqual(typ[2][2], TYP_BOMB_STANDARD)
        self.assertEqual(blg[2][2], 35)

    def test_tileset6_bomb_blueprints_use_235_and_diagonal_keysec_tiles(self) -> None:
        level = SimpleNamespace(
            source="vanilla",
            tileset=6,
            width=7,
            height=7,
            items=[
                {
                    "sec_x": 3,
                    "sec_y": 3,
                    "inactive_bp": 68,
                    "active_bp": 69,
                    "trigger_bp": 70,
                    "keysecs": [
                        {"x": 2, "y": 2},
                        {"x": 4, "y": 2},
                        {"x": 2, "y": 4},
                        {"x": 4, "y": 4},
                        {"x": 5, "y": 5},
                    ],
                }
            ],
        )
        typ = [[0 for _ in range(7)] for _ in range(7)]
        blg = [[0 for _ in range(7)] for _ in range(7)]

        Generator4Builder()._apply_item_tiles(level, typ, blg)

        self.assertEqual(typ[3][3], TYP_TILESET6_BOMB)
        self.assertEqual(blg[3][3], 68)
        for (dx, dy), expected in TILESET6_BOMB_DIAGONAL_KEY_TYP_BY_OFFSET.items():
            self.assertEqual(typ[3 + dy][3 + dx], expected)
            self.assertEqual(blg[3 + dy][3 + dx], 0)
        self.assertEqual(typ[5][5], TYP_GATE_CLOSED_2)

    def test_tileset6_bomb_without_diagonal_keysecs_does_not_stamp_corner_tiles(self) -> None:
        level = SimpleNamespace(
            source="vanilla",
            tileset=6,
            width=7,
            height=7,
            items=[
                {
                    "sec_x": 3,
                    "sec_y": 3,
                    "inactive_bp": 68,
                    "active_bp": 69,
                    "trigger_bp": 70,
                    "keysecs": [],
                }
            ],
        )
        typ = [[0 for _ in range(7)] for _ in range(7)]
        blg = [[0 for _ in range(7)] for _ in range(7)]

        Generator4Builder()._apply_item_tiles(level, typ, blg)

        self.assertEqual(typ[3][3], TYP_TILESET6_BOMB)
        for dx, dy in TILESET6_BOMB_DIAGONAL_KEY_TYP_BY_OFFSET:
            self.assertEqual(typ[3 + dy][3 + dx], 0)

    def test_upgrade_gem_building_ids_choose_matching_typ_map_cells(self) -> None:
        expected = {
            60: 106,
            61: 113,
            4: 100,
            7: 73,
            15: 104,
            51: 101,
            50: 102,
            16: 103,
            65: 110,
        }

        for building, typ_value in expected.items():
            with self.subTest(building=building):
                level = SimpleNamespace(
                    tileset=5,
                    gems=[["begin_gem", "sec_x = 2", "sec_y = 2", f"building = {building}", "end"]],
                )
                typ = [[0 for _ in range(4)] for _ in range(4)]
                blg = [[0 for _ in range(4)] for _ in range(4)]

                Generator4Builder()._apply_gem_tiles(level, typ, blg)

                self.assertEqual(typ[2][2], typ_value)
                self.assertEqual(blg[2][2], building)

    def test_bomb_keysecs_without_four_road_edges_use_243(self) -> None:
        level = SimpleNamespace(
            source="vanilla",
            items=[
                {
                    "sec_x": 2,
                    "sec_y": 2,
                    "inactive_bp": 35,
                    "active_bp": 36,
                    "trigger_bp": 37,
                    "keysecs": [{"x": 1, "y": 1}],
                }
            ]
        )
        typ = [[0 for _ in range(4)] for _ in range(4)]
        blg = [[0 for _ in range(4)] for _ in range(4)]

        Generator4Builder()._apply_item_tiles(level, typ, blg)

        self.assertEqual(blg[2][2], 35)
        self.assertEqual(typ[1][1], TYP_GATE_CLOSED_2)

    def test_bomb_keysecs_with_four_road_edges_use_244(self) -> None:
        level = SimpleNamespace(
            source="vanilla",
            items=[
                {
                    "sec_x": 3,
                    "sec_y": 3,
                    "inactive_bp": 35,
                    "active_bp": 36,
                    "trigger_bp": 37,
                    "keysecs": [{"x": 2, "y": 2}],
                }
            ]
        )
        typ = [[0 for _ in range(5)] for _ in range(5)]
        blg = [[0 for _ in range(5)] for _ in range(5)]
        typ[1][2] = 7
        typ[2][3] = 18
        typ[3][2] = 166
        typ[2][1] = 18

        Generator4Builder()._apply_item_tiles(level, typ, blg)

        self.assertEqual(typ[2][2], TYP_GATE_CLOSED_1)


class PassabilityTests(unittest.TestCase):
    def test_required_route_rejects_height_barrier(self) -> None:
        rows = [
            [0x7F, 0x88, 0x7F],
            [0x7F, 0x88, 0x7F],
            [0x7F, 0x88, 0x7F],
        ]

        self.assertTrue(route_blockers(rows, [(0, 1), (2, 1)]))

    def test_decorative_cliffs_outside_route_are_accepted(self) -> None:
        rows = [
            [0x7F, 0x7F, 0x88],
            [0x7F, 0x7F, 0x88],
            [0x7F, 0x7F, 0x88],
        ]

        self.assertEqual(route_blockers(rows, [(0, 0), (1, 2)]), [])


if __name__ == "__main__":
    unittest.main()
