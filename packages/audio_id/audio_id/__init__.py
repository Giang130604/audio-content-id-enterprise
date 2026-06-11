"""Shared audio matching primitives for the Audio Content ID MVP."""

from .alignment import alignment_similarity
from .embedding import LightweightEmbeddingModel, cosine_similarity
from .fingerprint import InMemoryFingerprintIndex, fingerprint_signal
from .models import AudioSignal, Candidate, ReferenceAsset, VerificationResult
from .pipeline import AudioContentIdPipeline
from .scoring import MatchAction, classify_score, combine_scores

__all__ = [
    "AudioContentIdPipeline",
    "AudioSignal",
    "Candidate",
    "InMemoryFingerprintIndex",
    "LightweightEmbeddingModel",
    "MatchAction",
    "ReferenceAsset",
    "VerificationResult",
    "alignment_similarity",
    "classify_score",
    "combine_scores",
    "cosine_similarity",
    "fingerprint_signal",
]

