from src.models.decision import DecisionAction
from src.simulation.scenarios import SCENARIOS
from src.ui.physical_process import TEMPLATE_PATH, _command_for
from src.ui.scenario_controls import run_scenario


def test_all_decision_actions_have_explicit_hardware_commands():
    expected = {
        DecisionAction.STORE: ("ROUTE_TO_STORE", "STORE"),
        DecisionAction.RECHARGE: ("ROUTE_TO_RECHARGE", "RECHARGE"),
        DecisionAction.STORE_AND_RECHARGE: ("SPLIT_STORE_RECHARGE", "SPLIT"),
        DecisionAction.DIVERT: ("ISOLATE_AND_DIVERT", "DIVERT"),
        DecisionAction.CONTROLLED_DISCHARGE: (
            "OPEN_CONTROLLED_DISCHARGE",
            "DISCHARGE",
        ),
    }

    for action, (command, router_target) in expected.items():
        actual_command, actual_target, _ = _command_for(action)
        assert (actual_command, actual_target) == (command, router_target)


def test_explainer_template_preserves_required_closed_loop_and_disclosures():
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    required_labels = (
        "1 — PHYSICAL PROCESS",
        "2 — SENSE",
        "3 — COMMUNICATE",
        "4 — ANALYZE",
        "5 — DECISION",
        "6 — SOFTWARE COMMANDS HARDWARE",
        "7 — MECHANICAL ACTION",
        "8 — FEEDBACK / VERIFICATION",
        "EDGE CONTROLLER / IoT GATEWAY",
        "Motor Driver / Relay",
        "MOTORIZED ROUTER",
        "COMMAND VERIFIED ✓",
        "NO PHYSICAL IOT SENSOR CONNECTED",
        "SIMULATED SENSOR VALUES",
        "certified, site-specific testing",
        "ENGINEERING DISTINCTION · FOLLOW THE SIGNAL",
        "1 · SENSOR · MEASURE",
        "2 · SOFTWARE · DECIDE",
        "3 · EDGE / PLC · TRANSLATE",
        "4 · ACTUATOR · ACT",
        "5 · FEEDBACK · VERIFY",
    )

    for label in required_labels:
        assert label in template


def test_scenario_sensor_flow_matches_current_runoff_and_duration():
    scenario = SCENARIOS["moderate_storage"]
    _, state, runoff, _ = run_scenario(scenario)

    assert state.incoming_flow_l_per_min == runoff / scenario.duration_minutes
