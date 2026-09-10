"""Multi-node rainfall event and network-wide decision diversity."""

import pandas as pd
import plotly.express as px
import streamlit as st

from src.ui.components import hero, latest_steps, node_map, section_heading
from src.ui.runtime import get_active_steps, load_nodes, network_impact, run_full_storm
from src.ui.theme import configure_page, render_sidebar_context


configure_page("Network Simulation")
render_sidebar_context()
hero(
    "NETWORK SIMULATION",
    "A common rainfall profile meets six different local catchments. Each node routes water according to its own capacity, soil and safety constraints.",
    "WHY DISTRIBUTED INTELLIGENCE MATTERS",
)
if st.button("Run full network event", type="primary"):
    run_full_storm()
steps = get_active_steps()
nodes = load_nodes()
latest = latest_steps(steps)
impact = network_impact(steps)

section_heading("RAIN EVENT", "One event, many node responses")
node_map(nodes, steps)

records = []
for step in steps:
    node = next(item for item in nodes if item.node_id == step.node_id)
    records.append(
        {
            "Pulse": step.step_index + 1,
            "Node": node.zone,
            "Action": step.decision.selected_action.value.replace("_", " "),
            "Runoff (L)": step.decision.allocation.incoming_l,
            "Retained (L)": step.decision.allocation.retained_l,
            "Downstream (L)": step.decision.allocation.downstream_l,
        }
    )
frame = pd.DataFrame(records)
chart = px.area(
    frame.groupby("Pulse", as_index=False)[["Retained (L)", "Downstream (L)"]].sum(),
    x="Pulse",
    y=["Retained (L)", "Downstream (L)"],
    color_discrete_sequence=["#5ce1d4", "#f7bd58"],
)
chart.update_layout(
    height=380,
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font_color="#bed1ce",
    yaxis={"gridcolor": "rgba(135,222,205,.1)"},
    legend_title="Modelled routing",
)
st.plotly_chart(chart, width="stretch", config={"displayModeBar": False})

summary = []
for node in nodes:
    step = latest[node.node_id]
    summary.append(
        {
            "Node": node.name,
            "Current action": step.decision.selected_action.value.replace("_", " "),
            "Water quality": step.sensor_state.water_quality_status.value,
            "Tank level (%)": round(step.storage_after_l / node.storage_capacity_l * 100, 1),
            "Soil saturation (%)": round(step.sensor_state.soil_saturation_percent, 1),
            "Retained this pulse (L)": round(step.decision.allocation.retained_l),
        }
    )
st.dataframe(pd.DataFrame(summary), hide_index=True, width="stretch")
st.caption(
    f"PROTOTYPE ESTIMATE · Network received {impact.stormwater_received_l:,.0f} L and retained {impact.retained_l:,.0f} L across the simulated event."
)
