"""Exercise real adapter logic with mocked SDK boundaries and no network."""

from unittest.mock import MagicMock

import pytest
from google.api_core.exceptions import PermissionDenied, ServiceUnavailable

from src.config.settings import Settings, get_settings
from src.persistence.firestore_repository import FirestoreRepository
from src.persistence.memory_repository import MemoryRepository
from src.persistence.repository import get_repository


@pytest.fixture
def adapter(monkeypatch):
    client = MagicMock()
    monkeypatch.setattr("google.cloud.firestore.Client", lambda **kwargs: client)
    sleep = MagicMock()
    monkeypatch.setattr("src.persistence.firestore_repository.time.sleep", sleep)
    monkeypatch.setattr(
        "src.persistence.firestore_repository.random.uniform", lambda low, high: high
    )
    repo = FirestoreRepository(Settings())
    return repo, client, sleep


def documents(nodes):
    return [MagicMock(to_dict=MagicMock(return_value=node.to_dict())) for node in nodes]


def test_successful_read_and_health_do_not_retry(adapter):
    repo, client, sleep = adapter
    nodes = MemoryRepository.from_demo_data().list_nodes()[:1]
    client.collection.return_value.stream.return_value = documents(nodes)
    repo.health_check()
    assert repo.list_nodes() == nodes
    assert repo.persistence_status == "FIRESTORE"
    sleep.assert_not_called()
    client.collection.return_value.stream.assert_called_once_with(retry=None, timeout=5)


def test_transient_read_recovers_on_second_attempt(adapter):
    repo, client, sleep = adapter
    nodes = MemoryRepository.from_demo_data().list_nodes()[:1]
    client.collection.return_value.stream.side_effect = [
        ServiceUnavailable("offline"),
        documents(nodes),
    ]
    assert repo.list_nodes() == nodes
    assert client.collection.return_value.stream.call_count == 2
    sleep.assert_called_once_with(0.2)
    assert repo.degraded_reason is None


def test_exhaustion_uses_seeded_memory_and_stays_degraded(adapter, caplog):
    repo, client, sleep = adapter
    client.collection.return_value.stream.side_effect = ServiceUnavailable(
        "private-example-token"
    )
    assert len(repo.list_nodes()) == 6
    assert repo.persistence_status == "MEMORY FALLBACK"
    assert repo.backend_name == "memory"
    assert client.collection.return_value.stream.call_count == 3
    assert [call.args[0] for call in sleep.call_args_list] == [0.2, 0.4]
    repo.list_nodes()
    repo.health_check()
    assert client.collection.return_value.stream.call_count == 3
    assert "private-example-token" not in caplog.text + str(repo.degraded_reason)
    assert all(
        "private-example-token" not in str(record.__dict__) for record in caplog.records
    )
    assert caplog.records[-1].reason == "retry_exhausted"


def test_backoff_is_exponential_and_capped(adapter):
    repo, client, sleep = adapter
    repo.settings = Settings(
        firestore_max_attempts=5,
        firestore_initial_delay_ms=200,
        firestore_max_delay_ms=500,
    )
    client.collection.return_value.stream.side_effect = ServiceUnavailable("offline")
    repo.list_nodes()
    assert [call.args[0] for call in sleep.call_args_list] == [0.2, 0.4, 0.5, 0.5]
    assert client.collection.return_value.stream.call_count == 5


def test_jitter_stays_inside_backoff_bounds(adapter, monkeypatch):
    repo, client, sleep = adapter
    jitter = MagicMock(side_effect=lambda low, high: low)
    monkeypatch.setattr("src.persistence.firestore_repository.random.uniform", jitter)
    client.collection.return_value.stream.side_effect = ServiceUnavailable("offline")
    repo.list_nodes()
    assert [call.args for call in jitter.call_args_list] == [(0.1, 0.2), (0.2, 0.4)]
    assert [call.args[0] for call in sleep.call_args_list] == [0.1, 0.2]


def test_permission_denied_falls_back_without_retry(adapter):
    repo, client, sleep = adapter
    client.collection.return_value.stream.side_effect = PermissionDenied(
        "private account detail"
    )
    assert repo.list_nodes()
    sleep.assert_not_called()
    assert repo.degraded_reason == "Firestore access unavailable."


def test_programming_error_propagates_without_retry(adapter):
    repo, client, sleep = adapter
    client.collection.return_value.stream.side_effect = TypeError("bug")
    with pytest.raises(TypeError):
        repo.list_nodes()
    sleep.assert_not_called()
    assert repo.degraded_reason is None
    with pytest.raises(ValueError, match="Unsupported event collection"):
        repo.save_event("invalid", {})


def test_partial_stream_failure_preserves_last_complete_snapshot(adapter):
    repo, client, _ = adapter
    nodes = MemoryRepository.from_demo_data().list_nodes()[:2]
    client.collection.return_value.stream.return_value = documents(nodes)
    repo.list_nodes()

    def broken_stream(**kwargs):
        yield documents(nodes[:1])[0]
        raise ServiceUnavailable("interrupted")

    client.collection.return_value.stream.side_effect = broken_stream
    assert repo.list_nodes() == nodes


def test_node_writes_retry_and_update_memory_mirror(adapter):
    repo, client, sleep = adapter
    nodes = MemoryRepository.from_demo_data().list_nodes()[:1]
    client.batch.return_value.commit.side_effect = [ServiceUnavailable("offline"), None]
    repo.save_nodes(nodes)
    assert client.batch.return_value.commit.call_count == 2
    sleep.assert_called_once_with(0.2)
    client.collection.return_value.stream.side_effect = ServiceUnavailable("offline")
    assert repo.list_nodes() == nodes
    nodes[0].name = "Updated in fallback"
    repo.save_nodes(nodes)
    assert repo.list_nodes()[0].name == "Updated in fallback"


def test_failed_node_write_is_saved_in_memory(adapter):
    repo, client, _ = adapter
    nodes = MemoryRepository.from_demo_data().list_nodes()[:1]
    client.batch.return_value.commit.side_effect = ServiceUnavailable("offline")
    repo.save_nodes(nodes)
    assert repo.list_nodes() == nodes
    assert repo.persistence_status == "MEMORY FALLBACK"


def test_event_retry_reuses_document_id(adapter):
    repo, client, _ = adapter
    client.collection.return_value.document.return_value.set.side_effect = [
        ServiceUnavailable("lost ack"),
        None,
    ]
    event_id = repo.save_event("node_events", {"simulated": True})
    calls = client.collection.return_value.document.call_args_list
    assert len(calls) == 2
    assert all(call.args == (event_id,) for call in calls)
    client.collection.return_value.document.return_value.set.assert_called_with(
        {"simulated": True}, retry=None, timeout=5
    )


def test_event_exhaustion_persists_payload_in_memory(adapter):
    repo, client, _ = adapter
    client.collection.return_value.document.return_value.set.side_effect = (
        ServiceUnavailable("offline")
    )
    event_id = repo.save_event("node_events", {"simulated": True})
    assert repo._memory._events["node_events"] == [{"id": event_id, "simulated": True}]
    assert repo.persistence_status == "MEMORY FALLBACK"


def test_factory_reports_startup_failure_without_exception_text(monkeypatch, caplog):
    def unavailable(**kwargs):
        raise RuntimeError("private-example-token")

    monkeypatch.setattr("google.cloud.firestore.Client", unavailable)
    repo = get_repository(Settings(data_backend="firestore"))
    assert isinstance(repo, MemoryRepository)
    assert repo.persistence_status == "MEMORY FALLBACK"
    assert "private-example-token" not in caplog.text + str(repo.degraded_reason)


def test_health_failure_keeps_factory_result_explicitly_degraded(adapter):
    _, client, _ = adapter
    client.collection.return_value.limit.return_value.stream.side_effect = (
        ServiceUnavailable("offline")
    )
    repo = get_repository(Settings(data_backend="firestore"))
    assert repo.persistence_status == "MEMORY FALLBACK"
    assert repo.list_nodes()


def test_retry_settings_are_bounded(monkeypatch):
    monkeypatch.setenv("FIRESTORE_MAX_ATTEMPTS", "900")
    monkeypatch.setenv("FIRESTORE_INITIAL_DELAY_MS", "-1")
    monkeypatch.setenv("FIRESTORE_MAX_DELAY_MS", "bad")
    monkeypatch.setenv("FIRESTORE_TIMEOUT_SECONDS", "900")
    get_settings.cache_clear()
    try:
        settings = get_settings()
        assert settings.firestore_max_attempts == 5
        assert settings.firestore_initial_delay_ms == 0
        assert settings.firestore_max_delay_ms == 2000
        assert settings.firestore_timeout_seconds == 30
    finally:
        get_settings.cache_clear()
