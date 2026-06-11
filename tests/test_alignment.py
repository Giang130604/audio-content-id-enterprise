from __future__ import annotations

import unittest

import tests._path  # noqa: F401
from audio_id.alignment import alignment_similarity
from tests.helpers import speed_change, synthetic_reference


class AlignmentTests(unittest.TestCase):
    def test_identical_audio_aligns_strongly(self) -> None:
        reference = synthetic_reference()
        self.assertGreaterEqual(alignment_similarity(reference, reference), 0.99)

    def test_speed_changed_audio_still_aligns(self) -> None:
        reference = synthetic_reference()
        query = speed_change(reference, 1.2)
        self.assertGreaterEqual(alignment_similarity(reference, query), 0.70)


if __name__ == "__main__":
    unittest.main()

