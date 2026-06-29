from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from ualg.constants import (
    ENABLE_EXCLUDED_VEHICLE_IDS,
    MD_TAERKASTEN_ENABLE_EXCLUDED_VEHICLE_IDS,
)
from ualg.gen3.corpus import skeleton_by_name, skeletons_for_source
from ualg.gen3.ldf_reader import parse_ldf
from ualg.gen3.placement import build_enables
from ualg.gen3.synthesis import adjacency_model_for, border_tile, synthesize_typ_map
from ualg.generator3 import Generator3
from ualg.ldf import parse_maps
from ualg.rng import MSVCRTRandom

_FACTION_RESISTANCE = 1
_FACTION_TAERKASTEN = 4
_FACTION_BLACK_SECT = 5

_SAMPLE_LDF = """begin_level
\tset\t=\t1
\tsky\t=\tobjects/test.base
\tambiencetrack\t=\t4_00_20000
\tevent_loop\t=\t3
end
begin_mbmap
\tname\t=\tMB_01.IFF
end
begin_gate
\tsec_x\t=\t2
\tsec_y\t=\t7
\ttarget_level\t=\t2\t\t; comment
\ttarget_level\t=\t3
\tkeysec_x\t=\t5
\tkeysec_y\t=\t3
end
begin_robo
\towner\t=\t1
\tvehicle\t=\t56
\tpos_x\t=\t7763
\tpos_y\t=\t-320
\tpos_z\t=\t-5474
\tenergy\t=\t300000
end
begin_robo
\towner\t=\t6
\tvehicle\t=\t59
\tpos_x\t=\t2623
\tpos_y\t=\t-120
\tpos_z\t=\t-5663
\tenergy\t=\t250000
\tcon_budget\t=\t85
\trad_budget\t=\t10
\tcon_delay\t=\t50010
end
begin_squad
\towner\t=\t6
\tvehicle\t=\t24
\tnum\t=\t2
\tpos_x\t=\t3482
\tpos_z\t=\t-6382
\tuseable
end
include data:scripts/startup2.scr
modify_vehicle\t56
\tshield\t=\t1
end
begin_enable 6
\tvehicle\t=\t24
end
begin_gem
\tsec_x\t=\t2
\tsec_y\t=\t6
\tbuilding\t=\t4
\ttype\t=\t3
\tbegin_action
\t\tmodify_vehicle\t22
\t\t\tenable\t=\t6
\t\tend
\tend_action
end
begin_maps
typ_map\t=
\t4 4
\tf8 fc fc f9
\tff 00 06 fd
\tff 06 00 fd
\tfb fe fe fa
own_map\t=
\t4 4
\t00 00 00 00
\t00 01 06 00
\t00 06 06 00
\t00 00 00 00
hgt_map\t=
\t4 4
\t80 80 80 80
\t80 80 80 80
\t80 80 80 80
\t80 80 80 80
blg_map\t=
\t4 4
\t00 00 00 00
\t00 05 00 00
\t00 00 00 00
\t00 00 00 00
end
"""


class LdfReaderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.level = parse_ldf(_SAMPLE_LDF, name="L0101", source="vanilla")

    def test_header_preserves_string_with_underscores(self) -> None:
        self.assertEqual(self.level.header["ambiencetrack"], "4_00_20000")
        self.assertEqual(self.level.header["event_loop"], 3)

    def test_gate_targets_and_inline_comment_stripped(self) -> None:
        gate = self.level.gates[0]
        self.assertEqual(gate["targets"], [2, 3])
        self.assertEqual(gate["keysecs"], [{"x": 5, "y": 3}])

    def test_robo_budgets_and_player_detection(self) -> None:
        self.assertEqual(self.level.player_owner, 1)
        player = self.level.robos[0]
        self.assertNotIn("con_budget", player)
        enemy = self.level.robos[1]
        self.assertEqual(enemy["con_budget"], 85)

    def test_squad_useable_flag(self) -> None:
        self.assertTrue(self.level.squads[0]["useable"])

    def test_gem_action_captured_verbatim(self) -> None:
        gem = self.level.gems[0]
        self.assertEqual(gem["sec_x"], 2)
        self.assertEqual(gem["building"], 4)
        self.assertIn("begin_action", gem["raw"])
        self.assertIn("end_action", gem["raw"])

    def test_prototype_keeps_include_and_modify(self) -> None:
        self.assertIn("include data:scripts/startup2.scr", self.level.prototype)
        self.assertIn("modify_vehicle\t56", self.level.prototype)

    def test_maps_parsed(self) -> None:
        self.assertEqual(self.level.width, 4)
        self.assertEqual(self.level.height, 4)
        self.assertEqual(self.level.maps["typ"][0][0], 0xF8)


class CorpusTests(unittest.TestCase):
    def test_both_sources_present(self) -> None:
        self.assertEqual(len(skeletons_for_source("vanilla")), 44)
        self.assertEqual(len(skeletons_for_source("metropolisDawn")), 31)

    def test_every_skeleton_has_intact_maps(self) -> None:
        for source in ("vanilla", "metropolisDawn"):
            for skeleton in skeletons_for_source(source):
                maps = skeleton.maps()
                self.assertEqual(set(maps), {"typ", "own", "hgt", "blg"})
                for rows in maps.values():
                    self.assertEqual(len(rows), skeleton.height)
                    self.assertTrue(all(len(row) == skeleton.width for row in rows))
                self.assertEqual(maps["typ"][0][0], 0xF8)
                self.assertEqual(maps["typ"][-1][-1], 0xFA)


class RemixTests(unittest.TestCase):
    def setUp(self) -> None:
        self.generator = Generator3()

    def test_profiles(self) -> None:
        self.assertEqual(self.generator.profiles.names(), ("original", "md-ghorkov", "md-taerkasten"))

    def test_single_is_deterministic(self) -> None:
        a = self.generator.generate_single(seed=12345, campaign_profile="original")
        b = self.generator.generate_single(seed=12345, campaign_profile="original")
        self.assertEqual(a.text, b.text)

    def test_seed_changes_output(self) -> None:
        a = self.generator.generate_single(seed=1, campaign_profile="original", skeleton="L1515")
        b = self.generator.generate_single(seed=2, campaign_profile="original", skeleton="L1515")
        self.assertNotEqual(a.text, b.text)

    def test_player_faction_preserved_and_enemies_remapped(self) -> None:
        level = self.generator.generate_single(seed=7, campaign_profile="original", skeleton="L0101")
        remap = level.metadata["faction_remap"]
        skeleton = skeleton_by_name("L0101", "vanilla")
        self.assertEqual(remap[skeleton.player_owner], 1)
        enemy_pool = set(self.generator.profiles.enemy_factions(self.generator.profiles.get("original")))
        for owner in skeleton.enemy_owners:
            self.assertIn(remap[owner], enemy_pool)

    def test_output_crlf_and_maps_roundtrip(self) -> None:
        level = self.generator.generate_single(seed=42, campaign_profile="original", skeleton="L0101")
        self.assertIn("\r\n", level.text)
        parsed = parse_maps(level.text)
        self.assertEqual(set(parsed), {"typ_map", "own_map", "hgt_map", "blg_map"})
        for _name, (width, height, rows) in parsed.items():
            self.assertEqual((width, height), (level.width, level.height))
            self.assertEqual(len(rows), height)

    def test_zero_radar_budgets(self) -> None:
        level = self.generator.generate_single(
            seed=7, campaign_profile="original", skeleton="L0101", zero_enemy_radar_budgets=True
        )
        for line in level.text.replace("\r\n", "\n").split("\n"):
            if line.strip().startswith("rad_budget"):
                self.assertEqual(line.split("=")[-1].strip(), "0")

    def test_campaigns_valid_for_all_profiles(self) -> None:
        for profile in ("original", "md-ghorkov", "md-taerkasten"):
            campaign = self.generator.generate_campaign(seed=2026, campaign_profile=profile)
            self.assertTrue(campaign.ok)
            self.assertTrue(campaign.levels)
            for level in campaign.levels:
                self.assertEqual(level.metadata["warnings"], [])
                self.assertLessEqual(len(level.metadata["faction_remap"]), 8)

    def test_campaign_rewires_gate_targets(self) -> None:
        campaign = self.generator.generate_campaign(seed=5, campaign_profile="md-ghorkov")
        profile = self.generator.profiles.get("md-ghorkov")
        level7 = next(level for level in campaign.levels if level.level_id == 7)
        expected = profile.targets_by_level.get(7, ())
        if expected:
            joined = level7.text.replace("\r\n", "\n")
            for target in expected:
                self.assertIn(f"target_level\t=\t{target}", joined)

    def test_unknown_profile_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.generator.generate_single(seed=1, campaign_profile="nope")


class SynthesisTests(unittest.TestCase):
    def setUp(self) -> None:
        self.generator = Generator3()

    def test_wfc_border_intact_and_adjacencies_valid(self) -> None:
        width, height = 14, 12
        rows, method = synthesize_typ_map("vanilla", 1, width, height, MSVCRTRandom(4242))
        self.assertEqual(method, "wfc")
        model = adjacency_model_for("vanilla", 1)
        for y in range(height):
            for x in range(width):
                expected = border_tile(x, y, width, height)
                if expected is not None:
                    self.assertEqual(rows[y][x], expected)
        for y in range(height):
            for x in range(width):
                if x + 1 < width:
                    self.assertIn(rows[y][x + 1], model.right.get(rows[y][x], set()))
                if y + 1 < height:
                    self.assertIn(rows[y + 1][x], model.down.get(rows[y][x], set()))

    def test_synthesize_typ_map_deterministic(self) -> None:
        a, _ = synthesize_typ_map("vanilla", 1, 14, 12, MSVCRTRandom(7))
        b, _ = synthesize_typ_map("vanilla", 1, 14, 12, MSVCRTRandom(7))
        self.assertEqual(a, b)

    def test_synthesis_single_is_deterministic_and_valid(self) -> None:
        a = self.generator.generate_single(seed=2026, campaign_profile="original", mode="synthesis")
        b = self.generator.generate_single(seed=2026, campaign_profile="original", mode="synthesis")
        self.assertEqual(a.text, b.text)
        self.assertEqual(a.metadata["mode"], "synthesis")
        self.assertEqual(a.metadata["warnings"], [])
        self.assertIn(a.metadata["synth_method"], ("wfc", "scanline"))

    def test_synthesis_has_player_and_enemy_hosts(self) -> None:
        level = self.generator.generate_single(seed=3, campaign_profile="original", mode="synthesis")
        joined = level.text.replace("\r\n", "\n")
        self.assertGreaterEqual(joined.count("begin_robo"), 2)
        self.assertIn("owner\t=\t1", joined)  # player faction host present

    def test_synthesis_maps_well_formed(self) -> None:
        level = self.generator.generate_single(seed=9, campaign_profile="original", mode="synthesis")
        parsed = parse_maps(level.text)
        self.assertEqual(set(parsed), {"typ_map", "own_map", "hgt_map", "blg_map"})
        typ = parsed["typ_map"][2]
        self.assertEqual(typ[0][0], 0xF8)
        self.assertEqual(typ[-1][-1], 0xFA)

    def test_synthesis_campaign_valid(self) -> None:
        campaign = self.generator.generate_campaign(seed=5, campaign_profile="md-ghorkov", mode="synthesis")
        self.assertTrue(campaign.ok)
        self.assertTrue(campaign.levels)
        for level in campaign.levels:
            self.assertEqual(level.metadata["warnings"], [])

    def test_unknown_mode_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.generator.generate_single(seed=1, mode="nonsense")


class EnableExclusionTests(unittest.TestCase):
    """Generator3 mirrors Generator2's begin_enable exclusions."""

    def setUp(self) -> None:
        self.generator = Generator3()

    def _enables_by_owner(self, profile: str, factions: list[int], profile_id: str) -> dict[int, dict]:
        roster = self.generator.profiles.get(profile).roster
        return {e["owner"]: e for e in build_enables(roster, factions, profile_id=profile_id)}

    def test_resistance_and_black_sect_exclude_single_player_units(self) -> None:
        for profile_id in ("original", "md-ghorkov", "md-taerkasten"):
            profile = profile_id if profile_id != "md-ghorkov" else "md-ghorkov"
            enables = self._enables_by_owner(profile, [_FACTION_RESISTANCE, _FACTION_BLACK_SECT], profile_id)
            for faction in (_FACTION_RESISTANCE, _FACTION_BLACK_SECT):
                for vehicle in ENABLE_EXCLUDED_VEHICLE_IDS:
                    self.assertNotIn(vehicle, enables[faction]["vehicles"], f"{profile_id}/{faction}")

    def test_md_taerkasten_excludes_taerkasten_units(self) -> None:
        enables = self._enables_by_owner("md-taerkasten", [_FACTION_TAERKASTEN, _FACTION_BLACK_SECT], "md-taerkasten")
        for faction in (_FACTION_TAERKASTEN, _FACTION_BLACK_SECT):
            for vehicle in MD_TAERKASTEN_ENABLE_EXCLUDED_VEHICLE_IDS:
                self.assertNotIn(vehicle, enables[faction]["vehicles"])

    def test_taerkasten_units_kept_outside_md_taerkasten(self) -> None:
        # The 143/144 exclusion is gated on the md-taerkasten profile only.
        enables = self._enables_by_owner("md-ghorkov", [_FACTION_TAERKASTEN], "md-ghorkov")
        self.assertTrue(set(MD_TAERKASTEN_ENABLE_EXCLUDED_VEHICLE_IDS) & set(enables[_FACTION_TAERKASTEN]["vehicles"]))

    def test_black_sect_buildings_excluded(self) -> None:
        from ualg.constants import BLACK_SECT_ENABLE_EXCLUDED_BUILDING_IDS

        enables = self._enables_by_owner("original", [_FACTION_BLACK_SECT], "original")
        self.assertFalse(
            set(BLACK_SECT_ENABLE_EXCLUDED_BUILDING_IDS) & set(enables[_FACTION_BLACK_SECT]["buildings"])
        )


if __name__ == "__main__":
    unittest.main()
