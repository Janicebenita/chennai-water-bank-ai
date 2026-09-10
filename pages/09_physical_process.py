"""Closed-loop physical, sensing, software, and actuator explainer."""

import streamlit as st

from src.simulation.scenarios import SCENARIOS
from src.ui.components import decision_card, hero, safety_notice, section_heading
from src.ui.physical_process import physical_process_animation
from src.ui.scenario_controls import run_scenario, show_mathematics
from src.ui.theme import configure_page, render_sidebar_context


configure_page("Physical Process")
render_sidebar_context()
hero(
    "HOW THE COMPLETE SYSTEM WORKS",
    "Follow one closed loop from physical rainwater, through simulated field sensing and explainable software intelligence, back to a mechanical routing command and verified physical response.",
    "ANIMATED SYSTEM EXPLAINER",
)

scenario_options = {
    "Store suitable rainwater": "moderate_storage",
    "Use storage and modelled recharge": "multi_retention",
    "Block contaminated first flush": "contaminated_first_flush",
    "Release residual flow safely": "extreme_capacity_exhausted",
}
selected_label = st.selectbox(
    "Choose a routing demonstration",
    list(scenario_options),
)
scenario = SCENARIOS[scenario_options[selected_label]]
node, state, runoff, decision = run_scenario(scenario)
tank_after_l = min(
    node.storage_capacity_l,
    node.current_storage_l + decision.allocation.stored_l,
)

metric_rows = (st.columns(3), st.columns(3))
metric_rows[0][0].metric("Rainfall", f"{state.rainfall_intensity_mm_hr:.1f} mm/hr")
metric_rows[0][1].metric("Incoming runoff", f"{runoff:,.0f} L")
metric_rows[0][2].metric(
    "Tank after routing",
    f"{tank_after_l / node.storage_capacity_l * 100:.0f}%",
)
metric_rows[1][0].metric("Soil saturation", f"{state.soil_saturation_percent:.0f}%")
metric_rows[1][1].metric(
    "Quality",
    state.water_quality_status.value.replace("_", " "),
)
metric_rows[1][2].metric(
    "Selected route",
    decision.selected_action.value.replace("_", " "),
)

physical_process_animation(
    decision,
    tank_fill_percent=tank_after_l / node.storage_capacity_l * 100,
    tank_before_percent=node.current_storage_l / node.storage_capacity_l * 100,
    soil_saturation_percent=state.soil_saturation_percent,
    node_name="Demonstration Water Bank Node",
    rainfall_intensity_mm_hr=state.rainfall_intensity_mm_hr,
    turbidity_ntu=state.turbidity_ntu,
    ph=state.ph,
    flow_rate_l_s=state.incoming_flow_l_per_min / 60.0,
    available_storage_l=node.available_storage_l,
    drain_stress_percent=state.drain_stress_percent,
    quality_status=state.water_quality_status.value,
)

section_heading(
    "DECISION DETAIL",
    "The software decides; controllers and actuators move the water",
    "The animation is driven by the same deterministic decision result shown below.",
)
decision_col, distinction_col = st.columns([1, 1.2])
with decision_col:
    decision_card(decision)
with distinction_col:
    with st.expander("Engineering distinction — text reference", expanded=False):
        st.markdown(
            """
            **Sensors measure:** rainfall, water quality, tank level, soil saturation, flow, and router position.

            **Software decides:** which safe, capacity-constrained route is appropriate.

            **Edge controller / PLC translates:** a software command into interlocked electrical control.

            **Actuator changes:** the motorized valve physically redirects water.

            **Feedback verifies:** flow and position sensors confirm that the commanded physical response occurred.
            """
        )

show_mathematics(scenario, runoff, decision)
safety_notice()
st.caption(
    "SIMULATED DATA · The sensors, commands, controller states, actuator motion, equipment geometry, and animation timing are illustrative. A real installation requires certified instruments and civil, plumbing, treatment, geotechnical, hydrogeological, electrical-control, functional-safety, and regulatory design."
)
