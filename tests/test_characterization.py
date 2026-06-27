from __future__ import annotations

import hashlib
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from ualg.constants import FACTION_GHORKOVS, FACTION_TAERKASTEN
from ualg.generator1 import Generator1, Generator1CustomOptions
from ualg.generator2 import Generator2


def _text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _campaign_hash(generator_output) -> str:
    text = "".join(level.filename + "\0" + level.text for level in generator_output.levels)
    return _text_hash(text)


class CharacterizationTests(unittest.TestCase):
    def test_generator1_seeded_single_output(self) -> None:
        level = Generator1().generate_single(seed=424242, difficulty=5, skill=6)

        self.assertEqual(_text_hash(level.text), "da1c01bce71729f8d390eafa6eaa14ec237c1b6b6fb29a9f2771331d9f368e75")

    def test_generator1_seeded_custom_output(self) -> None:
        level = Generator1().generate_custom(
            Generator1CustomOptions(
                seed=778899,
                width=14,
                height=12,
                gate_target_level_id=70,
                gate_key_count=4,
                player_energy=600000,
                ai_slot_present={
                    FACTION_GHORKOVS: [True, False, False],
                    FACTION_TAERKASTEN: [True, True, False],
                },
                ai_slot_energy={FACTION_GHORKOVS: [800000, 0, 0]},
                ai_host_vehicle_id={FACTION_GHORKOVS: 59},
                superitem_flags=[True, True],
                superitem_countdowns={1: 600000, 2: 1200000},
                enabled_vehicles={FACTION_GHORKOVS: [22, 23]},
                enabled_buildings={FACTION_GHORKOVS: [12, 30]},
            )
        )

        self.assertEqual(_text_hash(level.text), "148e7f012c286a2ec4e600486a310f0d0d463e89911ab4521cf9bf33d8e01b1c")

    def test_generator1_seeded_campaign_outputs(self) -> None:
        campaign = Generator1().generate_campaign(seed=13579, difficulty=5)
        md_campaign = Generator1().generate_campaign(seed=1234, campaign_profile="md-ghorkov")

        self.assertEqual(_campaign_hash(campaign), "f93afc3fae8a40e88c6c2aaf82b612013dda07f4cca4b338fe82353a5fd61bf1")
        self.assertEqual(_campaign_hash(md_campaign), "905e9472caad0502003a378d03f9e6add6831f98acb1b4fef0b51b0e7db2f3c0")

    def test_generator2_seeded_outputs(self) -> None:
        single = Generator2().generate_single(seed=112233, level_id=1)
        campaign = Generator2().generate_campaign(seed=998877)
        md_campaign = Generator2().generate_campaign(seed=998877, campaign_profile="md-taerkasten")

        self.assertEqual(_text_hash(single.text), "ab9f5be7cb6195a031a9ee4df12948a2cf340aaea37677e23539768cb0944118")
        self.assertEqual(_campaign_hash(campaign), "b2835debf2ab47804db65a91b0f26423998ca0dc1610329c9f67149e0df36174")
        self.assertEqual(_campaign_hash(md_campaign), "ecfd17c9ad8dea2e27a9d8f1b006ac9c5a3fd28947b95b7bfa76d264643ed1fc")


if __name__ == "__main__":
    unittest.main()
