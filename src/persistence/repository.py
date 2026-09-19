"""Repository contract and backend selection."""

from __future__ import annotations

from abc import ABC, abstractmethod
import logging
from typing import Any

from src.config.settings import Settings, get_settings
from src.models.node import WaterBankNode


class Repository(ABC):
    backend_name = "abstract"
    degraded_reason: str | None = None

    @property
    def persistence_status(self) -> str:
        return "MEMORY FALLBACK" if self.degraded_reason else self.backend_name.upper()

    @abstractmethod
    def list_nodes(self) -> list[WaterBankNode]:
        pass

    @abstractmethod
    def save_nodes(self, nodes: list[WaterBankNode]) -> None:
        pass

    @abstractmethod
    def save_event(self, collection: str, payload: dict[str, Any]) -> str:
        pass


def get_repository(settings: Settings | None = None) -> Repository:
    """Select Firestore when requested, falling back to seeded memory on any error."""
    active = settings or get_settings()
    if active.data_backend == "firestore":
        try:
            from .firestore_repository import FirestoreRepository

            repository = FirestoreRepository(active)
            repository.health_check()
            return repository
        except Exception:
            # Demo resilience is intentional: missing credentials must not blank the app.
            from .memory_repository import MemoryRepository

            fallback = MemoryRepository.from_demo_data()
            fallback.degraded_reason = "Firestore initialization unavailable."
            logging.getLogger(__name__).error(
                "Persistence: MEMORY FALLBACK",
                extra={
                    "operation": "initialize",
                    "reason": "firestore_initialization_unavailable",
                },
            )
            return fallback
    from .memory_repository import MemoryRepository

    return MemoryRepository.from_demo_data()
