"""Reusable dashboard visual components."""

from __future__ import annotations

import html
from collections.abc import Iterable

import plotly.graph_objects as go
import streamlit as st

from src.impact.calculator import ImpactSnapshot
from src.models.decision import DecisionAction, DecisionResult
from src.models.node import WaterBankNode
from src.models.scenario import SimulationStep


ACTION_COLORS = {
    DecisionAction.STORE: "#4aa8ff",
    DecisionAction.RECHARGE: "#69d39c",
    DecisionAction.STORE_AND_RECHARGE: "#5ce1d4",
    DecisionAction.DIVERT: "#ff6b6b",
    DecisionAction.CONTROLLED_DISCHARGE: "#f7bd58",
}


def hero(title: str, subtitle: str, eyebrow: str = "DISTRIBUTED URBAN WATER INTELLIGENCE") -> None:
    st.markdown(
        f"""
        <div class="hero">
          <div class="eyebrow">{html.escape(eyebrow)}</div>
          <h1>{html.escape(title)}</h1>
          <p>{html.escape(subtitle)}</p>
          <span class="pill">SIMULATED DATA</span>
          <span class="pill">EXPLAINABLE ENGINE</span>
          <span class="pill">IOT-READY INTERFACE</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def kpi_card(label: str, value: str, note: str = "PROTOTYPE ESTIMATE") -> None:
    st.markdown(
        f"""<div class="kpi"><div class="kpi-label">{html.escape(label)}</div>
        <div class="kpi-value">{html.escape(value)}</div><div class="kpi-note">{html.escape(note)}</div></div>""",
        unsafe_allow_html=True,
    )


def section_heading(label: str, title: str, body: str | None = None) -> None:
    st.markdown(f'<div class="section-label">{html.escape(label)}</div>', unsafe_allow_html=True)
    st.subheader(title)
    if body:
        st.caption(body)


def decision_card(decision: DecisionResult) -> None:
    action = decision.selected_action.value.replace("_", " ")
    st.markdown(
        f"""<div class="decision"><small>Explainable decision</small>
        <strong>{html.escape(action)}</strong><span>Priority {decision.priority * 100:.0f}%</span></div>""",
        unsafe_allow_html=True,
    )
    st.write(decision.human_explanation)


def routing_flow(action: DecisionAction) -> None:
    active = {
        "STORE": action in {DecisionAction.STORE, DecisionAction.STORE_AND_RECHARGE},
        "RECHARGE": action in {DecisionAction.RECHARGE, DecisionAction.STORE_AND_RECHARGE},
        "DIVERT": action == DecisionAction.DIVERT,
        "CONTROLLED": action == DecisionAction.CONTROLLED_DISCHARGE,
    }
    source = ["RAIN", "CATCHMENT", "FIRST FLUSH", "FILTRATION", "QUALITY GATE", "SMART ROUTER"]
    source_html = '<span class="flow-arrow">→</span>'.join(
        f'<span class="flow-node active">{item}</span>' for item in source
    )
    branches = " ".join(
        f'<span class="flow-node {"active" if is_active else ""}">{name}</span>'
        for name, is_active in active.items()
    )
    st.markdown(
        f'<div class="flow">{source_html}<span class="flow-arrow">⇢</span>{branches}</div>',
        unsafe_allow_html=True,
    )


def latest_steps(steps: Iterable[SimulationStep]) -> dict[str, SimulationStep]:
    latest: dict[str, SimulationStep] = {}
    for step in steps:
        latest[step.node_id] = step
    return latest


def node_map(nodes: list[WaterBankNode], steps: list[SimulationStep]) -> None:
    latest = latest_steps(steps)
    colors = []
    labels = []
    sizes = []
    for node in nodes:
        result = latest.get(node.node_id)
        action = result.decision.selected_action if result else DecisionAction.STORE
        colors.append(ACTION_COLORS[action])
        sizes.append(18 + (result.sensor_state.drain_stress_percent / 10 if result else 3))
        labels.append(
            f"<b>{node.name}</b><br>DEMONSTRATION NODE · {node.zone}<br>"
            f"Decision: {action.value.replace('_', ' ')}<br>"
            f"Tank: {(result.storage_after_l / node.storage_capacity_l * 100 if result else node.storage_percent):.0f}%<br>"
            f"Rain: {(result.sensor_state.rainfall_intensity_mm_hr if result else 0):.1f} mm/hr<br>"
            f"Managed: {(result.decision.allocation.retained_l if result else 0):,.0f} L"
        )
    fig = go.Figure(
        go.Scattermapbox(
            lat=[node.latitude for node in nodes],
            lon=[node.longitude for node in nodes],
            mode="markers",
            marker={"size": sizes, "color": colors, "opacity": 0.9},
            text=labels,
            hoverinfo="text",
        )
    )
    fig.update_layout(
        mapbox={"style": "open-street-map", "center": {"lat": 13.02, "lon": 80.20}, "zoom": 9.3},
        margin={"l": 0, "r": 0, "t": 0, "b": 0},
        height=480,
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
    )
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
    st.caption(
        "DEMONSTRATION NODES — blue/green: active retention · amber: capacity pressure · red: safety diversion. No physical installations are implied."
    )


def before_after_chart(impact: ImpactSnapshot) -> None:
    without = impact.stormwater_received_l
    with_bank = impact.immediate_downstream_l
    fig = go.Figure()
    fig.add_bar(
        x=["Without Water Bank", "With Water Bank"],
        y=[without, with_bank],
        marker_color=["#557078", "#4aa8ff"],
        text=[f"{without:,.0f} L", f"{with_bank:,.0f} L"],
        textposition="outside",
    )
    fig.update_layout(
        height=360,
        yaxis_title="Immediate downstream runoff (litres)",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font_color="#b9cecb",
        margin={"l": 20, "r": 20, "t": 25, "b": 20},
        yaxis={"gridcolor": "rgba(135,222,205,.10)"},
    )
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


def safety_notice() -> None:
    st.markdown(
        '<div class="notice"><b>Water-quality safeguard:</b> Prototype logic is illustrative and requires certified, site-specific testing before any real-world groundwater recharge.</div>',
        unsafe_allow_html=True,
    )
