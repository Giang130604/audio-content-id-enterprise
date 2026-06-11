from __future__ import annotations

import math
from typing import Protocol

from .fingerprint import fingerprint_signal
from .models import AudioSignal


class EmbeddingModel(Protocol):
    def embed(self, signal: AudioSignal) -> tuple[float, ...]:
        ...


def normalize_vector(vector: tuple[float, ...]) -> tuple[float, ...]:
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return tuple(0.0 for _ in vector)
    return tuple(value / norm for value in vector)


def cosine_similarity(left: tuple[float, ...], right: tuple[float, ...]) -> float:
    if len(left) != len(right):
        raise ValueError("vectors must have the same dimensions")
    if not left:
        return 0.0
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    score = sum(a * b for a, b in zip(left, right)) / (left_norm * right_norm)
    return max(0.0, min(1.0, score))


class LightweightEmbeddingModel:
    """Deterministic local embedding used when CLAP is unavailable."""

    def __init__(self, dimensions: int = 64) -> None:
        if dimensions <= 0:
            raise ValueError("dimensions must be positive")
        self.dimensions = dimensions

    def embed(self, signal: AudioSignal) -> tuple[float, ...]:
        buckets = [0.0 for _ in range(self.dimensions)]
        fingerprints = fingerprint_signal(signal)
        if not fingerprints:
            return tuple(buckets)

        for fingerprint in fingerprints:
            bucket = int(fingerprint.token[:8], 16) % self.dimensions
            buckets[bucket] += 1.0

        return normalize_vector(tuple(buckets))


class CLAPEmbeddingModel:
    """Optional LAION-CLAP adapter for production embedding search."""

    def __init__(self, checkpoint_path: str | None = None) -> None:
        try:
            import laion_clap  # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                "CLAPEmbeddingModel requires the optional `ml` dependencies"
            ) from exc

        self._model = laion_clap.CLAP_Module(enable_fusion=False)
        if checkpoint_path:
            self._model.load_ckpt(checkpoint_path)

    def embed(self, signal: AudioSignal) -> tuple[float, ...]:
        raise NotImplementedError(
            "Wire CLAP waveform preprocessing here once model weights are available."
        )

