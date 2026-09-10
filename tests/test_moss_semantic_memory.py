import asyncio
from types import SimpleNamespace

from src.config.settings import Settings
from src.memory import get_semantic_memory
from src.memory.moss_semantic_memory import MossSemanticMemory
from src.memory.null_semantic_memory import NullSemanticMemory
from src.models.water_event import WaterEvent


def _event():
    from datetime import datetime, timezone

    return WaterEvent(
        event_id="event-1",
        timestamp=datetime.now(timezone.utc),
        asset_id="WB-TEST-01",
        zone_id="Judge Lab",
        event_type="STORAGE_ROUTING",
        operational_summary="SIMULATED DATA storage event.",
        risk_context="No verified physical risk context.",
        action="STORE",
        outcome="100 L stored.",
        semantic_text="SIMULATED DATA storage event at a fictional demonstration node.",
        source_refs=("decision:WB-TEST-01:1",),
        metadata={"simulated": True, "severity": "moderate"},
    )


class FakeMossClient:
    def __init__(self, *, has_index=True, fail=False):
        self.has_index = has_index
        self.fail = fail
        self.created = []
        self.added = []
        self.loaded = []
        self.query_options = None

    async def list_indexes(self):
        if self.fail:
            raise RuntimeError("unavailable")
        return [SimpleNamespace(name="events")] if self.has_index else []

    async def create_index(self, name, docs, wait=True):
        self.created.append((name, docs, wait))
        self.has_index = True

    async def add_docs(self, name, docs, options=None):
        self.added.append((name, docs, options))

    async def load_index(self, name):
        if self.fail:
            raise RuntimeError("unavailable")
        self.loaded.append(name)

    async def query(self, name, query, options=None):
        if self.fail:
            raise RuntimeError("unavailable")
        self.query_options = options
        return SimpleNamespace(
            docs=[
                SimpleNamespace(
                    id="event-1",
                    text="SIMULATED DATA evidence",
                    metadata={"simulated": True, "zone_id": "Judge Lab"},
                    score=0.91,
                )
            ]
        )


def test_moss_disabled_mode_uses_noop_memory():
    memory = get_semantic_memory(Settings(moss_enabled=False))
    result = asyncio.run(memory.retrieve_context("query"))

    assert isinstance(memory, NullSemanticMemory)
    assert result.status == "disabled"
    assert result.contexts == ()


def test_moss_enabled_without_credentials_falls_back_without_startup_failure():
    memory = get_semantic_memory(Settings(moss_enabled=True))
    result = asyncio.run(memory.retrieve_context("query"))

    assert isinstance(memory, NullSemanticMemory)
    assert result.status == "unavailable"
    assert result.contexts == ()


def test_moss_adapter_uses_real_index_add_load_and_query_contracts():
    client = FakeMossClient(has_index=True)
    memory = MossSemanticMemory("project", "key", "events", client=client)

    indexed = asyncio.run(memory.index_event(_event()))
    retrieved = asyncio.run(
        memory.retrieve_context("storage event", {"zone_id": "Judge Lab"}, 3)
    )

    assert indexed.status == "indexed"
    assert client.added and client.loaded == ["events"]
    assert retrieved.status == "available"
    assert retrieved.contexts[0].evidence_id == "event-1"
    assert retrieved.retrieval_ms is not None and retrieved.retrieval_ms >= 0
    assert client.query_options.top_k == 3
    assert client.query_options.filter == {
        "field": "zone_id",
        "condition": {"$eq": "Judge Lab"},
    }


def test_moss_adapter_creates_missing_index_with_first_event():
    client = FakeMossClient(has_index=False)
    memory = MossSemanticMemory("project", "key", "events", client=client)

    result = asyncio.run(memory.index_event(_event()))

    assert result.status == "indexed"
    assert client.created[0][0] == "events"
    assert client.created[0][2] is True


def test_moss_failure_returns_unavailable_without_evidence():
    memory = MossSemanticMemory(
        "project", "key", "events", client=FakeMossClient(fail=True)
    )

    indexed = asyncio.run(memory.index_event(_event()))
    retrieved = asyncio.run(memory.retrieve_context("query"))

    assert indexed.status == "unavailable"
    assert retrieved.status == "unavailable"
    assert retrieved.contexts == ()
    assert retrieved.error_code == "moss_retrieval_failed"
