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
