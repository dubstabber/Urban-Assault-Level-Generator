from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from ualg.data import gen4_rules
from ualg.gen3.ldf_reader import parse_ldf
from ualg.gen4.passability import route_blockers
from ualg.gen4.rules_builder import build_rules
from ualg.generator4 import Generator4
from ualg.ldf import parse_maps


class RulesTests(unittest.TestCase):
    def test_baked_rules_available(self) -> None:
        rules = gen4_rules()

        self.assertEqual(rules["version"], 1)
        self.assertEqual(len(rules["profiles"]["original"]["levels"]), 44)
        self.assertEqual(len(rules["profiles"]["md-ghorkov"]["levels"]), 16)
        self.assertEqual(len(rules["profiles"]["md-taerkasten"]["levels"]), 15)

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


class GenerationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.generator = Generator4()

    def test_single_is_deterministic(self) -> None:
        a = self.generator.generate_single(seed=12345, campaign_profile="original", level_id=2)
        b = self.generator.generate_single(seed=12345, campaign_profile="original", level_id=2)

        self.assertEqual(a.text, b.text)
        self.assertEqual(a.metadata["generator"], "generator4")
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
