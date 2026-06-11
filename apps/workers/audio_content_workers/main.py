from __future__ import annotations

import logging
import os
import signal
import time
from dataclasses import dataclass


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("audio-content-workers")


@dataclass(frozen=True)
class WorkerSettings:
    redpanda_brokers: str = os.getenv("REDPANDA_BROKERS", "localhost:9092")
    qdrant_url: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    postgres_dsn: str = os.getenv(
        "POSTGRES_DSN", "postgresql://audio_id:audio_id@localhost:5432/audio_id"
    )
    poll_interval_seconds: float = float(os.getenv("WORKER_POLL_INTERVAL", "5"))


class WorkerRuntime:
    """Placeholder runtime for Kafka/Qdrant/Postgres-backed workers.

    The local MVP keeps matching in-memory through the API. This runtime is the
    production extension point for splitting preprocess, fingerprint, embedding,
    and verification stages into independently scalable consumers.
    """

    def __init__(self, settings: WorkerSettings) -> None:
        self.settings = settings
        self._running = True

    def stop(self, *_args) -> None:
        self._running = False

    def run(self) -> None:
        logger.info("worker starting with brokers=%s", self.settings.redpanda_brokers)
        logger.info("qdrant=%s postgres=%s", self.settings.qdrant_url, self.settings.postgres_dsn)
        while self._running:
            logger.info("worker idle: waiting for pipeline topics")
            time.sleep(self.settings.poll_interval_seconds)
        logger.info("worker stopped")


def main() -> None:
    runtime = WorkerRuntime(WorkerSettings())
    signal.signal(signal.SIGTERM, runtime.stop)
    signal.signal(signal.SIGINT, runtime.stop)
    runtime.run()


if __name__ == "__main__":
    main()

