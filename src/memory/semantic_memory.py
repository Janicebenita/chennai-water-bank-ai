"""Provider-neutral semantic-memory contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from src.models.agent_state import SemanticEvidence
from src.models.water_event import WaterEvent


@dataclass(frozen=True)
class SemanticMemoryHealth:
    enabled: bool
    status: str
    message: str


@dataclass(frozen=True)
class SemanticIndexResult:
    status: str
    event_id: str | None = None
    error_code: str | None = None


@dataclass(frozen=True)
class SemanticRetrievalResult:
    status: str
    contexts: tuple[SemanticEvidence, ...] = ()
    retrieval_ms: float | None = None
    error_code: str | None = None


class SemanticMemory(ABC):
    @abstractmethod
    async def health_check(self) -> SemanticMemoryHealth:
        pass

    @abstractmethod
    async def index_event(self, event: WaterEvent) -> SemanticIndexResult:
        pass

    @abstractmethod
    async def retrieve_context(
        self,
        query: str,
        filters: dict[str, Any] | None = None,
        limit: int = 4,
    ) -> SemanticRetrievalResult:
        pass
