from __future__ import annotations

import unittest

import tests._path  # noqa: F401
from audio_id.pipeline import AudioContentIdPipeline
from audio_id.scoring import MatchAction
from tests.helpers import add_noise, synthetic_reference


class PipelineTests(unittest.TestCase):
    def test_exact_reference_is_high_confidence(self) -> None:
        reference = synthetic_reference()
        pipeline = AudioContentIdPipeline()
        pipeline.register_asset("asset-1", "Reference Track", "Rights Owner", reference)

        results = pipeline.detect(reference, detection_id="det-1")

        self.assertTrue(results)
        self.assertEqual(results[0].asset_id, "asset-1")
        self.assertEqual(results[0].action, MatchAction.HIGH_CONFIDENCE.value)
        self.assertGreaterEqual(results[0].final_score, 0.90)

    def test_noisy_reference_is_review_or_better(self) -> None:
        reference = synthetic_reference()
        query = add_noise(reference)
        pipeline = AudioContentIdPipeline()
        pipeline.register_asset("asset-1", "Reference Track", "Rights Owner", reference)

        results = pipeline.detect(query, detection_id="det-2")

        self.assertTrue(results)
        self.assertIn(
            results[0].action,
            {MatchAction.HUMAN_REVIEW.value, MatchAction.HIGH_CONFIDENCE.value},
        )
        self.assertGreaterEqual(results[0].final_score, 0.70)


if __name__ == "__main__":
    unittest.main()

