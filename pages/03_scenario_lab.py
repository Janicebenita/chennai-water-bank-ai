"""Predefined scenarios and judge-controlled stress testing."""

from dataclasses import replace

import plotly.graph_objects as go
import streamlit as st

from src.simulation.scenarios import SCENARIOS
from src.ui.components import decision_card, hero, routing_flow, safety_notice
from src.ui.scenario_controls import run_scenario, show_mathematics
from src.ui.theme import configure_page, render_sidebar_context


configure_page("Scenario Lab")
render_sidebar_context()
hero(
    "TRY BREAKING THE SYSTEM",
    "Change rain, storage, soil, quality and network pressure. The Explainable Decision Engine will show exactly what the Water Bank should do.",
    "JUDGE MODE",
)

predefined_tab, manual_tab = st.tabs(["Predefined demo scenarios", "Manual stress test"])


def render_result(scenario):
    node, state, runoff, decision = run_scenario(scenario)
    st.markdown(f"**Expected tendency:** {scenario.expected_tendency}")
    left, right = st.columns([0.92, 1.25])
    with left:
        decision_card(decision)
        routing_flow(decision.selected_action)
    with right:
        allocation = decision.allocation
        metrics = st.columns(2)
        metrics[0].metric("Calculated runoff", f"{runoff:,.0f} L")
        metrics[1].metric("Locally retained", f"{allocation.retained_l:,.0f} L")
        metrics[0].metric("Stored", f"{allocation.stored_l:,.0f} L")
        metrics[1].metric("Modelled recharge", f"{allocation.recharged_l:,.0f} L")
        metrics[0].metric("Diverted", f"{allocation.diverted_l:,.0f} L")
        metrics[1].metric("Controlled discharge", f"{allocation.controlled_discharge_l:,.0f} L")
        scores = decision.scores
        fig = go.Figure(
            go.Bar(
                x=list(scores.keys())[:3],
                y=list(scores.values())[:3],
                marker_color=["#4aa8ff", "#69d39c", "#f7bd58"],
                text=[f"{value * 100:.0f}%" for value in list(scores.values())[:3]],
            )
        )
        fig.update_layout(
            title="Transparent priority scores",
            height=280,
            yaxis={"range": [0, 1], "gridcolor": "rgba(135,222,205,.1)"},
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#bed1ce",
            margin={"l": 20, "r": 10, "t": 45, "b": 15},
        )
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
    show_mathematics(scenario, runoff, decision)
    return decision


with predefined_tab:
    selected_id = st.selectbox(
        "Load a scenario",
        list(SCENARIOS.keys()),
        format_func=lambda key: SCENARIOS[key].name,
    )
    scenario = SCENARIOS[selected_id]
    st.caption(scenario.description)
    render_result(scenario)
    if selected_id == "extreme_capacity_exhausted":
        st.warning(
            "Distributed Water Bank nodes can reduce or manage part of runoff, but cannot absorb unlimited extreme rainfall."
        )

with manual_tab:
    base = SCENARIOS["multi_retention"]
    st.markdown("#### Configure a synthetic catchment")
    c1, c2, c3 = st.columns(3)
    rainfall = c1.slider("Rainfall depth (mm)", 0.0, 80.0, base.rainfall_mm, 1.0)
    area = c2.slider("Catchment area (m²)", 250.0, 5000.0, base.catchment_area_m2, 50.0)
    coefficient = c3.slider("Runoff coefficient", 0.2, 0.98, base.runoff_coefficient, 0.01)
    tank_capacity = c1.slider("Tank capacity (L)", 0.0, 100000.0, base.storage_capacity_l, 1000.0)
    tank_percent = c2.slider("Tank level (%)", 0, 100, int(base.current_storage_l / base.storage_capacity_l * 100))
    recharge = c3.slider("Recharge capacity (L/hr)", 0.0, 30000.0, base.recharge_capacity_l_per_hour, 500.0)
    soil = c1.slider("Soil saturation (%)", 0, 100, int(base.soil_saturation_percent))
    drain = c2.slider("Drain stress (%)", 0, 100, int(base.drain_stress_percent))
    quality = c3.selectbox("Water quality", ["Clean", "Storage only", "Contaminated"])
    first_flush = c1.toggle("First flush active", value=False)
    recharge_enabled = c2.toggle("Recharge pathway available", value=True)
    turbidity = {"Clean": 3.0, "Storage only": 14.0, "Contaminated": 60.0}[quality]
    ph = 6.0 if quality == "Contaminated" else 7.2
    manual = replace(
        base,
        scenario_id="manual",
        name="Judge-defined stress test",
        description="Manual synthetic inputs",
        rainfall_mm=rainfall,
        rainfall_intensity_mm_hr=rainfall,
        catchment_area_m2=area,
        runoff_coefficient=coefficient,
        storage_capacity_l=tank_capacity,
        current_storage_l=tank_capacity * tank_percent / 100,
        recharge_capacity_l_per_hour=recharge,
        recharge_available=recharge_enabled,
        soil_saturation_percent=float(soil),
        drain_stress_percent=float(drain),
        turbidity_ntu=turbidity,
        ph=ph,
        contamination_detected=quality == "Contaminated",
        first_flush_active=first_flush,
        expected_tendency="Calculated from current inputs",
    )
    if st.button("WHAT SHOULD THE WATER BANK DO?", type="primary", width="stretch"):
        st.session_state["manual_scenario"] = manual
    render_result(st.session_state.get("manual_scenario", manual))

safety_notice()
