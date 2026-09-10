from src.models.decision import DecisionAction
from src.persistence.memory_repository import MemoryRepository
from src.simulation.simulator import DigitalSensorSimulator, SensorDataSource


def test_simulator_implements_replaceable_sensor_interface():
    assert isinstance(DigitalSensorSimulator(), SensorDataSource)


def test_network_storm_produces_multiple_node_decisions_and_balances_mass():
    nodes = MemoryRepository.from_demo_data().list_nodes()
    steps = DigitalSensorSimulator().simulate_network(nodes)
    assert len(steps) == len(nodes) * 8
    assert {step.node_id for step in steps} == {node.node_id for node in nodes}
    assert all(abs(step.decision.allocation.mass_balance_error_l) < 1e-7 for step in steps)
    assert any(step.decision.selected_action == DecisionAction.DIVERT for step in steps)
    assert any(step.decision.allocation.retained_l > 0 for step in steps)
    latest = {step.node_id: step for step in steps}
    assert {step.decision.selected_action for step in latest.values()} == set(DecisionAction)
