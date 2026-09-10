from src.events import EventContextBuilder
from src.persistence.memory_repository import MemoryRepository
from src.simulation.simulator import DigitalSensorSimulator


def _event():
    node = MemoryRepository.from_demo_data().list_nodes()[0]
    step = DigitalSensorSimulator().simulate_network([node], steps=1)[0]
    return node, step, EventContextBuilder().build(node, step)


def test_meaningful_simulation_step_generates_evidence_linked_water_event():
    node, step, event = _event()

    assert event is not None
    assert event.asset_id == node.node_id
    assert event.zone_id == node.zone
    assert event.metadata["simulated"] is True
    assert "SIMULATED DATA" in event.semantic_text
    assert "not a measured Chennai incident" in event.semantic_text
    assert event.source_refs


def test_water_event_identifier_is_stable_for_same_authoritative_step():
    node, step, event = _event()
    again = EventContextBuilder().build(node, step)

    assert event is not None and again is not None
    assert event.event_id == again.event_id
    assert event.to_dict()["timestamp"].endswith("+00:00")
