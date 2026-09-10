import pytest

from src.models.decision import DecisionAction
from src.simulation.scenarios import SCENARIOS
from src.ui.scenario_controls import run_scenario


def test_unsafe_water_never_recharges():
    _, _, _, result = run_scenario(SCENARIOS["contaminated_first_flush"])
    assert result.selected_action == DecisionAction.DIVERT
    assert result.allocation.recharged_l == 0


def test_moderate_rain_uses_storage():
    _, _, _, result = run_scenario(SCENARIOS["moderate_storage"])
    assert result.selected_action == DecisionAction.STORE
    assert result.allocation.stored_l > 0


def test_nearly_full_tank_uses_recharge_family():
    _, _, _, result = run_scenario(SCENARIOS["heavy_recharge"])
    assert result.selected_action in {
        DecisionAction.RECHARGE,
        DecisionAction.STORE_AND_RECHARGE,
    }
    assert result.allocation.recharged_l > 0


def test_full_tank_and_saturated_soil_controls_discharge():
    _, _, _, result = run_scenario(SCENARIOS["extreme_capacity_exhausted"])
    assert result.selected_action == DecisionAction.CONTROLLED_DISCHARGE
    assert result.allocation.controlled_discharge_l > 0


@pytest.mark.parametrize("scenario", SCENARIOS.values())
def test_scenario_allocations_are_nonnegative_and_balanced(scenario):
    _, _, _, result = run_scenario(scenario)
    allocation = result.allocation
    assert allocation.stored_l >= 0
    assert allocation.recharged_l >= 0
    assert allocation.diverted_l >= 0
    assert allocation.controlled_discharge_l >= 0
    assert allocation.mass_balance_error_l == pytest.approx(0, abs=1e-7)

