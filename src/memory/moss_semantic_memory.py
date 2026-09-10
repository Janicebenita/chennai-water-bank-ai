"""Isolated adapter for the official Moss Python SDK."""

from __future__ import annotations

import json
import logging
from math import isfinite
from threading import RLock
from time import perf_counter_ns
from typing import Any

from moss import DocumentInfo, MossClient, MutationOptions, QueryOptions

from src.models.agent_state import SemanticEvidence
from src.models.water_event import WaterEvent

from .semantic_memory import (
    SemanticIndexResult,
    SemanticMemory,
    SemanticMemoryHealth,
    SemanticRetrievalResult,
)


LOGGER = logging.getLogger(__name__)


def water_event_to_document_info(event: WaterEvent) -> DocumentInfo:
    """Map an evidence-linked WaterEvent to the verified Moss SDK contract."""
    metadata = event.moss_metadata()
    metadata["outcome"] = event.outcome
    return DocumentInfo(
        id=event.event_id,
        text=event.semantic_text,
        metadata=metadata,
        payload=json.dumps({"source_refs": list(event.source_refs)}),
    )


class MossSemanticMemory(SemanticMemory):
    """Index and retrieve WaterEvents through one narrow Moss dependency."""

    def __init__(
        self,
        project_id: str,
        project_key: str,
        index_name: str,
        *,
        client: MossClient | None = None,
    ) -> None:
        if not project_id or not project_key or not index_name:
            raise ValueError("Moss project ID, project key and index name are required")
        self.index_name = index_name
        self._client = client or MossClient(project_id, project_key)
        self._loaded = False
        self._operation_lock = RLock()

    async def health_check(self) -> SemanticMemoryHealth:
        try:
            indexes = await self._client.list_indexes()
            exists = any(item.name == self.index_name for item in indexes)
            return SemanticMemoryHealth(
                True,
                "available" if exists else "index_missing",
                "Moss index is available." if exists else "Moss is reachable; index is not created yet.",
            )
        except Exception as exc:
            self._log_failure("health_check", exc)
            return SemanticMemoryHealth(True, "unavailable", "Moss health check failed.")

    async def index_event(self, event: WaterEvent) -> SemanticIndexResult:
        document = water_event_to_document_info(event)
        try:
            with self._operation_lock:
                indexes = await self._client.list_indexes()
                if any(item.name == self.index_name for item in indexes):
                    await self._client.add_docs(
                        self.index_name,
                        [document],
                        MutationOptions(upsert=True),
                    )
                else:
                    await self._client.create_index(self.index_name, [document], wait=True)
                await self._client.load_index(self.index_name)
                self._loaded = True
            return SemanticIndexResult("indexed", event.event_id)
        except Exception as exc:
            self._loaded = False
            self._log_failure("index_event", exc)
            return SemanticIndexResult("unavailable", event.event_id, "moss_index_failed")

    async def retrieve_context(
        self,
        query: str,
        filters: dict[str, Any] | None = None,
        limit: int = 4,
    ) -> SemanticRetrievalResult:
        query_started: int | None = None
        try:
            with self._operation_lock:
                if not self._loaded:
                    await self._client.load_index(self.index_name)
                    self._loaded = True
                query_started = perf_counter_ns()
                result = await self._client.query(
                    self.index_name,
                    query,
                    QueryOptions(
                        top_k=max(1, min(10, limit)),
                        filter=self._metadata_filter(filters),
                    ),
                )
            elapsed_ms = self._retrieval_latency_ms(result, query_started)
            contexts = tuple(
                SemanticEvidence(
                    evidence_id=item.id,
                    text=item.text,
                    metadata=dict(item.metadata or {}),
                    relevance=float(item.score) if item.score is not None else None,
                )
                for item in result.docs
            )
            return SemanticRetrievalResult("available", contexts, elapsed_ms)
        except Exception as exc:
            elapsed_ms = (
                None
                if query_started is None
                else (perf_counter_ns() - query_started) / 1_000_000
            )
            self._log_failure("retrieve_context", exc)
            return SemanticRetrievalResult(
                "unavailable", (), elapsed_ms, "moss_retrieval_failed"
            )

    @staticmethod
    def _retrieval_latency_ms(result: Any, query_started: int) -> float:
        sdk_value = getattr(result, "time_taken_ms", None)
        try:
            sdk_ms = float(sdk_value)
        except (TypeError, ValueError):
            sdk_ms = float("nan")
        if isfinite(sdk_ms) and sdk_ms >= 0:
            return sdk_ms
        return (perf_counter_ns() - query_started) / 1_000_000

    @staticmethod
    def _metadata_filter(filters: dict[str, Any] | None) -> dict[str, Any] | None:
        if not filters:
            return None
        clauses = [
            {"field": key, "condition": {"$eq": str(value)}}
            for key, value in filters.items()
            if value is not None and str(value).strip()
        ]
        if not clauses:
            return None
        if len(clauses) == 1:
            return clauses[0]
        return {"$and": clauses}

    @staticmethod
    def _log_failure(operation: str, exc: Exception) -> None:
        LOGGER.warning(
            "Moss operation failed",
            extra={"operation": operation, "error_type": type(exc).__name__},
        )
