from __future__ import annotations

import hashlib
import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Iterable

from .models import AudioSignal, Candidate


@dataclass(frozen=True)
class Fingerprint:
    token: str
    offset: int


def _frames(samples: tuple[float, ...], frame_size: int, hop_size: int) -> Iterable[tuple[int, tuple[float, ...]]]:
    if frame_size <= 0 or hop_size <= 0:
        raise ValueError("frame_size and hop_size must be positive")
    if len(samples) < frame_size:
        return
    for start in range(0, len(samples) - frame_size + 1, hop_size):
        yield start // hop_size, samples[start : start + frame_size]


def _frame_features(frame: tuple[float, ...]) -> tuple[int, int, int]:
    energy = math.sqrt(sum(sample * sample for sample in frame) / len(frame))
    zero_crossings = sum(
        1
        for left, right in zip(frame, frame[1:])
        if (left < 0 <= right) or (right < 0 <= left)
    )
    delta = sum(abs(right - left) for left, right in zip(frame, frame[1:])) / max(
        1, len(frame) - 1
    )

    energy_bin = min(15, int(energy * 24))
    zcr_bin = min(15, int((zero_crossings / len(frame)) * 64))
    delta_bin = min(15, int(delta * 32))
    return energy_bin, zcr_bin, delta_bin


def _stable_token(features: tuple[int, int, int]) -> str:
    payload = f"{features[0]}:{features[1]}:{features[2]}".encode("ascii")
    return hashlib.blake2b(payload, digest_size=6).hexdigest()


def fingerprint_signal(
    signal: AudioSignal,
    frame_size: int | None = None,
    hop_size: int | None = None,
    silence_floor: float = 0.01,
) -> tuple[Fingerprint, ...]:
    """Create lightweight acoustic fingerprints from frame-level envelopes.

    This MVP implementation favors deterministic behavior and low dependency
    cost. Production should replace this with a peak-pair spectrogram
    fingerprint index.
    """

    if not signal.samples:
        return tuple()

    frame_size = frame_size or max(256, int(signal.sample_rate * 0.064))
    hop_size = hop_size or max(128, frame_size // 2)
    fingerprints: list[Fingerprint] = []

    for offset, frame in _frames(signal.samples, frame_size, hop_size):
        energy = math.sqrt(sum(sample * sample for sample in frame) / len(frame))
        if energy < silence_floor:
            continue
        fingerprints.append(Fingerprint(_stable_token(_frame_features(frame)), offset))

    return tuple(fingerprints)


class InMemoryFingerprintIndex:
    """Simple posting-list index for local MVP and tests."""

    def __init__(self) -> None:
        self._postings: dict[str, list[tuple[str, int]]] = defaultdict(list)
        self._asset_sizes: dict[str, int] = {}

    def add(self, asset_id: str, fingerprints: Iterable[Fingerprint]) -> None:
        items = tuple(fingerprints)
        self._asset_sizes[asset_id] = len(items)
        for fingerprint in items:
            self._postings[fingerprint.token].append((asset_id, fingerprint.offset))

    def query(
        self,
        fingerprints: Iterable[Fingerprint],
        top_k: int = 10,
    ) -> tuple[Candidate, ...]:
        query_items = tuple(fingerprints)
        if not query_items:
            return tuple()

        offset_votes: dict[str, Counter[int]] = defaultdict(Counter)
        total_votes: Counter[str] = Counter()
        for query_fingerprint in query_items:
            for asset_id, reference_offset in self._postings.get(
                query_fingerprint.token, []
            ):
                offset_delta = reference_offset - query_fingerprint.offset
                offset_votes[asset_id][offset_delta] += 1
                total_votes[asset_id] += 1

        candidates: list[Candidate] = []
        for asset_id, votes in total_votes.items():
            strongest_offsets = offset_votes[asset_id].most_common(5)
            reference_size = max(1, self._asset_sizes.get(asset_id, votes))
            denominator = max(1, min(reference_size, len(query_items)))
            consensus = strongest_offsets[0][1] if strongest_offsets else 0
            score = min(1.0, max(votes / denominator, consensus / denominator))
            candidates.append(
                Candidate(
                    asset_id=asset_id,
                    fingerprint_score=round(score, 6),
                    offset_votes=tuple(strongest_offsets),
                )
            )

        candidates.sort(key=lambda item: item.fingerprint_score, reverse=True)
        return tuple(candidates[:top_k])

