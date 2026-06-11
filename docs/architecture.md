# Audio Content ID Enterprise MVP Architecture

## Goal

Detect whether an uploaded audio or video soundtrack matches registered
copyrighted audio while minimizing false positives.

## Pipeline

1. Filter with acoustic fingerprints.
   - Convert audio to mono PCM.
   - Extract lightweight frame-level fingerprints.
   - Use a posting-list index to reduce the search space to candidates.

2. Embed candidate audio.
   - MVP uses deterministic histogram embeddings for local execution.
   - Production adapter target is LAION-CLAP or a custom triplet-loss model.
   - Vector search target is Qdrant for ANN retrieval.

3. Verify and align.
   - Run DTW over time-series features.
   - This verifies transformed copies such as speed changes or noisy versions.
   - The final score weights fingerprint, embedding, and alignment confidence.

4. Route by confidence.
   - `>= 0.90`: high-confidence match.
   - `0.70 - 0.89`: human review.
   - `< 0.70`: no action.

## Local MVP Runtime

Docker Compose provides:

- FastAPI service for public APIs.
- Worker container as the future Kafka consumer runtime.
- Redpanda as Kafka-compatible streaming infrastructure.
- Qdrant for vector database integration.
- Postgres for metadata and review queues.
- MinIO for object storage.

The first implementation keeps indexes in memory so unit tests and API smoke
tests can run without external infrastructure. The service boundaries and
environment variables are already shaped for replacing in-memory stores with
Postgres, Qdrant, and Redpanda-backed implementations.

## Production Extension Points

- Replace `LightweightEmbeddingModel` with `CLAPEmbeddingModel`.
- Move fingerprints and reference metadata to Postgres.
- Persist audio assets to MinIO.
- Publish ingestion jobs to Redpanda topics.
- Split preprocess, fingerprint, embedding, verification, and review workers.
- Add NVIDIA Triton for GPU-hosted CLAP or custom audio embedding models.

