"""Modelled impact analytics and without-vs-with comparison."""

import pandas as pd
import plotly.express as px
import streamlit as st

from src.ui.components import before_after_chart, hero, kpi_card, section_heading
from src.ui.runtime import get_active_steps, load_nodes, network_impact
from src.ui.theme import configure_page, render_sidebar_context


configure_page("Impact Analytics")
render_sidebar_context()
hero(
    "IMPACT ANALYTICS",
    "Quantify where calculated runoff went—without equating retained litres with flooding prevented.",
    "PROTOTYPE ESTIMATES",
)
steps = get_active_steps()
nodes = load_nodes()
impact = network_impact(steps)

cards = st.columns(4)
with cards[0]:
    kpi_card("Stormwater received", f"{impact.stormwater_received_l:,.0f} L")
with cards[1]:
    kpi_card("Stored", f"{impact.stored_l:,.0f} L")
with cards[2]:
    kpi_card("Modelled recharge", f"{impact.recharged_l:,.0f} L")
with cards[3]:
    kpi_card("Immediate retention", f"{impact.retention_percentage:.1f}%")

section_heading("COMPARISON", "Without Water Bank vs with Water Bank")
left, right = st.columns([1.3, 1])
with left:
    before_after_chart(impact)
with right:
    st.markdown(
        f"""
        ### Engineering interpretation

        - Calculated runoff: **{impact.stormwater_received_l:,.0f} L**
        - Stored locally: **{impact.stored_l:,.0f} L**
        - Routed toward modelled recharge: **{impact.recharged_l:,.0f} L**
        - Immediate downstream runoff: **{impact.immediate_downstream_l:,.0f} L**
        - Estimated immediate runoff retained at the modelled catchments: **{impact.retained_l:,.0f} L**

        This is a volume-allocation estimate, not a hydraulic flood-depth or damage model.
        """
    )

records = []
for step in steps:
    node = next(item for item in nodes if item.node_id == step.node_id)
    records.append(
        {
            "Node": node.zone,
            "Stored": step.decision.allocation.stored_l,
            "Recharged": step.decision.allocation.recharged_l,
            "Downstream": step.decision.allocation.downstream_l,
        }
    )
frame = pd.DataFrame(records).groupby("Node", as_index=False).sum()
fig = px.bar(
    frame,
    x="Node",
    y=["Stored", "Recharged", "Downstream"],
    barmode="stack",
    color_discrete_sequence=["#4aa8ff", "#69d39c", "#f7bd58"],
)
fig.update_layout(
    height=410,
    yaxis_title="Litres across event",
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font_color="#bed1ce",
    yaxis={"gridcolor": "rgba(135,222,205,.1)"},
)
st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
