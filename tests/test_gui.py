from __future__ import annotations

import sys
import shutil
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from ualg.constants import FACTION_BLACK_SECT, FACTION_GHORKOVS, FACTION_MYKONIANS, FACTION_PLAYER, FACTION_TAERKASTEN
from ualg.gui import (
    CustomWizardState,
    GuiSettings,
    _unit_enable_values,
    backup_campaign_ldfs,
    backup_existing_file,
    custom_wizard_options_from_state,
    load_settings,
    main,
    save_settings,
)
from ualg.gui_support.workflows import (
    create_configured_backups,
    generate_generator1_single,
    generate_generator2_campaign,
    generate_generator3_campaign,
    generate_generator3_single,
)


GENERATOR2_ENEMY_STATION_DELAY_KEYS = {
    "con_delay",
    "def_delay",
    "rec_delay",
    "rob_delay",
    "pow_delay",
    "rad_delay",
    "saf_delay",
    "cpl_delay",
}


class FakeVar:
    def __init__(self, value: bool) -> None:
        self.value = value

    def get(self) -> bool:
        return self.value


class GuiHelperTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_path = ROOT / ".gui_test_work" / self._testMethodName
        if self.tmp_path.exists():
            shutil.rmtree(self.tmp_path)
        self.tmp_path.mkdir(parents=True)

    def tearDown(self) -> None:
        if self.tmp_path.exists():
            shutil.rmtree(self.tmp_path)
        work_dir = ROOT / ".gui_test_work"
        if work_dir.exists() and not any(work_dir.iterdir()):
            work_dir.rmdir()

    def test_settings_round_trip(self) -> None:
        path = self.tmp_path / "RandomUA.ini"
        settings = GuiSettings(
            random_level_file=str(self.tmp_path / "single.ldf"),
            custom_level_file=str(self.tmp_path / "custom.ldf"),
            campaign_directory=str(self.tmp_path / "campaign"),
            exe_location=str(self.tmp_path / "UA.exe"),
            use_building_scripts=False,
            generator1_zero_enemy_radar_budgets=True,
            generator2_single_level_file=str(self.tmp_path / "gen2_single.ldf"),
            generator2_campaign_directory=str(self.tmp_path / "gen2_campaign"),
            generator2_zero_enemy_station_delays=True,
            generator2_zero_enemy_radar_budgets=True,
            generator3_single_level_file=str(self.tmp_path / "gen3_single.ldf"),
            generator3_campaign_directory=str(self.tmp_path / "gen3_campaign"),
            generator3_zero_enemy_station_delays=True,
            generator3_zero_enemy_radar_budgets=True,
        )

        saved = save_settings(settings, path)
        loaded = load_settings(saved)

        self.assertEqual(loaded, settings)

    def test_load_settings_reads_legacy_case_insensitively(self) -> None:
        path = self.tmp_path / "RandomUA.ini"
        path.write_text(
            "\n".join(
                [
                    "[RLG Data]",
                    "data3-do not change=0",
                    "[FileLocations]",
                    "randomlevelfile=C:/levels/random.ldf",
                    "customlevelfile=C:/levels/custom.ldf",
                    "[UA Installed Folder]",
                    "campaigndirectory=C:/ua/campaign",
                    "exelocation=C:/ua/UA.exe",
                ]
            ),
            encoding="utf-8",
        )

        loaded = load_settings(path)

        self.assertEqual(loaded.random_level_file, "C:/levels/random.ldf")
        self.assertEqual(loaded.custom_level_file, "C:/levels/custom.ldf")
        self.assertEqual(loaded.campaign_directory, "C:/ua/campaign")
        self.assertEqual(loaded.exe_location, "C:/ua/UA.exe")
        self.assertFalse(loaded.use_building_scripts)
        self.assertFalse(loaded.generator1_zero_enemy_radar_budgets)
        self.assertEqual(loaded.generator2_single_level_file, "")
        self.assertEqual(loaded.generator2_campaign_directory, "")
        self.assertFalse(loaded.generator2_zero_enemy_station_delays)
        self.assertFalse(loaded.generator2_zero_enemy_radar_budgets)

    def test_load_settings_reads_generator2_paths(self) -> None:
        path = self.tmp_path / "RandomUA.ini"
        path.write_text(
            "\n".join(
                [
                    "[Generator1]",
                    "ZeroEnemyRadarBudgets=1",
                    "[Generator2]",
                    "SingleLevelFile=C:/levels/L0101.ldf",
                    "CampaignDirectory=C:/levels/gen2",
                    "ZeroEnemyStationDelays=1",
                    "ZeroEnemyRadarBudgets=1",
                ]
            ),
            encoding="utf-8",
        )

        loaded = load_settings(path)

        self.assertTrue(loaded.generator1_zero_enemy_radar_budgets)
        self.assertEqual(loaded.generator2_single_level_file, "C:/levels/L0101.ldf")
        self.assertEqual(loaded.generator2_campaign_directory, "C:/levels/gen2")
        self.assertTrue(loaded.generator2_zero_enemy_station_delays)
        self.assertTrue(loaded.generator2_zero_enemy_radar_budgets)

    def test_backup_existing_file_copies_without_removing_source(self) -> None:
        source = self.tmp_path / "level.ldf"
        source.write_text("old level", encoding="utf-8")

        backup = backup_existing_file(source, timestamp="20260102_030405")

        self.assertIsNotNone(backup)
        assert backup is not None
        self.assertTrue(source.exists())
        self.assertTrue(backup.exists())
        self.assertEqual(backup.name, "level.ldf.bak_20260102_030405")
        self.assertEqual(backup.read_text(encoding="utf-8"), "old level")

    def test_backup_existing_file_ignores_missing_source(self) -> None:
        self.assertIsNone(backup_existing_file(self.tmp_path / "missing.ldf"))

    def test_backup_campaign_ldfs_moves_only_ldf_files(self) -> None:
        directory = self.tmp_path
        first = directory / "l0101.ldf"
        second = directory / "L0202.LDF"
        note = directory / "readme.txt"
        first.write_text("one", encoding="utf-8")
        second.write_text("two", encoding="utf-8")
        note.write_text("keep", encoding="utf-8")

        backup_dir, moved = backup_campaign_ldfs(directory, timestamp="20260102_030405")

        self.assertIsNotNone(backup_dir)
        assert backup_dir is not None
        self.assertEqual(backup_dir.name, "Backup_20260102_030405")
        self.assertEqual({path.name for path in moved}, {"l0101.ldf", "L0202.LDF"})
        self.assertFalse(first.exists())
        self.assertFalse(second.exists())
        self.assertTrue(note.exists())
        self.assertEqual((backup_dir / "l0101.ldf").read_text(encoding="utf-8"), "one")
        self.assertEqual((backup_dir / "L0202.LDF").read_text(encoding="utf-8"), "two")

    def test_backup_campaign_ldfs_ignores_empty_or_missing_directory(self) -> None:
        empty_dir = self.tmp_path / "empty"
        empty_dir.mkdir()
        self.assertEqual(backup_campaign_ldfs(empty_dir), (None, []))
        self.assertEqual(backup_campaign_ldfs(self.tmp_path / "missing"), (None, []))

    def test_generator1_single_workflow_writes_level_and_reports_backup(self) -> None:
        target = self.tmp_path / "single.ldf"
        target.write_text("old level", encoding="utf-8")

        result = generate_generator1_single(
            target,
            seed=424242,
            difficulty=5,
            skill=6,
            improved=True,
            zero_enemy_radar_budgets=True,
        )

        self.assertEqual(result.written, target)
        self.assertEqual(result.level.seed, 424242)
        self.assertTrue(target.exists())
        self.assertIn("Generated by Urban Assault Level Generator", target.read_text(encoding="utf-8"))
        self.assertIsNotNone(result.backup_path)
        assert result.backup_path is not None
        self.assertTrue(result.backup_path.exists())
        self.assertEqual(result.backup_path.read_text(encoding="utf-8"), "old level")
        radar_values = self._radar_budget_values(result.level.text)
        self.assertTrue(radar_values)
        self.assertEqual(set(radar_values), {"0"})

    def test_generator2_campaign_workflow_writes_campaign_and_reports_backup(self) -> None:
        directory = self.tmp_path / "campaign"
        directory.mkdir()
        old_level = directory / "old.ldf"
        old_level.write_text("old campaign level", encoding="utf-8")

        result = generate_generator2_campaign(
            directory,
            seed=998877,
            campaign_profile="original",
            zero_enemy_station_delays=True,
            zero_enemy_radar_budgets=True,
        )

        self.assertEqual(result.directory, directory)
        self.assertEqual(result.campaign_profile, "original")
        self.assertEqual(result.campaign.seed, 998877)
        self.assertEqual(len(result.written), len(result.campaign.levels))
        self.assertTrue(all(path.exists() for path in result.written))
        self.assertFalse(old_level.exists())
        self.assertIsNotNone(result.backup_dir)
        assert result.backup_dir is not None
        self.assertEqual(result.moved, [result.backup_dir / "old.ldf"])
        self.assertEqual((result.backup_dir / "old.ldf").read_text(encoding="utf-8"), "old campaign level")
        delay_values = [
            value
            for level in result.campaign.levels
            for value in self._generator2_delay_values(level.text)
        ]
        self.assertTrue(delay_values)
        self.assertEqual(set(delay_values), {"0"})
        radar_values = [
            value
            for level in result.campaign.levels
            for value in self._radar_budget_values(level.text)
        ]
        self.assertTrue(radar_values)
        self.assertEqual(set(radar_values), {"0"})

    def test_load_settings_reads_generator3_paths(self) -> None:
        path = self.tmp_path / "RandomUA.ini"
        path.write_text(
            "\n".join(
                [
                    "[Generator3]",
                    "SingleLevelFile=C:/levels/gen3.ldf",
                    "CampaignDirectory=C:/levels/gen3camp",
                    "ZeroEnemyStationDelays=1",
                    "ZeroEnemyRadarBudgets=1",
                ]
            ),
            encoding="utf-8",
        )

        loaded = load_settings(path)

        self.assertEqual(loaded.generator3_single_level_file, "C:/levels/gen3.ldf")
        self.assertEqual(loaded.generator3_campaign_directory, "C:/levels/gen3camp")
        self.assertTrue(loaded.generator3_zero_enemy_station_delays)
        self.assertTrue(loaded.generator3_zero_enemy_radar_budgets)

    def test_generator3_single_remix_workflow_writes_level_and_backup(self) -> None:
        target = self.tmp_path / "remix.ldf"
        target.write_text("old level", encoding="utf-8")

        result = generate_generator3_single(
            target,
            seed=12345,
            campaign_profile="original",
            mode="remix",
            skeleton="L0101",
            zero_enemy_radar_budgets=True,
        )

        self.assertEqual(result.written, target)
        self.assertEqual(result.level.metadata["mode"], "remix")
        self.assertEqual(result.level.metadata["skeleton"], "L0101")
        self.assertTrue(target.exists())
        self.assertIsNotNone(result.backup_path)
        assert result.backup_path is not None
        self.assertEqual(result.backup_path.read_text(encoding="utf-8"), "old level")
        radar_values = self._radar_budget_values(result.level.text)
        self.assertTrue(radar_values)
        self.assertEqual(set(radar_values), {"0"})

    def test_generator3_single_synthesis_workflow(self) -> None:
        target = self.tmp_path / "synth.ldf"

        result = generate_generator3_single(
            target,
            seed=12345,
            campaign_profile="original",
            mode="synthesis",
        )

        self.assertEqual(result.level.metadata["mode"], "synthesis")
        self.assertIn(result.level.metadata["synth_method"], ("wfc", "scanline"))
        self.assertTrue(target.exists())

    def test_generator3_campaign_workflow_writes_campaign(self) -> None:
        directory = self.tmp_path / "gen3camp"
        directory.mkdir()

        result = generate_generator3_campaign(
            directory,
            seed=2026,
            campaign_profile="md-ghorkov",
            mode="remix",
        )

        self.assertEqual(result.campaign_profile, "md-ghorkov")
        self.assertEqual(len(result.written), len(result.campaign.levels))
        self.assertTrue(result.written)
        self.assertTrue(all(path.exists() for path in result.written))

    def test_configured_backup_workflow_skips_blanks_and_deduplicates_paths(self) -> None:
        single = self.tmp_path / "single.ldf"
        single.write_text("single level", encoding="utf-8")
        campaign_dir = self.tmp_path / "campaign"
        campaign_dir.mkdir()
        old_campaign = campaign_dir / "old.ldf"
        old_campaign.write_text("campaign level", encoding="utf-8")
        note = campaign_dir / "note.txt"
        note.write_text("keep", encoding="utf-8")

        result = create_configured_backups(
            ("", str(single), str(single), str(self.tmp_path / "missing.ldf"), "   "),
            ("", str(campaign_dir), f" {campaign_dir} "),
        )

        self.assertEqual(len(result.created), 3)
        file_backups = [path for path in result.created if path.name.startswith("single.ldf.bak_")]
        self.assertEqual(len(file_backups), 1)
        self.assertEqual(file_backups[0].read_text(encoding="utf-8"), "single level")
        backup_dirs = [path for path in result.created if path.is_dir()]
        self.assertEqual(len(backup_dirs), 1)
        self.assertEqual((backup_dirs[0] / "old.ldf").read_text(encoding="utf-8"), "campaign level")
        self.assertFalse(old_campaign.exists())
        self.assertTrue(note.exists())

    def test_gui_entrypoint_rejects_arguments_without_creating_window(self) -> None:
        with self.assertRaises(SystemExit):
            main(["unexpected"])

    def test_gui_source_does_not_probe_legacy_executable(self) -> None:
        gui_files = [
            SRC / "ualg" / "gui.py",
            *(SRC / "ualg" / "gui_support").glob("*.py"),
        ]
        source = "\n".join(path.read_text(encoding="utf-8") for path in gui_files)

        self.assertNotIn("find_legacy_executable", source)
        self.assertNotIn("load_dialogs", source)
        self.assertNotIn("load_license_text", source)

    @staticmethod
    def _generator2_delay_values(text: str) -> list[str]:
        values: list[str] = []
        for line in text.splitlines():
            if "=" not in line:
                continue
            key, value = (part.strip() for part in line.split("=", 1))
            if key in GENERATOR2_ENEMY_STATION_DELAY_KEYS:
                values.append(value)
        return values

    @staticmethod
    def _radar_budget_values(text: str) -> list[str]:
        values: list[str] = []
        for line in text.splitlines():
            if "=" not in line:
                continue
            key, value = (part.strip() for part in line.split("=", 1))
            if key == "rad_budget":
                values.append(value)
        return values

    def test_unit_enable_mapping_uses_legacy_checkbox_ids(self) -> None:
        vehicles, buildings, faction = _unit_enable_values(
            143,
            {1075: FakeVar(True), 1046: FakeVar(True), 1085: FakeVar(True)},
        )
        self.assertEqual(faction, FACTION_PLAYER)
        self.assertIn(16, vehicles)
        self.assertIn(5, vehicles)
        self.assertIn(63, buildings)
        self.assertNotIn(38, buildings)

        vehicles, buildings, faction = _unit_enable_values(143, {1095: FakeVar(True)})
        self.assertEqual(faction, FACTION_PLAYER)
        self.assertEqual(vehicles, [])
        self.assertEqual(buildings, [38])

        vehicles, buildings, faction = _unit_enable_values(
            145,
            {1082: FakeVar(True), 1053: FakeVar(True)},
        )
        self.assertEqual(faction, FACTION_TAERKASTEN)
        self.assertEqual(vehicles, [35])
        self.assertEqual(buildings, [73])

        vehicles, buildings, faction = _unit_enable_values(
            146,
            {1074: FakeVar(True), 1052: FakeVar(True)},
        )
        self.assertEqual(faction, FACTION_MYKONIANS)
        self.assertEqual(vehicles, [68])
        self.assertEqual(buildings, [72])

        vehicles, buildings, faction = _unit_enable_values(147, {1151: FakeVar(True)})
        self.assertEqual(faction, FACTION_BLACK_SECT)
        self.assertIn(22, vehicles)
        self.assertIn(134, vehicles)
        self.assertIn(73, vehicles)
        self.assertIn(52, buildings)

        vehicles, buildings, faction = _unit_enable_values(149, {1098: FakeVar(True), 1153: FakeVar(False)})
        self.assertEqual(faction, FACTION_BLACK_SECT)
        self.assertEqual(vehicles, [])
        self.assertEqual(buildings, [48])

    def test_custom_wizard_state_maps_legacy_options(self) -> None:
        state = CustomWizardState(
            random_size=False,
            width=20,
            height=10,
            player_energy=1500,
            gate_target_level_id=70,
            random_gate_keys=False,
            gate_key_count=4,
            win_movie=True,
            lose_movie=True,
            random_bombs=False,
            bomb_included=[True, True],
            bomb_custom_countdown=[True, False],
            bomb_countdown_seconds=[600, 1200],
            random_build_options=False,
        )
        state.host_present[FACTION_GHORKOVS] = [True, True, False]
        state.host_energy[FACTION_GHORKOVS] = [2000, 2500, 1500]
        state.ghorkov_host_types = ["Turantul I", "Turantul II", "Turantul I"]
        state.faction_random_build_options[FACTION_PLAYER] = False
        state.faction_random_build_options[FACTION_GHORKOVS] = False
        state.enabled_vehicles[FACTION_PLAYER] = {1, 16}
        state.enabled_buildings[FACTION_PLAYER] = {38}
        state.enabled_vehicles[FACTION_GHORKOVS] = {22}
        state.enabled_buildings[FACTION_GHORKOVS] = {52}

        options = custom_wizard_options_from_state(state, allow_new_buildings=True)

        self.assertEqual(options.width, 22)
        self.assertEqual(options.height, 12)
        self.assertEqual(options.player_energy, 600000)
        self.assertEqual(options.ai_slot_present[FACTION_GHORKOVS], [True, True, False])
        self.assertEqual(options.ai_slot_energy[FACTION_GHORKOVS], [800000, 1000000, 0])
        self.assertEqual(options.ai_slot_host_vehicle_id[FACTION_GHORKOVS], [59, 57, 0])
        self.assertEqual(options.gate_target_level_id, 70)
        self.assertEqual(options.gate_key_count, 4)
        self.assertTrue(options.win_movie)
        self.assertTrue(options.lose_movie)
        self.assertEqual(options.superitem_flags, [True, True])
        self.assertEqual(options.superitem_countdowns, {1: 600000})
        self.assertEqual(options.enabled_vehicles[FACTION_PLAYER], [1, 16])
        self.assertEqual(options.enabled_buildings[FACTION_PLAYER], [38])
        self.assertEqual(options.enabled_vehicles[FACTION_GHORKOVS], [22])
        self.assertEqual(options.enabled_buildings[FACTION_GHORKOVS], [52])

    def test_custom_wizard_filters_new_buildings_when_scripts_disabled(self) -> None:
        state = CustomWizardState(random_bombs=False, random_build_options=False)
        state.host_present[FACTION_GHORKOVS] = [True, False, False]
        state.faction_random_build_options[FACTION_PLAYER] = False
        state.enabled_buildings[FACTION_PLAYER] = {38, 63}

        options = custom_wizard_options_from_state(state, allow_new_buildings=False)

        self.assertEqual(options.enabled_vehicles[FACTION_PLAYER], [])
        self.assertEqual(options.enabled_buildings[FACTION_PLAYER], [63])

    def test_custom_wizard_requires_enemy_host(self) -> None:
        state = CustomWizardState(random_bombs=False)

        with self.assertRaises(ValueError):
            custom_wizard_options_from_state(state)


if __name__ == "__main__":
    unittest.main()
