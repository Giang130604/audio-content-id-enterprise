from __future__ import annotations

import unittest

import tests._path  # noqa: F401
from audio_id.scoring import MatchAction, classify_score, combine_scores


class ScoringTests(unittest.TestCase):
    def test_score_thresholds(self) -> None:
        self.assertEqual(classify_score(0.90), MatchAction.HIGH_CONFIDENCE)
        self.assertEqual(classify_score(0.70), MatchAction.HUMAN_REVIEW)
        self.assertEqual(classify_score(0.69), MatchAction.NO_ACTION)

    def test_combined_score_weights_alignment_highest(self) -> None:
        score = combine_scores(0.8, 0.8, 1.0)
        self.assertGreater(score, 0.85)
        self.assertLessEqual(score, 1.0)


if __name__ == "__main__":
    unittest.main()

