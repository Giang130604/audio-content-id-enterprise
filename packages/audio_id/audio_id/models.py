from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class AudioSignal:
    """In-memory mono audio signal normalized to floats in [-1.0, 1.0]."""

    samples: tuple[float, ...]
    sample_rate: int

    def __post_init__(self) -> None:
        if self.sample_rate <= 0:
            raise ValueError("sample_rate must be positive")
        object.__setattr__(self, "samples", tuple(float(x) for x in self.samples))

    @property
    def duration_seconds(self) -> float:
        if not self.samples:
            return 0.0
        return len(self.samples) / self.sample_rate


@dataclass(frozen=True)
class ReferenceAsset:
    asset_id: str
    title: str
    owner: str
    signal: AudioSignal
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Candidate:
    asset_id: str
    fingerprint_score: float
    offset_votes: tuple[tuple[int, int], ...] = field(default_factory=tuple)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class VerificationResult:
    detection_id: str
    asset_id: str
    action: str
    final_score: float
    fingerprint_score: float
    embedding_score: float
    alignment_score: float
    matched_offsets: tuple[tuple[int, int], ...] = field(default_factory=tuple)
    metadata: dict[str, Any] = field(default_factory=dict)

