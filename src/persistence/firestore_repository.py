"""Bounded Firestore operations with explicit seeded-memory fallback."""

from __future__ import annotations

import logging
import random
import time
from threading import RLock
from typing import Any, Callable, TypeVar
from uuid import uuid4

from google.api_core import exceptions
from google.auth.exceptions import GoogleAuthError

from src.config.settings import Settings
from src.models.node import WaterBankNode

from .memory_repository import MemoryRepository
from .repository import Repository

LOGGER = logging.getLogger(__name__)
T = TypeVar("T")
TRANSIENT_ERRORS = (
    exceptions.ServiceUnavailable,
    exceptions.DeadlineExceeded,
    exceptions.ResourceExhausted,
    exceptions.Aborted,
    exceptions.InternalServerError,
    ConnectionError,
    TimeoutError,
)


class FirestoreRepository(Repository):
    backend_name = "firestore"
    allowed_event_collections = {
        "simulation_runs",
        "node_events",
        "decisions",
        "impact_snapshots",
    }

    def __init__(self, settings: Settings) -> None:
        from google.cloud import firestore

        self.settings = settings
        self._memory = MemoryRepository.from_demo_data()
        self._lock = RLock()
        self.client = firestore.Client(
            project=settings.gcp_project, database=settings.firestore_database
        )

    def _execute(
        self, operation: str, remote: Callable[[], T], local: Callable[[], T]
    ) -> T:
        # Streamlit caches this repository across sessions; fallback must be sticky.
        with self._lock:
            if self.degraded_reason:
                return local()
            attempts = max(1, min(5, self.settings.firestore_max_attempts))
            for attempt in range(1, attempts + 1):
                try:
                    return remote()
                except (
                    exceptions.GoogleAPICallError,
                    GoogleAuthError,
                    ConnectionError,
                    TimeoutError,
                ) as exc:
                    transient = isinstance(exc, TRANSIENT_ERRORS)
                    # Never serialize exception messages, credentials, IDs or payloads.
                    if transient and attempt < attempts:
                        cap = (
                            min(
                                max(
                                    0, min(10000, self.settings.firestore_max_delay_ms)
                                ),
                                max(
                                    0,
                                    min(5000, self.settings.firestore_initial_delay_ms),
                                )
                                * 2 ** (attempt - 1),
                            )
                            / 1000
                        )
                        delay = random.uniform(cap / 2, cap)
                        LOGGER.warning(
                            "Firestore operation retry",
                            extra={
                                "operation": operation,
                                "attempt": attempt,
                                "delay_seconds": delay,
                                "reason": "transient_failure",
                            },
                        )
                        time.sleep(delay)
                        continue
                    self.backend_name = "memory"
                    self.degraded_reason = (
                        "Firestore retry limit reached."
                        if transient
                        else "Firestore access unavailable."
                    )
                    LOGGER.error(
                        "Persistence: MEMORY FALLBACK",
                        extra={
                            "operation": operation,
                            "attempt": attempt,
                            "reason": "retry_exhausted"
                            if transient
                            else "access_unavailable",
                        },
                    )
                    return local()
            raise AssertionError("Unreachable retry state")

    @property
    def _rpc_options(self) -> dict[str, Any]:
        # Disable SDK retries so the configured attempt budget remains authoritative.
        return {
            "retry": None,
            "timeout": max(1, min(30, self.settings.firestore_timeout_seconds)),
        }

    def health_check(self) -> None:
        def read() -> None:
            next(
                iter(
                    self.client.collection("nodes").limit(1).stream(**self._rpc_options)
                ),
                None,
            )

        self._execute("health_check", read, lambda: None)

    def list_nodes(self) -> list[WaterBankNode]:
        def read() -> list[WaterBankNode]:
            nodes = [
                WaterBankNode.from_dict(item.to_dict())
                for item in self.client.collection("nodes").stream(**self._rpc_options)
            ]
            # Replace the mirror only after a complete read.
            self._memory.save_nodes(nodes)
            return nodes

        return self._execute("list_nodes", read, self._memory.list_nodes)

    def save_nodes(self, nodes: list[WaterBankNode]) -> None:
        def write() -> None:
            batch = self.client.batch()
            for node in nodes:
                batch.set(
                    self.client.collection("nodes").document(node.node_id),
                    node.to_dict(),
                )
            batch.commit(**self._rpc_options)
            self._memory.save_nodes(nodes)

        self._execute("save_nodes", write, lambda: self._memory.save_nodes(nodes))

    def save_event(self, collection: str, payload: dict[str, Any]) -> str:
        if collection not in self.allowed_event_collections:
            raise ValueError("Unsupported event collection")
        # Reuse one ID across retries, including ambiguous write acknowledgements.
        event_id = str(uuid4())

        def write() -> str:
            self.client.collection(collection).document(event_id).set(
                payload, **self._rpc_options
            )
            return event_id

        return self._execute(
            "save_event", write, lambda: self._memory.save_event(collection, payload)
        )
