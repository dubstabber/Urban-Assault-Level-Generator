from __future__ import annotations

import subprocess
import sys
import unittest
import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from ualg.constants import (
    BUILDINGS_BY_FACTION,
    FACTION_BLACK_SECT,
    FACTION_PLAYER,
    FACTION_GHORKOVS,
    FACTION_MYKONIANS,
    FACTION_SULGOGARS,
    FACTION_TAERKASTEN,
    FACTION_TUTOR,
    GENERATOR1_CAMPAIGN_FILENAMES,
    GENERATOR1_MD_CAMPAIGN_LEVEL_IDS_BY_PROFILE,
    GENERATOR1_MD_CAMPAIGN_TARGETS_BY_PROFILE,
    GENERATOR2_CAMPAIGN_LEVEL_IDS,
    GENERATOR2_MD_CAMPAIGN_LEVEL_IDS_BY_PROFILE,
    GENERATOR2_MD_CAMPAIGN_TARGETS_BY_PROFILE,
    GENERATOR2_SET_LIST,
    VEHICLES_BY_FACTION,
    TYP_GATE_CLOSED_1,
    TYP_GATE_CLOSED_2,
    TYP_MAP_INTERIOR_LOOKUP,
)
from ualg.data import (
    UA_METROPOLIS_DAWN_PROFILE,
    UA_ORIGINAL_PROFILE,
    tileset_compatibility,
    ua_faction_buildings,
    ua_faction_units,
    ua_mission_briefing_maps,
)
from ualg.generator1 import (
    Generator1,
    Generator1CustomOptions,
    TECH_UPGRADE_BUILDING_TILESETS,
    TECH_UPGRADE_BUILDING_TYP_BY_ID,
)
from ualg.generator2 import Generator2
from ualg.ldf import parse_maps
from ualg.rng import MSVCRTRandom


class CoreTests(unittest.TestCase):
    def test_msvcrt_rng_sequence(self) -> None:
        rng = MSVCRTRandom(1)
        self.assertEqual([rng.rand() for _ in range(5)], [41, 18467, 6334, 26500, 19169])

    def test_generator1_single_structure(self) -> None:
        level = Generator1().generate_single(seed=424242, difficulty=5, skill=6)
        self.assertIn("begin_level", level.text)
        self.assertIn("begin_gate", level.text)
        self.assertIn("begin_robo", level.text)
        self.assertIn("begin_maps", level.text)
        self.assertIn("begin_enable\t1", level.text)
        self.assertEqual(self._mission_maps(level.text), ("MB_02.IFF", "DB_02.IFF"))
        maps = parse_maps(level.text)
        self.assertEqual(set(maps), {"typ_map", "own_map", "hgt_map", "blg_map"})
        for _name, (width, height, rows) in maps.items():
            self.assertEqual(width, level.width)
            self.assertEqual(height, level.height)
            self.assertEqual(len(rows), level.height)
            self.assertTrue(all(len(row) == level.width for row in rows))
        self._assert_crlf_only(level.text)

    def test_generator1_campaign_order_and_targets(self) -> None:
        campaign = Generator1().generate_campaign(seed=13579, difficulty=5)
        self.assertTrue(campaign.ok)
        self.assertEqual([level.filename for level in campaign.levels], list(GENERATOR1_CAMPAIGN_FILENAMES))
        self.assertEqual(len(campaign.levels), 44)
        first = campaign.levels[0].text
        third = campaign.levels[2].text
        idx43 = campaign.levels[42].text
        final = campaign.levels[43].text
        self.assertIn("target_level\t=\t26", first)
        self.assertIn("target_level\t=\t1", third)
        self.assertIn("target_level\t=\t99", idx43)
        self.assertIn("target_level\t=\t0", final)
        self.assertIn("win_movie", idx43)
        self.assertIn("lose_movie", idx43)
        self.assertNotIn("begin_enable\t1", "\n".join(level.text for level in campaign.levels))

    def test_generator1_rosters_follow_uadata_original(self) -> None:
        units = ua_faction_units(UA_ORIGINAL_PROFILE)
        buildings = ua_faction_buildings(UA_ORIGINAL_PROFILE)

        for faction in (
            FACTION_PLAYER,
            FACTION_GHORKOVS,
            FACTION_TAERKASTEN,
            FACTION_MYKONIANS,
            FACTION_SULGOGARS,
            FACTION_TUTOR,
        ):
            self.assertEqual(VEHICLES_BY_FACTION[faction], units[faction])
            self.assertEqual(BUILDINGS_BY_FACTION[faction], buildings[faction])

        expected_black_units = self._dedupe(
            units[FACTION_PLAYER]
            + units[FACTION_SULGOGARS]
            + units[FACTION_MYKONIANS]
            + units[FACTION_TAERKASTEN]
            + units[FACTION_GHORKOVS]
        )
        expected_black_buildings = self._dedupe(
            buildings[FACTION_PLAYER]
            + buildings[FACTION_SULGOGARS]
            + buildings[FACTION_MYKONIANS]
            + buildings[FACTION_TAERKASTEN]
            + buildings[FACTION_BLACK_SECT]
            + buildings[FACTION_GHORKOVS]
        )
        self.assertEqual(VEHICLES_BY_FACTION[FACTION_BLACK_SECT], expected_black_units)
        self.assertEqual(BUILDINGS_BY_FACTION[FACTION_BLACK_SECT], expected_black_buildings)

    def test_generator1_metropolis_dawn_ghorkov_campaign_profile(self) -> None:
        campaign = Generator1().generate_campaign(seed=1234, campaign_profile="md-ghorkov")
        expected_filenames = [
            f"L{level_id:02d}{level_id:02d}.ldf"
            for level_id in GENERATOR1_MD_CAMPAIGN_LEVEL_IDS_BY_PROFILE["md-ghorkov"]
        ]

        self.assertEqual([level.filename for level in campaign.levels], expected_filenames)
        self.assertEqual(len(campaign.levels), 16)
        self._assert_metropolis_dawn_mission_maps(campaign.levels)
        by_id = {level.level_id: level for level in campaign.levels}
        for level_id, targets in GENERATOR1_MD_CAMPAIGN_TARGETS_BY_PROFILE["md-ghorkov"].items():
            self.assertEqual(self._gate_targets(by_id[level_id].text), targets)

        turantul_i = self._robo_owner_vehicles(by_id[35].text)
        turantul_ii = self._robo_owner_vehicles(by_id[37].text)
        self.assertIn((6, 176), turantul_i)
        self.assertIn((6, 177), turantul_ii)
        self.assertEqual(sum(1 for owner, _vehicle in turantul_i if owner == 6), 1)
        self.assertIn((1, 56), turantul_i)

    def test_generator1_metropolis_dawn_taerkasten_campaign_profile(self) -> None:
        campaign = Generator1().generate_campaign(seed=1234, campaign_profile="md-taerkasten")
        expected_filenames = [
            f"L{level_id:02d}{level_id:02d}.ldf"
            for level_id in GENERATOR1_MD_CAMPAIGN_LEVEL_IDS_BY_PROFILE["md-taerkasten"]
        ]

        self.assertEqual([level.filename for level in campaign.levels], expected_filenames)
        self.assertEqual(len(campaign.levels), 15)
        self._assert_metropolis_dawn_mission_maps(campaign.levels)
        by_id = {level.level_id: level for level in campaign.levels}
        for level_id, targets in GENERATOR1_MD_CAMPAIGN_TARGETS_BY_PROFILE["md-taerkasten"].items():
            self.assertEqual(self._gate_targets(by_id[level_id].text), targets)

        owner_vehicles = self._robo_owner_vehicles(by_id[78].text)
        self.assertIn((4, 178), owner_vehicles)
        self.assertEqual(sum(1 for owner, _vehicle in owner_vehicles if owner == 4), 1)
        self.assertIn((1, 56), self._robo_owner_vehicles(by_id[45].text))

    def test_generator1_typ_map_policy(self) -> None:
        improved = Generator1().generate_single(seed=424242, difficulty=5, skill=6)
        strict = Generator1().generate_single(seed=424242, difficulty=5, skill=6, improved=False)
        improved_maps = parse_maps(improved.text)
        strict_maps = parse_maps(strict.text)
        improved_typ = improved_maps["typ_map"][2]
        improved_blg = improved_maps["blg_map"][2]
        strict_typ = strict_maps["typ_map"][2]
        strict_blg = strict_maps["blg_map"][2]
        improved_allowed = tileset_compatibility()[improved.tileset]
        strict_allowed = set(TYP_MAP_INTERIOR_LOOKUP)
        key_types = {TYP_GATE_CLOSED_1, TYP_GATE_CLOSED_2}
        for y in range(1, improved.height - 1):
            for x in range(1, improved.width - 1):
                if improved_blg[y][x] or improved_typ[y][x] in key_types:
                    continue
                self.assertIn(improved_typ[y][x], improved_allowed)
        for y in range(1, strict.height - 1):
            for x in range(1, strict.width - 1):
                if strict_blg[y][x] or strict_typ[y][x] in key_types:
                    continue
                self.assertIn(strict_typ[y][x], strict_allowed)
        self.assertTrue(any(set(TYP_MAP_INTERIOR_LOOKUP) - allowed for allowed in tileset_compatibility().values()))

    def test_generator1_determinism(self) -> None:
        gen = Generator1()
        first = gen.generate_single(seed=24680, difficulty=7, skill=3)
        second = gen.generate_single(seed=24680, difficulty=7, skill=3)
        third = gen.generate_single(seed=24681, difficulty=7, skill=3)
        self.assertEqual(first.text, second.text)
        self.assertNotEqual(first.text, third.text)

    def test_generator1_custom_options_affect_output(self) -> None:
        level = Generator1().generate_custom(
            Generator1CustomOptions(
                seed=424242,
                width=12,
                height=10,
                gate_target_level_id=70,
                gate_key_count=3,
                win_movie=True,
                lose_movie=True,
                player_energy=600000,
                ai_slot_present={FACTION_GHORKOVS: [True, False, False]},
                ai_slot_energy={FACTION_GHORKOVS: [800000, 0, 0]},
                ai_host_vehicle_id={FACTION_GHORKOVS: 59},
                superitem_flags=[True, False],
                superitem_countdowns={1: 600000},
                enabled_vehicles={FACTION_GHORKOVS: [22]},
                enabled_buildings={FACTION_PLAYER: [38], FACTION_GHORKOVS: [52]},
            )
        )

        self.assertEqual(level.width, 12)
        self.assertEqual(level.height, 10)
        self.assertIn("target_level\t=\t70", level.text)
        self.assertIn("win_movie", level.text)
        self.assertIn("lose_movie", level.text)
        self.assertIn("vehicle\t=\t59", level.text)
        self.assertIn("energy\t=\t800000", level.text)
        self.assertIn("countdown\t=\t600000", level.text)
        self.assertIn("\tvehicle = 22", level.text)
        self.assertIn("\tbuilding = 38", level.text)
        self.assertIn("\tbuilding = 52", level.text)
        gate_keys = self._keysec_pairs(self._blocks(level.text, "begin_gate")[0])
        self.assertEqual(len(gate_keys), 3)

    def test_generator1_custom_supports_per_slot_ghorkov_host_vehicles(self) -> None:
        level = Generator1().generate_custom(
            Generator1CustomOptions(
                seed=778899,
                width=12,
                height=10,
                player_energy=600000,
                ai_slot_present={FACTION_GHORKOVS: [True, True, False]},
                ai_slot_energy={FACTION_GHORKOVS: [400000, 500000, 0]},
                ai_slot_host_vehicle_id={FACTION_GHORKOVS: [59, 57, 0]},
            )
        )

        ghorkov_blocks = [
            block
            for block in self._blocks(level.text, "begin_robo")
            if self._property_values(block, "owner") == ["6"]
        ]
        vehicles = [int(self._property_values(block, "vehicle")[0]) for block in ghorkov_blocks]
        energies = [int(self._property_values(block, "energy")[0]) for block in ghorkov_blocks]

        self.assertEqual(vehicles, [59, 57])
        self.assertEqual(energies, [400000, 500000])

    def test_generator1_buildings_have_non_neutral_ownership(self) -> None:
        for seed in (424242, 24680, 13579):
            level = Generator1().generate_single(seed=seed, difficulty=7, skill=9)
            maps = parse_maps(level.text)
            own = maps["own_map"][2]
            blg = maps["blg_map"][2]
            for y in range(1, level.height - 1):
                for x in range(1, level.width - 1):
                    if blg[y][x]:
                        self.assertNotEqual(own[y][x], 0, f"building at {(x, y)} has neutral ownership")

    def test_generator1_gate_keys_do_not_overwrite_typ_map(self) -> None:
        level = Generator1().generate_single(seed=424242, difficulty=5, skill=6)
        typ = parse_maps(level.text)["typ_map"][2]
        blg = parse_maps(level.text)["blg_map"][2]
        gate_blocks = self._blocks(level.text, "begin_gate")
        self.assertEqual(len(gate_blocks), 1)
        keys = self._keysec_pairs(gate_blocks[0])
        self.assertGreater(len(keys), 0)
        self.assertEqual(len(keys), len(set(keys)))
        for x, y in keys:
            self.assertTrue(0 < x < level.width - 1)
            self.assertTrue(0 < y < level.height - 1)
            self.assertNotIn(typ[y][x], {TYP_GATE_CLOSED_1, TYP_GATE_CLOSED_2})
            self.assertEqual(blg[y][x], 0)

    def test_generator1_superitem_keys_reuse_count_and_do_not_collide(self) -> None:
        level = Generator1().generate_single(seed=24680, difficulty=7, skill=11)
        maps = parse_maps(level.text)
        typ = maps["typ_map"][2]
        blg = maps["blg_map"][2]
        gate_keys = self._keysec_pairs(self._blocks(level.text, "begin_gate")[0])
        item_keys = [self._keysec_pairs(block) for block in self._blocks(level.text, "begin_item")]
        self.assertGreaterEqual(len(item_keys), 2)
        self.assertEqual(len(item_keys[0]), len(item_keys[1]))
        all_keys = gate_keys + [key for keys in item_keys for key in keys]
        self.assertEqual(len(all_keys), len(set(all_keys)))
        for x, y in all_keys:
            self.assertTrue(0 < x < level.width - 1)
            self.assertTrue(0 < y < level.height - 1)
            self.assertEqual(blg[y][x], 0)
        for keys in item_keys:
            for x, y in keys:
                self.assertIn(typ[y][x], {TYP_GATE_CLOSED_1, TYP_GATE_CLOSED_2})

    def test_generator1_tech_upgrade_buildings_match_maps(self) -> None:
        seen_buildings: set[int] = set()
        for seed in range(1, 12):
            level = Generator1().generate_single(seed=seed, difficulty=7, skill=6)
            maps = parse_maps(level.text)
            typ = maps["typ_map"][2]
            blg = maps["blg_map"][2]
            own = maps["own_map"][2]
            for block in self._blocks(level.text, "begin_gem"):
                x = int(self._property_values(block, "sec_x")[0])
                y = int(self._property_values(block, "sec_y")[0])
                building = int(self._property_values(block, "building")[0])
                seen_buildings.add(building)

                self.assertEqual(blg[y][x], building)
                self.assertEqual(typ[y][x], TECH_UPGRADE_BUILDING_TYP_BY_ID[building])
                self.assertNotEqual(own[y][x], 0)
                if building in TECH_UPGRADE_BUILDING_TILESETS:
                    self.assertIn(level.tileset, TECH_UPGRADE_BUILDING_TILESETS[building])

        self.assertEqual(seen_buildings, set(TECH_UPGRADE_BUILDING_TYP_BY_ID))

    def test_generator2_single_structure_and_determinism(self) -> None:
        gen = Generator2()
        first = gen.generate_single(seed=112233, level_id=1)
        second = gen.generate_single(seed=112233, level_id=1)
        third = gen.generate_single(seed=112234, level_id=1)
        self.assertEqual(first.text, second.text)
        self.assertNotEqual(first.text, third.text)
        self.assertGreater(len(first.text), 1000)
        self.assertIn("Generator: Generator2", first.text)
        self.assertIn("begin_gate", first.text)
        self.assertIn("begin_enable", first.text)
        self.assertEqual(self._mission_maps(first.text), ("MB_15.IFF", "DB_15.IFF"))
        maps = parse_maps(first.text)
        self.assertEqual(set(maps), {"typ_map", "own_map", "hgt_map", "blg_map"})
        self.assertGreaterEqual((first.width - 2) * (first.height - 2), 80)
        enemy_robos = [block for block in first.text.split("begin_robo") if "owner         = 1" not in block]
        self.assertGreaterEqual(len(enemy_robos), 1)
        self._assert_crlf_only(first.text)
        self._assert_generator2_typ_border(first)

    def test_generator2_campaign_graph(self) -> None:
        campaign = Generator2().generate_campaign(seed=998877)
        self.assertTrue(campaign.ok)
        self.assertEqual(len(campaign.levels), len(GENERATOR2_CAMPAIGN_LEVEL_IDS))
        by_id = {level.level_id: level for level in campaign.levels}
        self.assertIn("target_level", by_id[1].text)
        self.assertIn("= 2", by_id[1].text)
        self.assertIn("= 3", by_id[1].text)
        self.assertIn("= 40", by_id[34].text)
        self.assertIn("= 44", by_id[34].text)
        self.assertNotIn("target_level", by_id[15].text)
        self.assertIn("= 15", by_id[75].text)

    def test_generator2_metropolis_dawn_ghorkov_campaign_profile(self) -> None:
        campaign = Generator2().generate_campaign(seed=998877, campaign_profile="md-ghorkov")
        expected_ids = GENERATOR2_MD_CAMPAIGN_LEVEL_IDS_BY_PROFILE["md-ghorkov"]

        self.assertEqual([level.level_id for level in campaign.levels], expected_ids)
        self.assertEqual(len(campaign.levels), 16)
        self._assert_metropolis_dawn_mission_maps(campaign.levels)
        by_id = {level.level_id: level for level in campaign.levels}
        for level_id, targets in GENERATOR2_MD_CAMPAIGN_TARGETS_BY_PROFILE["md-ghorkov"].items():
            self.assertEqual(self._gate_targets(by_id[level_id].text), targets)

        self.assertEqual(self._robo_owner_vehicles(by_id[35].text)[0], (6, 176))
        self.assertEqual(self._robo_owner_vehicles(by_id[37].text)[0], (6, 177))
        for level in campaign.levels:
            self.assertTrue(all(owner != 6 for owner, _vehicle in self._robo_owner_vehicles(level.text)[1:]))

    def test_generator2_metropolis_dawn_taerkasten_campaign_profile(self) -> None:
        campaign = Generator2().generate_campaign(seed=998877, campaign_profile="md-taerkasten")
        expected_ids = GENERATOR2_MD_CAMPAIGN_LEVEL_IDS_BY_PROFILE["md-taerkasten"]

        self.assertEqual([level.level_id for level in campaign.levels], expected_ids)
        self.assertEqual(len(campaign.levels), 15)
        self._assert_metropolis_dawn_mission_maps(campaign.levels)
        by_id = {level.level_id: level for level in campaign.levels}
        for level_id, targets in GENERATOR2_MD_CAMPAIGN_TARGETS_BY_PROFILE["md-taerkasten"].items():
            self.assertEqual(self._gate_targets(by_id[level_id].text), targets)

        for level in campaign.levels:
            owner_vehicles = self._robo_owner_vehicles(level.text)
            self.assertEqual(owner_vehicles[0], (4, 178))
            self.assertTrue(all(owner != 4 for owner, _vehicle in owner_vehicles[1:]))

    def test_generator2_typ_map_uses_legacy_set_list(self) -> None:
        for values in GENERATOR2_SET_LIST.values():
            self.assertTrue(values)
        for tileset, values in GENERATOR2_SET_LIST.items():
            self.assertTrue(set(values).issubset(tileset_compatibility()[tileset]))
            self.assertTrue(tileset_compatibility()[tileset] - set(values))

        for seed in range(1, 25):
            level = Generator2().generate_single(seed=seed, level_id=1)
            allowed = set(GENERATOR2_SET_LIST[level.tileset])
            typ = parse_maps(level.text)["typ_map"][2]
            for y in range(1, level.height - 1):
                for x in range(1, level.width - 1):
                    self.assertIn(typ[y][x], allowed)

    def test_generator2_squad_blocks_do_not_emit_mb_status(self) -> None:
        found_squad = False
        for seed in range(1, 25):
            level = Generator2().generate_single(seed=seed, level_id=1)
            squad_blocks = self._blocks(level.text, "begin_squad")
            if not squad_blocks:
                continue
            found_squad = True
            for block in squad_blocks:
                self.assertFalse(any("mb_status" in line for line in block))
        self.assertTrue(found_squad)

    def test_cli_writes_files(self) -> None:
        gen1_output = ROOT / ".cli_smoke_gen1_single.ldf"
        gen1_campaign = ROOT / ".cli_smoke_gen1_campaign"
        gen1_md_campaign = ROOT / ".cli_smoke_gen1_md_campaign"
        gen2_output = ROOT / ".cli_smoke_gen2_single.ldf"
        gen2_md_campaign = ROOT / ".cli_smoke_gen2_md_campaign"
        env = {**os.environ, "PYTHONPATH": str(SRC), "PYTHONDONTWRITEBYTECODE": "1"}
        try:
            result = subprocess.run(
                [sys.executable, "-B", "-m", "ualg.cli", "gen1", "single", "--seed", "1234", "--output", str(gen1_output)],
                cwd=ROOT,
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(gen1_output.exists())
            self.assertIn("begin_level", gen1_output.read_text(encoding="utf-8"))

            result = subprocess.run(
                [sys.executable, "-B", "-m", "ualg.cli", "gen1", "campaign", "--seed", "1234", "--output-dir", str(gen1_campaign)],
                cwd=ROOT,
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(len(list(gen1_campaign.glob("*.ldf"))), len(GENERATOR1_CAMPAIGN_FILENAMES))

            result = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    "-m",
                    "ualg.cli",
                    "gen1",
                    "campaign",
                    "--seed",
                    "1234",
                    "--campaign-profile",
                    "md-ghorkov",
                    "--output-dir",
                    str(gen1_md_campaign),
                ],
                cwd=ROOT,
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(
                len(list(gen1_md_campaign.glob("*.ldf"))),
                len(GENERATOR1_MD_CAMPAIGN_LEVEL_IDS_BY_PROFILE["md-ghorkov"]),
            )

            result = subprocess.run(
                [sys.executable, "-B", "-m", "ualg.cli", "gen2", "single", "--seed", "1234", "--level-id", "1", "--output", str(gen2_output)],
                cwd=ROOT,
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(gen2_output.exists())
            self.assertIn("begin_level", gen2_output.read_text(encoding="utf-8"))

            result = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    "-m",
                    "ualg.cli",
                    "gen2",
                    "campaign",
                    "--seed",
                    "1234",
                    "--campaign-profile",
                    "md-taerkasten",
                    "--output-dir",
                    str(gen2_md_campaign),
                ],
                cwd=ROOT,
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(
                len(list(gen2_md_campaign.glob("*.ldf"))),
                len(GENERATOR2_MD_CAMPAIGN_LEVEL_IDS_BY_PROFILE["md-taerkasten"]),
            )
        finally:
            for output in (gen1_output, gen2_output):
                if output.exists():
                    output.unlink()
            if gen1_campaign.exists():
                shutil.rmtree(gen1_campaign)
            if gen1_md_campaign.exists():
                shutil.rmtree(gen1_md_campaign)
            if gen2_md_campaign.exists():
                shutil.rmtree(gen2_md_campaign)

    @staticmethod
    def _blocks(text: str, block_name: str) -> list[list[str]]:
        blocks: list[list[str]] = []
        current: list[str] = []
        in_block = False
        for line in text.splitlines():
            stripped = line.strip()
            if stripped == block_name:
                in_block = True
                current = []
                continue
            if in_block and stripped == "end":
                blocks.append(current)
                in_block = False
                continue
            if in_block:
                current.append(line)
        return blocks

    @staticmethod
    def _keysec_pairs(block: list[str]) -> list[tuple[int, int]]:
        pairs: list[tuple[int, int]] = []
        pending_x: int | None = None
        for line in block:
            if "=" not in line:
                continue
            key, value = (part.strip() for part in line.split("=", 1))
            if key == "keysec_x":
                pending_x = int(value)
            elif key == "keysec_y" and pending_x is not None:
                pairs.append((pending_x, int(value)))
                pending_x = None
        return pairs

    @staticmethod
    def _property_values(block: list[str], name: str) -> list[str]:
        values: list[str] = []
        for line in block:
            if "=" not in line:
                continue
            key, value = (part.strip() for part in line.split("=", 1))
            if key == name:
                values.append(value)
        return values

    def _robo_owner_vehicles(self, text: str) -> list[tuple[int, int]]:
        result: list[tuple[int, int]] = []
        for block in self._blocks(text, "begin_robo"):
            owners = self._property_values(block, "owner")
            vehicles = self._property_values(block, "vehicle")
            if owners and vehicles:
                result.append((int(owners[0]), int(vehicles[0])))
        return result

    def _gate_targets(self, text: str) -> list[int]:
        result: list[int] = []
        for block in self._blocks(text, "begin_gate"):
            result.extend(int(value) for value in self._property_values(block, "target_level"))
        return result

    def _mission_maps(self, text: str) -> tuple[str, str]:
        mb_blocks = self._blocks(text, "begin_mbmap")
        db_blocks = self._blocks(text, "begin_dbmap")
        return (
            self._property_values(mb_blocks[0], "name")[0],
            self._property_values(db_blocks[0], "name")[0],
        )

    def _assert_metropolis_dawn_mission_maps(self, levels) -> None:
        briefing_maps = {name.lower() for name in ua_mission_briefing_maps(UA_METROPOLIS_DAWN_PROFILE)}
        for level in levels:
            briefing_map, debriefing_map = self._mission_maps(level.text)
            self.assertEqual(briefing_map.lower(), f"mb_{level.level_id:02d}.iff")
            self.assertEqual(debriefing_map.lower(), briefing_map.lower())
            self.assertIn(briefing_map.lower(), briefing_maps)

    @staticmethod
    def _dedupe(values: list[int]) -> list[int]:
        return list(dict.fromkeys(values))

    def _assert_crlf_only(self, text: str) -> None:
        self.assertEqual(text.count("\n"), text.count("\r\n"))

    def _assert_generator2_typ_border(self, level) -> None:
        width, height, typ = parse_maps(level.text)["typ_map"]
        self.assertEqual(width, level.width)
        self.assertEqual(height, level.height)
        self.assertEqual(typ[0][0], 248)
        self.assertEqual(typ[0][width - 1], 249)
        self.assertEqual(typ[height - 1][0], 251)
        self.assertEqual(typ[height - 1][width - 1], 250)
        for x in range(1, width - 1):
            self.assertEqual(typ[0][x], 252)
            self.assertEqual(typ[height - 1][x], 254)
        for y in range(1, height - 1):
            self.assertEqual(typ[y][0], 255)
            self.assertEqual(typ[y][width - 1], 253)


if __name__ == "__main__":
    unittest.main()
