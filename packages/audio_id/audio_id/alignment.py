from __future__ import annotations

import math

from .models import AudioSignal


def extract_alignment_features(
    signal: AudioSignal,
    frame_size: int | None = None,
    hop_size: int | None = None,
) -> tuple[tuple[float, float, float], ...]:
    if not signal.samples:
        return tuple()

    frame_size = frame_size or max(128, int(signal.sample_rate * 0.032))
    hop_size = hop_size or max(64, frame_size // 2)
    features: list[tuple[float, float, float]] = []
    samples = signal.samples

    if len(samples) < frame_size:
        frame_size = len(samples)
        hop_size = len(samples)

    for start in range(0, len(samples) - frame_size + 1, hop_size):
        frame = samples[start : start + frame_size]
        energy = math.sqrt(sum(sample * sample for sample in frame) / len(frame))
        mean_abs = sum(abs(sample) for sample in frame) / len(frame)
        delta = sum(abs(right - left) for left, right in zip(frame, frame[1:])) / max(
            1, len(frame) - 1
        )
        features.append((energy, mean_abs, delta))

    return tuple(features)


def _downsample(
    features: tuple[tuple[float, float, float], ...],
    max_length: int,
) -> tuple[tuple[float, float, float], ...]:
    if len(features) <= max_length:
        return features
    stride = math.ceil(len(features) / max_length)
    return tuple(features[index] for index in range(0, len(features), stride))


def _feature_distance(
    left: tuple[float, float, float],
    right: tuple[float, float, float],
) -> float:
    return math.sqrt(sum((a - b) * (a - b) for a, b in zip(left, right)))


def dtw_distance(
    reference: tuple[tuple[float, float, float], ...],
    query: tuple[tuple[float, float, float], ...],
    max_length: int = 512,
) -> float:
    if not reference or not query:
        return 1.0

    reference = _downsample(reference, max_length)
    query = _downsample(query, max_length)

    previous = [math.inf for _ in range(len(query) + 1)]
    previous[0] = 0.0

    for ref_feature in reference:
        current = [math.inf for _ in range(len(query) + 1)]
        for column, query_feature in enumerate(query, start=1):
            cost = _feature_distance(ref_feature, query_feature)
            current[column] = cost + min(
                previous[column], current[column - 1], previous[column - 1]
            )
        previous = current

    path_length = max(len(reference), len(query))
    return previous[-1] / path_length


def alignment_similarity(reference: AudioSignal, query: AudioSignal) -> float:
    distance = dtw_distance(
        extract_alignment_features(reference),
        extract_alignment_features(query),
    )
    similarity = math.exp(-6.0 * distance)
    return round(max(0.0, min(1.0, similarity)), 6)

