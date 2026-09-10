import asyncio
from datetime import datetime, timezone
from types import MappingProxyType

from src.agents import CapacityAgent, IncidentMemoryAgent
from src.models.agent_state import SharedAgentState


def _state(semantic_status="disabled"):
    return SharedAgentState(
        request_id="request-1",
        timestamp=datetime.now(timezone.utc),
        zone_id="Judge Lab",
        asset_ids=("WB-TEST-01",),
        user_intent="Assess capacity",
        authoritative_facts=MappingProxyType(
            {
                "node_id": "WB-TEST-01",
                "rainfall_intensity_mm_hr": 20.0,
                "drain_stress_percent": 50.0,
                "contamination_detected": False,
                "first_flush_active": False,
                "available_storage_l": 2500.0,
                "recharge_capacity_l_per_hour": 800.0,
                "recharge_available": True,
                "decision": "STORE",
            }
        ),
        authoritative_fact_refs=("decision:WB-TEST-01:1",),
        moss_query="query",
        semantic_context_status=semantic_status,
    )


def test_capacity_agent_uses_authoritative_numeric_capacity():
    finding = asyncio.run(CapacityAgent().analyze(_state()))

    assert finding.status == "available"
    assert "2,500 L tank headroom" in finding.summary
    assert "800 L/hr" in finding.summary
    assert finding.evidence_refs == ("decision:WB-TEST-01:1",)


def test_incident_agent_does_not_fabricate_when_moss_is_unavailable():
    finding = asyncio.run(IncidentMemoryAgent().analyze(_state("unavailable")))

    assert finding.status == "unavailable"
    assert "temporarily unavailable" in finding.summary
    assert finding.evidence_refs == ()
