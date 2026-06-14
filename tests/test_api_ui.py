from __future__ import annotations

import io
import unittest
import wave

import tests._path  # noqa: F401
from apps.api.audio_content_api import main as api_main
from audio_id.pipeline import AudioContentIdPipeline
from audio_id.scoring import MatchAction
from tests.helpers import synthetic_reference


def wav_bytes() -> bytes:
    signal = synthetic_reference()
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(signal.sample_rate)
        frames = bytearray()
        for sample in signal.samples:
            value = int(max(-1.0, min(1.0, sample)) * 32767)
            frames.extend(value.to_bytes(2, byteorder="little", signed=True))
        wav_file.writeframes(bytes(frames))
    return buffer.getvalue()


class ApiUiTests(unittest.TestCase):
    def setUp(self) -> None:
        from fastapi.testclient import TestClient

        api_main.pipeline = AudioContentIdPipeline()
        api_main.detections.clear()
        api_main.review_cases.clear()
        self.client = TestClient(api_main.app)

    def register_reference(self) -> dict:
        response = self.client.post(
            "/v1/assets",
            data={
                "asset_id": "asset-api-test",
                "title": "API Test Track",
                "owner": "Test Owner",
            },
            files={"file": ("reference.wav", wav_bytes(), "audio/wav")},
        )
        self.assertEqual(response.status_code, 200)
        return response.json()

    def test_list_assets_after_registration(self) -> None:
        self.register_reference()

        response = self.client.get("/v1/assets")

        self.assertEqual(response.status_code, 200)
        assets = response.json()
        self.assertEqual(len(assets), 1)
        self.assertEqual(assets[0]["asset_id"], "asset-api-test")

    def test_detection_history_after_high_confidence_match(self) -> None:
        self.register_reference()

        detection = self.client.post(
            "/v1/detections",
            files={"file": ("query.wav", wav_bytes(), "audio/wav")},
        )
        self.assertEqual(detection.status_code, 200)
        payload = detection.json()
        self.assertTrue(payload["matches"])
        self.assertEqual(
            payload["matches"][0]["action"],
            MatchAction.HIGH_CONFIDENCE.value,
        )

        history = self.client.get("/v1/detections")
        self.assertEqual(history.status_code, 200)
        self.assertEqual(history.json()[0]["detection_id"], payload["detection_id"])

    def test_review_decision_closes_open_case(self) -> None:
        api_main.review_cases["review-test"] = {
            "detection_id": "review-test",
            "status": "open",
            "match": {"action": MatchAction.HUMAN_REVIEW.value, "final_score": 0.75},
            "decision": None,
        }

        response = self.client.post(
            "/v1/review-cases/review-test/decision",
            json={
                "decision": "approve",
                "reviewer": "local-tester",
                "notes": "Looks valid",
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "closed")
        self.assertEqual(payload["decision"]["decision"], "approve")

    def test_ui_and_static_assets_load(self) -> None:
        page = self.client.get("/ui")
        script = self.client.get("/ui/static/app.js")
        styles = self.client.get("/ui/static/styles.css")

        self.assertEqual(page.status_code, 200)
        self.assertIn("Audio Content ID Console", page.text)
        self.assertEqual(script.status_code, 200)
        self.assertIn("registerAsset", script.text)
        self.assertEqual(styles.status_code, 200)
        self.assertIn(".score-grid", styles.text)


if __name__ == "__main__":
    unittest.main()

