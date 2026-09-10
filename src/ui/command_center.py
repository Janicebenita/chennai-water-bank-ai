"""Main hackathon command center."""

from __future__ import annotations

import time

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.models.decision import DecisionAction
from src.ui.ai_command_center import render_ai_operations
from src.ui.components import (
    before_after_chart,
    hero,
    kpi_card,
    latest_steps,
    node_map,
    safety_notice,
    section_heading,
)
from src.ui.runtime import (
    get_active_steps,
    load_nodes,
    network_impact,
    reset_storm,
    run_full_storm,
)


def render_command_center() -> None:
    hero(
        "CHENNAI WATER BANK",
        "Distributed Intelligence for Urban Rainwater — retain a measurable portion of suitable stormwater closer to where it falls.",
    )
    nodes = load_nodes()

    controls = st.columns([2.2, 1, 1, 1.15])
    simulate = controls[0].button(
        "SIMULATE CHENNAI STORM", type="primary", width="stretch"
    )
    start = controls[1].button("Start", width="stretch")
    pause = controls[2].button("Pause", width="stretch")
    speed = controls[3].selectbox(
        "Simulation speed", ["1x", "5x", "10x", "30x"], index=1, label_visibility="collapsed"
    )
    if pause:
        st.session_state["storm_running"] = False
    if simulate or start:
        st.session_state["storm_running"] = True
        progress = st.progress(0, text=f"Routing simulated storm pulses at {speed}…")
        for index in range(8):
            progress.progress((index + 1) / 8, text=f"Storm pulse {index + 1} of 8 · {speed}")
            time.sleep(0.025)
        run_full_storm()
        st.session_state["storm_running"] = False
        progress.empty()
        st.toast("Simulated storm completed. Network impact report updated.", icon="💧")

    with st.expander("Simulation controls", expanded=False):
        left, middle, right = st.columns(3)
        left.write(f"Status: **{'RUNNING' if st.session_state.get('storm_running') else 'READY'}**")
        middle.write(f"Speed: **{speed}**")
        if right.button("Reset simulation", width="stretch"):
            reset_storm()
            st.rerun()

    steps = get_active_steps()
    latest = latest_steps(steps)
    impact = network_impact(steps)
    current_rainfall = max(
        (step.sensor_state.rainfall_intensity_mm_hr for step in latest.values()), default=0.0
    )
    available_capacity = sum(
        max(0.0, node.storage_capacity_l - latest[node.node_id].storage_after_l)
        if node.node_id in latest
        else node.available_storage_l
        for node in nodes
    )
    risk_nodes = sum(
        1
        for step in latest.values()
        if step.sensor_state.drain_stress_percent >= 80
        or step.decision.selected_action
        in {DecisionAction.DIVERT, DecisionAction.CONTROLLED_DISCHARGE}
    )

    st.markdown("### Network pulse")
    row1 = st.columns(5)
    with row1[0]:
        kpi_card("Active Water Bank Nodes", str(len(nodes)), "SIMULATED NETWORK")
    with row1[1]:
        kpi_card("Current Rainfall", f"{current_rainfall:.1f} mm/hr")
    with row1[2]:
        kpi_card("Stormwater Received", f"{impact.stormwater_received_l / 1000:,.1f} kL")
    with row1[3]:
        kpi_card("Water Retained", f"{impact.retained_l / 1000:,.1f} kL")
    with row1[4]:
        kpi_card("Runoff Retention", f"{impact.retention_percentage:.1f}%")

    row2 = st.columns(5)
    with row2[0]:
        kpi_card("Stored", f"{impact.stored_l / 1000:,.1f} kL")
    with row2[1]:
        kpi_card("Recharged", f"{impact.recharged_l / 1000:,.1f} kL", "MODELLED PATHWAY")
    with row2[2]:
        kpi_card("Diverted / Discharged", f"{impact.immediate_downstream_l / 1000:,.1f} kL")
    with row2[3]:
        kpi_card("Available Tank Capacity", f"{available_capacity / 1000:,.1f} kL")
    with row2[4]:
        kpi_card("Nodes at Risk", str(risk_nodes), "CURRENT SIMULATED STATE")

    section_heading(
        "CITY VIEW",
        "Distributed node intelligence",
        "Each marker is a fictional demonstration node, not an existing Chennai installation.",
    )
    map_col, allocation_col = st.columns([1.55, 1])
    with map_col:
        node_map(nodes, steps)
    with allocation_col:
        fig = go.Figure(
            go.Pie(
                labels=["Stored", "Modelled recharge", "Diverted", "Controlled discharge"],
                values=[
                    impact.stored_l,
                    impact.recharged_l,
                    impact.diverted_l,
                    impact.controlled_discharge_l,
                ],
                hole=0.62,
                marker_colors=["#4aa8ff", "#69d39c", "#ff6b6b", "#f7bd58"],
                textinfo="percent",
            )
        )
        fig.update_layout(
            title="How modelled runoff was routed",
            height=420,
            margin={"l": 10, "r": 10, "t": 55, "b": 10},
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#bed1ce",
            legend={"orientation": "h", "y": -0.08},
        )
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
        safety_count = sum(
            1
            for step in steps
            if "SAFETY_GATE_OVERRIDE" in step.decision.reason_codes
            or "FIRST_FLUSH_DIVERSION" in step.decision.reason_codes
        )
        st.info(f"{safety_count} safety interventions blocked unsuitable water from direct recharge.")

    section_heading(
        "NODE DECISIONS",
        "One storm. Different local responses.",
        "Different catchments, tank levels, soil conditions and safety states produce different decisions.",
    )
    table_rows = []
    for node in nodes:
        step = latest.get(node.node_id)
        if not step:
            continue
        table_rows.append(
            {
                "Demonstration node": node.name,
                "Zone": node.zone,
                "Decision": step.decision.selected_action.value.replace("_", " "),
                "Rain (mm/hr)": round(step.sensor_state.rainfall_intensity_mm_hr, 1),
                "Tank (%)": round(step.storage_after_l / node.storage_capacity_l * 100, 1),
                "Drain stress (%)": round(step.sensor_state.drain_stress_percent, 1),
                "Managed now (L)": round(step.decision.allocation.retained_l),
            }
        )
    st.dataframe(pd.DataFrame(table_rows), hide_index=True, width="stretch")

    render_ai_operations(nodes, latest)

    section_heading(
        "BEFORE / AFTER",
        "Immediate downstream runoff comparison",
        "Retained litres are not the same as litres of flooding prevented.",
    )
    before_col, copy_col = st.columns([1.35, 1])
    with before_col:
        before_after_chart(impact)
    with copy_col:
        st.markdown(
            f"""
            <div class="report">
              <h3>Modelled catchment effect</h3>
              <p><b>Without Water Bank</b><br>{impact.stormwater_received_l:,.0f} L immediate downstream runoff</p>
              <p><b>With Water Bank</b><br>{impact.immediate_downstream_l:,.0f} L immediate downstream runoff</p>
              <p><b>Retained locally</b><br>{impact.retained_l:,.0f} L ({impact.retention_percentage:.1f}%)</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if st.session_state.get("storm_complete"):
        section_heading("FINAL REPORT", "WATER BANK STORM REPORT")
        st.markdown(
            f"""
            <div class="report">
              <h3>Simulated Rain Event</h3>
              <p>The distributed Water Bank network retained <b>{impact.retained_l:,.0f} litres</b>
              of modelled runoff during this simulated event. {impact.stored_l:,.0f} L was routed
              to storage and {impact.recharged_l:,.0f} L toward modelled recharge pathways.
              Unsafe water was prevented from entering recharge pathways by the quality safety gate.</p>
              <p><b>Nodes participating:</b> {len(nodes)} &nbsp; · &nbsp;
              <b>Immediate retention:</b> {impact.retention_percentage:.1f}% &nbsp; · &nbsp;
              <b>Residual downstream flow:</b> {impact.immediate_downstream_l:,.0f} L</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    safety_notice()
    st.markdown(
        '<div class="safe-note"><b>Scientific boundary:</b> This simulation-driven digital prototype demonstrates distributed retention logic. It does not claim to stop Chennai flooding or represent measured government data.</div>',
        unsafe_allow_html=True,
    )
