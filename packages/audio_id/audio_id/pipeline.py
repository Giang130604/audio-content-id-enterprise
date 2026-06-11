from __future__ import annotations

from dataclasses import asdict
from uuid import uuid4

from .alignment import alignment_similarity
from .embedding import EmbeddingModel, LightweightEmbeddingModel, cosine_similarity
from .fingerprint import InMemoryFingerprintIndex, fingerprint_signal
from .models import AudioSignal, ReferenceAsset, VerificationResult
from .scoring import DEFAULT_SCORE_POLICY, ScorePolicy, classify_score, combine_scores


class AudioContentIdPipeline:
    """In-memory implementation of the Filter -> Embed -> Verify pipeline."""

    def __init__(
        self,
        embedding_model: EmbeddingModel | None = None,
        score_policy: ScorePolicy = DEFAULT_SCORE_POLICY,
    ) -> None:
        self.embedding_model = embedding_model or LightweightEmbeddingModel()
        self.score_policy = score_policy
        self.fingerprint_index = InMemoryFingerprintIndex()
        self.references: dict[str, ReferenceAsset] = {}
        self.reference_embeddings: dict[str, tuple[float, ...]] = {}

    def register_asset(
        self,
        asset_id: str,
        title: str,
        owner: str,
        signal: AudioSignal,
        metadata: dict | None = None,
    ) -> ReferenceAsset:
        if not asset_id:
            raise ValueError("asset_id is required")
        reference = ReferenceAsset(
            asset_id=asset_id,
            title=title,
            owner=owner,
            signal=signal,
            metadata=metadata or {},
        )
        fingerprints = fingerprint_signal(signal)
        self.references[asset_id] = reference
        self.reference_embeddings[asset_id] = self.embedding_model.embed(signal)
        self.fingerprint_index.add(asset_id, fingerprints)
        return reference

    def detect(
        self,
        query: AudioSignal,
        detection_id: str | None = None,
        top_k: int = 5,
    ) -> tuple[VerificationResult, ...]:
        detection_id = detection_id or str(uuid4())
        query_fingerprints = fingerprint_signal(query)
        query_embedding = self.embedding_model.embed(query)
        candidates = self.fingerprint_index.query(query_fingerprints, top_k=top_k)

        results: list[VerificationResult] = []
        for candidate in candidates:
            reference = self.references[candidate.asset_id]
            reference_embedding = self.reference_embeddings[candidate.asset_id]
            embedding_score = cosine_similarity(reference_embedding, query_embedding)
            alignment_score = alignment_similarity(reference.signal, query)
            final_score = combine_scores(
                candidate.fingerprint_score,
                embedding_score,
                alignment_score,
                self.score_policy,
            )
            action = classify_score(final_score, self.score_policy)
            results.append(
                VerificationResult(
                    detection_id=detection_id,
                    asset_id=candidate.asset_id,
                    action=action.value,
                    final_score=final_score,
                    fingerprint_score=candidate.fingerprint_score,
                    embedding_score=round(embedding_score, 6),
                    alignment_score=alignment_score,
                    matched_offsets=candidate.offset_votes,
                    metadata={
                        "reference": {
                            "title": reference.title,
                            "owner": reference.owner,
                            **reference.metadata,
                        }
                    },
                )
            )

        results.sort(key=lambda item: item.final_score, reverse=True)
        return tuple(results)

    def result_to_dict(self, result: VerificationResult) -> dict:
        return asdict(result)

