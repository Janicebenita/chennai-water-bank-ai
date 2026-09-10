import asyncio
from datetime import datetime, timezone
from types import MappingProxyType

from src.agents import (
    AssetMaintenanceAgent,
    CapacityAgent,
    IncidentMemoryAgent,
    RainRiskAgent,
)
from src.models.agent_state import SemanticEvidence, SharedAgentState


def _state(semantic_status="disabled", contexts=()):
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
        moss_context=contexts,
        moss_context_refs=tuple(item.evidence_id for item in contexts),
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


def _evidence(evidence_id, event_type, *, asset_id="WB-TEST-01"):
    return SemanticEvidence(
        evidence_id,
        "SIMULATED DATA evidence",
        {
            "zone_id": "Judge Lab",
            "asset_id": asset_id,
            "event_type": event_type,
            "action": "DIVERT",
            "outcome": "120 L remained downstream.",
            "simulated": "true",
        },
        0.91,
    )


def test_rain_risk_agent_uses_bounded_context_without_replacing_live_values():
    contexts = (
        _evidence("risk-1", "HIGH_DRAIN_STRESS"),
        _evidence("risk-2", "WATER_QUALITY_INTERVENTION"),
        _evidence("risk-3", "CAPACITY_CONSTRAINT"),
    )

    finding = asyncio.run(RainRiskAgent().analyze(_state("available", contexts)))

    assert "rainfall is 20.0 mm/hr" in finding.summary
    assert "closest evidence risk-1" in finding.summary
    assert "outcome 120 L remained downstream" in finding.summary
    assert finding.evidence_refs[-2:] == ("risk-1", "risk-2")


def test_incident_memory_preserves_evidence_actions_outcomes_and_ids():
    contexts = (_evidence("incident-1", "HISTORICAL_INCIDENT"),)

    finding = asyncio.run(
        IncidentMemoryAgent().analyze(_state("available", contexts))
    )

    assert "incident-1: action DIVERT" in finding.summary
    assert "outcome 120 L remained downstream" in finding.summary
    assert finding.evidence_refs == ("incident-1",)


def test_asset_agent_filters_unrelated_semantic_evidence():
    contexts = (
        _evidence("maintenance-1", "MAINTENANCE_EVENT"),
        _evidence("other-asset", "ASSET_FAILURE", asset_id="WB-OTHER"),
        _evidence("rain-only", "HIGH_DRAIN_STRESS"),
    )

    finding = asyncio.run(
        AssetMaintenanceAgent().analyze(_state("available", contexts))
    )

    assert finding.status == "available"
    assert finding.evidence_refs[-1] == "maintenance-1"
    assert "other-asset" not in finding.evidence_refs
    assert "rain-only" not in finding.evidence_refs


def test_asset_agent_explicitly_reports_no_relevant_maintenance_evidence():
    contexts = (_evidence("rain-only", "HIGH_DRAIN_STRESS"),)

    finding = asyncio.run(
        AssetMaintenanceAgent().analyze(_state("available", contexts))
    )

    assert finding.status == "limited"
    assert "No relevant maintenance evidence retrieved." in finding.summary
    assert finding.evidence_refs == ("decision:WB-TEST-01:1",)
