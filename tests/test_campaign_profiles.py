from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from ualg.campaign_profiles import ProfileRegistry, default_profile_registry
from ualg.generator1 import Generator1
from ualg.generator2 import Generator2
from ualg.generator4 import Generator4


class CampaignProfileTests(unittest.TestCase):
    def test_default_registry_exposes_builtin_profiles(self) -> None:
        registry = default_profile_registry()

        self.assertEqual(registry.names("generator1"), ("original", "md-ghorkov", "md-taerkasten"))
        self.assertEqual(registry.names("generator2"), ("original", "md-ghorkov", "md-taerkasten"))
        self.assertEqual(registry.names("generator4"), ("original", "md-ghorkov", "md-taerkasten"))
        self.assertEqual(registry.get("generator1", "md-ghorkov").level_ids[0], 7)
        self.assertEqual(registry.get("generator2", "original").targets_by_level[1], (2, 3))

    def test_unknown_profile_reports_available_choices(self) -> None:
        registry = default_profile_registry()

        with self.assertRaisesRegex(ValueError, "Choose one of: original, md-ghorkov, md-taerkasten"):
            registry.get("generator1", "missing")

    def test_generator1_accepts_injected_profile_registry(self) -> None:
        registry = ProfileRegistry.from_mapping({
            "version": 1,
            "generators": {
                "generator1": {
                    "tiny": {
                        "data_profile": "original",
                        "roster_profile": "original",
                        "mission_map_profile": None,
                        "mission_briefing_default": "MB_02.IFF",
                        "mission_debriefing_default": "DB_02.IFF",
                        "player_faction": 1,
                        "level_filenames": ["l0101.ldf"],
                        "target_mode": "next",
                    }
                }
            },
        })

        campaign = Generator1(profile_registry=registry).generate_campaign(seed=1234, campaign_profile="tiny")

        self.assertEqual([level.filename for level in campaign.levels], ["l0101.ldf"])
        self.assertIn("target_level\t=\t0", campaign.levels[0].text)

    def test_generator2_accepts_injected_profile_registry(self) -> None:
        registry = ProfileRegistry.from_mapping({
            "version": 1,
            "generators": {
                "generator2": {
                    "tiny": {
                        "data_profile": "original",
                        "mission_map_profile": None,
                        "mission_briefing_default": "MB_15.IFF",
                        "mission_debriefing_default": "DB_15.IFF",
                        "player_faction": "res",
                        "player_vehicle": 56,
                        "level_ids": [1],
                        "targets_by_level": {"1": []},
                        "enemy_factions": ["sul"],
                        "vehicles_by_faction": {"res": [16], "sul": [73]},
                        "buildings_by_faction": {"res": [11], "sul": [10]},
                        "host_vehicles": {"sul": 61},
                    }
                }
            },
        })

        campaign = Generator2(profile_registry=registry).generate_campaign(seed=1234, campaign_profile="tiny")

        self.assertEqual([level.filename for level in campaign.levels], ["L0101.ldf"])
        self.assertIn("Generator: Generator2", campaign.levels[0].text)

    def test_generator4_accepts_injected_profile_registry(self) -> None:
        registry = ProfileRegistry.from_mapping({
            "version": 1,
            "generators": {
                "generator4": {
                    "tiny": {
                        "data_profile": "original",
                        "roster_profile": "original",
                        "mission_map_profile": None,
                        "mission_briefing_default": "MB_02.IFF",
                        "mission_debriefing_default": "DB_02.IFF",
                        "player_faction": 1,
                        "level_filenames": ["l0202.ldf"],
                        "target_mode": "next",
                    }
                }
            },
        })

        campaign = Generator4(profile_registry=registry).generate_campaign(seed=1234, campaign_profile="tiny")

        self.assertEqual([level.filename for level in campaign.levels], ["L0202.ldf"])
        self.assertIn("Generator: Generator4", campaign.levels[0].text)


if __name__ == "__main__":
    unittest.main()
