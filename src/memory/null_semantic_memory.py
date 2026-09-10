"""No-op semantic memory used when Moss is disabled or misconfigured."""

from __future__ import annotations

from typing import Any

from src.models.water_event import WaterEvent

from .semantic_memory import (
    SemanticIndexResult,
    SemanticMemory,
    SemanticMemoryHealth,
    SemanticRetrievalResult,
)


class NullSemanticMemory(SemanticMemory):
    def __init__(self, status: str = "disabled", message: str = "Moss is disabled.") -> None:
        self.status = status
        self.message = message

    async def health_check(self) -> SemanticMemoryHealth:
        return SemanticMemoryHealth(False, self.status, self.message)

    async def index_event(self, event: WaterEvent) -> SemanticIndexResult:
        return SemanticIndexResult(self.status, event.event_id)

    async def retrieve_context(
        self,
        query: str,
        filters: dict[str, Any] | None = None,
        limit: int = 4,
    ) -> SemanticRetrievalResult:
        return SemanticRetrievalResult(self.status)
