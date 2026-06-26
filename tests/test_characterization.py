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

        self.assertEqual(_campaign_hash(campaign), "efba36a160d00ac744a0537fdfebbb3cc9b3b998b92a17817efab04f71d43582")
        self.assertEqual(_campaign_hash(md_campaign), "388f7e83dbc41af79ed90900a25d913063a0a6a2837e0321d88a63a950eaea53")

    def test_generator2_seeded_outputs(self) -> None:
        single = Generator2().generate_single(seed=112233, level_id=1)
        campaign = Generator2().generate_campaign(seed=998877)
        md_campaign = Generator2().generate_campaign(seed=998877, campaign_profile="md-taerkasten")

        self.assertEqual(_text_hash(single.text), "054e34e1f1df475d95378b622822dc838d421bdc5e311d86a8380732742627c6")
        self.assertEqual(_campaign_hash(campaign), "ddeb8cd6e5d01b156a5f8909f602b7890be3db80872297326df8238a12e0d592")
        self.assertEqual(_campaign_hash(md_campaign), "3518cbf6f3bdd684ea8e9689a8119ffa467aec42b80718c9b41ecf3c7e30bcf1")


if __name__ == "__main__":
    unittest.main()
