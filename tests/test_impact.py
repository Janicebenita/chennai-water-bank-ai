from src.impact.calculator import aggregate_impacts, impact_from_decision
from src.simulation.scenarios import SCENARIOS
from src.ui.scenario_controls import run_scenario


def test_retained_is_stored_plus_recharged():
    _, _, _, decision = run_scenario(SCENARIOS["multi_retention"])
    impact = impact_from_decision(decision)
    assert impact.retained_l == impact.stored_l + impact.recharged_l
    assert impact.immediate_downstream_l < impact.stormwater_received_l


def test_network_aggregation_sums_allocations():
    decisions = [run_scenario(item)[3] for item in SCENARIOS.values()]
    combined = aggregate_impacts(impact_from_decision(item) for item in decisions)
    assert combined.stormwater_received_l == sum(item.allocation.incoming_l for item in decisions)

