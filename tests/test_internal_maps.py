from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from ualg.core.maps import filled_rows, set_cell, set_cell_if_in_bounds


class InternalMapHelperTests(unittest.TestCase):
    def test_filled_rows_masks_values_and_creates_distinct_rows(self) -> None:
        rows = filled_rows(2, 2, 300)

        self.assertEqual(rows, [[44, 44], [44, 44]])
        rows[0][0] = 1
        self.assertEqual(rows[1][0], 44)

    def test_cell_writes_apply_byte_mask(self) -> None:
        rows = filled_rows(2, 2)

        set_cell(rows, 1, 0, 511)
        written = set_cell_if_in_bounds(rows, 2, 2, 0, 1, -1)
        skipped = set_cell_if_in_bounds(rows, 2, 2, 3, 1, 99)

        self.assertTrue(written)
        self.assertFalse(skipped)
        self.assertEqual(rows, [[0, 255], [255, 0]])


if __name__ == "__main__":
    unittest.main()
