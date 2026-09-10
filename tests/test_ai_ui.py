from src.models.agent_state import SemanticEvidence
from src.ui.ai_command_center import _evidence_rows


def test_ui_evidence_rows_include_timestamp_and_provenance():
    evidence = SemanticEvidence(
        "event-123",
        "SIMULATED DATA WaterEvent",
        {
            "timestamp": "2026-09-10T10:00:00+00:00",
            "event_type": "ASSET_UNAVAILABLE",
            "zone_id": "Judge Lab",
            "asset_id": "WB-TEST-01",
            "action": "DIVERT",
            "outcome": "No recharge was modelled.",
        },
        0.875,
    )

    rows = _evidence_rows((evidence,))

    assert rows == [
        {
            "WaterEvent ID": "event-123",
            "Timestamp": "2026-09-10T10:00:00+00:00",
            "Event type": "ASSET_UNAVAILABLE",
            "Zone": "Judge Lab",
            "Asset": "WB-TEST-01",
            "Relevance": "0.875",
            "Action": "DIVERT",
            "Outcome": "No recharge was modelled.",
        }
    ]
