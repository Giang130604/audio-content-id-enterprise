from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class MatchAction(StrEnum):
    HIGH_CONFIDENCE = "high_confidence_match"
    HUMAN_REVIEW = "human_review"
    NO_ACTION = "no_action"


@dataclass(frozen=True)
class ScorePolicy:
    high_confidence_threshold: float = 0.90
    review_threshold: float = 0.70
    fingerprint_weight: float = 0.25
    embedding_weight: float = 0.25
    alignment_weight: float = 0.50


DEFAULT_SCORE_POLICY = ScorePolicy()


def clamp_score(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def combine_scores(
    fingerprint_score: float,
    embedding_score: float,
    alignment_score: float,
    policy: ScorePolicy = DEFAULT_SCORE_POLICY,
) -> float:
    """Weighted final confidence for the three-stage matcher."""

    total_weight = (
        policy.fingerprint_weight + policy.embedding_weight + policy.alignment_weight
    )
    if total_weight <= 0:
        raise ValueError("score policy must have positive total weight")

    score = (
        clamp_score(fingerprint_score) * policy.fingerprint_weight
        + clamp_score(embedding_score) * policy.embedding_weight
        + clamp_score(alignment_score) * policy.alignment_weight
    ) / total_weight
    return round(clamp_score(score), 6)


def classify_score(
    final_score: float,
    policy: ScorePolicy = DEFAULT_SCORE_POLICY,
) -> MatchAction:
    score = clamp_score(final_score)
    if score >= policy.high_confidence_threshold:
        return MatchAction.HIGH_CONFIDENCE
    if score >= policy.review_threshold:
        return MatchAction.HUMAN_REVIEW
    return MatchAction.NO_ACTION

