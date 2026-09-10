"""Repository contract and backend selection."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from src.config.settings import Settings, get_settings
from src.models.node import WaterBankNode


class Repository(ABC):
    backend_name = "abstract"

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
            pass
    from .memory_repository import MemoryRepository

    return MemoryRepository.from_demo_data()

