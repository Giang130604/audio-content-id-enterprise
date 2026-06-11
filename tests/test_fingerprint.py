from __future__ import annotations

import unittest

import tests._path  # noqa: F401
from audio_id.fingerprint import InMemoryFingerprintIndex, fingerprint_signal
from tests.helpers import add_noise, synthetic_reference


class FingerprintTests(unittest.TestCase):
    def test_index_returns_noisy_reference_candidate(self) -> None:
        reference = synthetic_reference()
        query = add_noise(reference)

        index = InMemoryFingerprintIndex()
        index.add("asset-1", fingerprint_signal(reference))
        candidates = index.query(fingerprint_signal(query))

        self.assertTrue(candidates)
        self.assertEqual(candidates[0].asset_id, "asset-1")
        self.assertGreaterEqual(candidates[0].fingerprint_score, 0.7)


if __name__ == "__main__":
    unittest.main()

