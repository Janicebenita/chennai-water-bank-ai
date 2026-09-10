import asyncio

from src.agents.base import AdvisoryAgent
from src.memory.null_semantic_memory import NullSemanticMemory
from src.memory.semantic_memory import (
    SemanticIndexResult,
    SemanticMemory,
    SemanticMemoryHealth,
    SemanticRetrievalResult,
)
from src.models.agent_state import AgentFinding, SemanticEvidence
from src.orchestration import WaterBankOrchestrator
from src.persistence.memory_repository import MemoryRepository
from src.simulation.simulator import DigitalSensorSimulator


def _node_and_step():
    node = MemoryRepository.from_demo_data().list_nodes()[0]
    step = DigitalSensorSimulator().simulate_network([node], steps=1)[0]
    return node, step


class RetrievedMemory(SemanticMemory):
    async def health_check(self):
        return SemanticMemoryHealth(True, "available", "ok")

    async def index_event(self, event):
        return SemanticIndexResult("indexed", event.event_id)

    async def retrieve_context(self, query, filters=None, limit=4):
        return SemanticRetrievalResult(
            "available",
            (
                SemanticEvidence(
                    "evidence-1",
                    "SIMULATED DATA comparison event",
                    {"simulated": True},
                    0.88,
                ),
            ),
            2.5,
        )


class FailingAgent(AdvisoryAgent):
    name = "broken"

    async def analyze(self, state):
        raise RuntimeError("failure")


class MutatingAgent(AdvisoryAgent):
    name = "mutating"

    async def analyze(self, state):
        state.authoritative_facts["decision"] = "OVERWRITTEN"
        return AgentFinding(self.name, "available", "bad", "bad")


class TrackingMemory(RetrievedMemory):
    def __init__(self):
        self.retrieve_calls = 0
        self.last_query = ""

    async def retrieve_context(self, query, filters=None, limit=4):
        self.retrieve_calls += 1
        self.last_query = query
        return await super().retrieve_context(query, filters, limit)


class ContextCaptureAgent(AdvisoryAgent):
    def __init__(self, name, seen):
        self.name = name
        self.seen = seen

    async def analyze(self, state):
        self.seen.append((id(state.moss_context), state.moss_context_refs))
        return AgentFinding(
            self.name,
            "available",
            "context captured",
            "advisory only",
            state.moss_context_refs,
        )


def test_orchestrator_merges_evidence_and_defaults_human_review_to_pending():
    node, step = _node_and_step()
    result = asyncio.run(WaterBankOrchestrator(RetrievedMemory()).analyze(node, step))

    assert result.moss_status == "available"
    assert result.moss_results_count == 1
    assert set(result.agent_findings) == {
        "rain_risk",
        "incident_memory",
        "capacity",
        "asset_maintenance",
    }
    assert result.human_approval_state == "pending"
    assert result.latency.moss_retrieval_ms == 2.5
    assert result.latency.total_request_ms >= 0


def test_moss_disabled_preserves_existing_deterministic_decision():
    node, step = _node_and_step()
    result = asyncio.run(
        WaterBankOrchestrator(NullSemanticMemory()).analyze(node, step)
    )

    assert result.moss_status == "disabled"
    assert result.live_facts["decision"] == step.decision.selected_action.value
    assert result.semantic_context == ()
    assert "deterministic" in result.recommendation


def test_agent_failures_are_isolated_and_reported():
    node, step = _node_and_step()
    result = asyncio.run(
        WaterBankOrchestrator(RetrievedMemory(), agents=(FailingAgent(),)).analyze(
            node, step
        )
    )

    assert result.agent_findings["broken"].status == "failed"
    assert any("failed" in warning for warning in result.warnings)
    assert result.live_facts["decision"] == step.decision.selected_action.value


def test_semantic_or_agent_content_cannot_overwrite_authoritative_facts():
    node, step = _node_and_step()
    expected = step.decision.selected_action.value
    result = asyncio.run(
        WaterBankOrchestrator(RetrievedMemory(), agents=(MutatingAgent(),)).analyze(
            node, step
        )
    )

    assert result.agent_findings["mutating"].status == "failed"
    assert result.live_facts["decision"] == expected


def test_one_retrieval_is_reused_by_all_four_agents():
    node, step = _node_and_step()
    memory = TrackingMemory()
    seen = []
    names = ("rain_risk", "incident_memory", "capacity", "asset_maintenance")
    agents = tuple(ContextCaptureAgent(name, seen) for name in names)

    result = asyncio.run(
        WaterBankOrchestrator(memory, agents=agents).analyze(node, step)
    )

    assert memory.retrieve_calls == 1
    assert len(seen) == 4
    assert len({context_id for context_id, _ in seen}) == 1
    assert all(refs == ("evidence-1",) for _, refs in seen)
    assert set(result.agent_findings) == set(names)
    assert "storage" in memory.last_query
    assert "recharge capacity" in memory.last_query
    assert "event type" in memory.last_query
    assert "asset availability" in memory.last_query
