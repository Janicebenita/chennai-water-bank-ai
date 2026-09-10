from src.config.settings import Settings
from src.persistence.memory_repository import MemoryRepository
from src.persistence.repository import get_repository


def test_memory_backend_loads_demo_nodes():
    repository = get_repository(Settings(data_backend="memory"))
    assert isinstance(repository, MemoryRepository)
    assert len(repository.list_nodes()) >= 6


def test_firestore_failure_falls_back_to_memory(monkeypatch):
    from src.persistence import firestore_repository

    def fail(*args, **kwargs):
        raise RuntimeError("credentials unavailable")

    monkeypatch.setattr(firestore_repository.FirestoreRepository, "__init__", fail)
    repository = get_repository(Settings(data_backend="firestore"))
    assert isinstance(repository, MemoryRepository)
    assert repository.list_nodes()

