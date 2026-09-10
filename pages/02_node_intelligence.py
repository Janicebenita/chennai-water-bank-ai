"""Node-level state, explanation and active water-routing path."""

import pandas as pd
import streamlit as st

from src.ui.components import decision_card, hero, latest_steps, routing_flow, safety_notice, section_heading
from src.ui.physical_process import physical_process_animation
from src.ui.runtime import get_active_steps, load_nodes
from src.ui.theme import configure_page, render_sidebar_context


configure_page("Node Intelligence")
render_sidebar_context()
hero(
    "NODE INTELLIGENCE",
    "Inspect the current simulated state, safety gate and litre-by-litre routing decision at one demonstration catchment.",
    "LOCAL DECISION LAYER",
)

nodes = load_nodes()
steps = get_active_steps()
latest = latest_steps(steps)
selected_name = st.selectbox("Choose demonstration node", [node.name for node in nodes])
node = next(item for item in nodes if item.name == selected_name)
step = latest[node.node_id]
state = step.sensor_state
decision = step.decision

left, right = st.columns([0.9, 1.35])
with left:
    decision_card(decision)
    st.markdown("#### Why?")
    for reason in decision.reason_codes:
        st.write(f"✓ {reason.replace('_', ' ').title()}")
    st.markdown("#### Why not the alternatives?")
    for action, reason in decision.rejected_alternatives.items():
        st.caption(f"**{action.replace('_', ' ')}** — {reason}")
with right:
    section_heading("CURRENT STATE", node.name, f"{node.zone} · DEMONSTRATION NODE · SIMULATED DATA")
    metrics = st.columns(3)
    metrics[0].metric("Rainfall", f"{state.rainfall_intensity_mm_hr:.1f} mm/hr")
    metrics[1].metric("Runoff this pulse", f"{decision.allocation.incoming_l:,.0f} L")
    metrics[2].metric("Tank level", f"{step.storage_after_l / node.storage_capacity_l * 100:.0f}%")
    metrics = st.columns(3)
    metrics[0].metric("Modelled recharge", f"{decision.allocation.recharged_l:,.0f} L")
    metrics[1].metric("Soil saturation", f"{state.soil_saturation_percent:.0f}%")
    metrics[2].metric("Drain stress", f"{state.drain_stress_percent:.0f}%")
    quality = pd.DataFrame(
        [
            {"Indicator": "Quality status", "Simulated value": state.water_quality_status.value},
            {"Indicator": "Turbidity", "Simulated value": f"{state.turbidity_ntu:.1f} NTU"},
            {"Indicator": "pH", "Simulated value": f"{state.ph:.1f}"},
            {"Indicator": "First flush", "Simulated value": "ACTIVE" if state.first_flush_active else "CLEARED"},
        ]
    )
    st.dataframe(quality, hide_index=True, width="stretch")

section_heading("ACTIVE ROUTE", "Water routing")
routing_flow(decision.selected_action)
allocation_cols = st.columns(4)
allocation_cols[0].metric("Incoming", f"{decision.allocation.incoming_l:,.0f} L")
allocation_cols[1].metric("Stored", f"{decision.allocation.stored_l:,.0f} L")
allocation_cols[2].metric("Recharged", f"{decision.allocation.recharged_l:,.0f} L")
allocation_cols[3].metric("Downstream", f"{decision.allocation.downstream_l:,.0f} L")

section_heading(
    "SIMULATED PHYSICAL PROCESS",
    "From rain to the active destination",
    "The illuminated route and litres are tied to this node's current simulated decision.",
)
physical_process_animation(
    decision,
    tank_fill_percent=step.storage_after_l / node.storage_capacity_l * 100,
    tank_before_percent=step.storage_before_l / node.storage_capacity_l * 100,
    soil_saturation_percent=state.soil_saturation_percent,
    node_name=node.name,
    rainfall_intensity_mm_hr=state.rainfall_intensity_mm_hr,
    turbidity_ntu=state.turbidity_ntu,
    ph=state.ph,
    flow_rate_l_s=state.incoming_flow_l_per_min / 60.0,
    available_storage_l=max(0.0, node.storage_capacity_l - step.storage_before_l),
    drain_stress_percent=state.drain_stress_percent,
    quality_status=state.water_quality_status.value,
)

with st.expander("Constraints applied"):
    for constraint in decision.constraints:
        st.write(f"• {constraint}")
    st.code(f"Mass-balance error = {decision.allocation.mass_balance_error_l:.8f} L", language="text")
safety_notice()
