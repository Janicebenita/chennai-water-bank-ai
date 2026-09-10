"""Problem, solution, boundaries and hackathon positioning."""

import streamlit as st

from src.ui.components import hero, safety_notice, section_heading
from src.ui.theme import configure_page, render_sidebar_context


configure_page("About the Solution")
render_sidebar_context()
hero(
    "BANK THE RAIN.",
    "Reduce the Flood. Secure the Future. A simulation-driven digital prototype for distributed urban rainwater management.",
    "CHENNAI WATER BANK",
)

problem, principle, solution = st.columns(3)
with problem:
    st.markdown("### The problem")
    st.write(
        "Chennai can experience intense storm runoff and local drainage stress while also facing dry-period water-security and groundwater pressure."
    )
with principle:
    st.markdown("### The principle")
    st.write(
        "Suitable rainwater need not be treated only as water to dispose of. A measurable portion can be safely retained closer to where it falls."
    )
with solution:
    st.markdown("### The solution")
    st.write(
        "Distributed nodes capture, assess and route water to storage, modelled recharge, diversion or controlled discharge—then quantify the result."
    )

section_heading("THE OPERATING IDEA", "Predict · Capture · Assess · Decide · Route · Measure")
st.markdown(
    """
Each Water Bank node represents a local urban catchment such as a campus, apartment complex, school, park or commercial property. The current prototype uses synthetic digital sensors. Those inputs pass through a normalized interface so a future MQTT or HTTPS ingestion adapter can replace the simulator without rewriting the business logic.
"""
)

st.markdown("### What this prototype can demonstrate")
st.markdown(
    """
- A configured node can retain a calculable portion of modelled runoff.
- Local tanks and eligible recharge pathways can reduce immediate downstream volume.
- Unsafe and first-flush water is blocked from direct recharge.
- Different local constraints justify different routing decisions during one storm.
- Every allocation exposes its formula, assumptions and mass balance.
"""
)

st.markdown("### What this prototype does not claim")
st.markdown(
    """
It is not a validated digital twin of Chennai and does not claim to stop flooding. It does not replace municipal drainage, large flood-control infrastructure, watershed management, reservoirs, wetland protection, certified treatment design or professional hydrogeological assessment. It is a potential complementary distributed intervention.
"""
)

section_heading("60-SECOND DEMO", "A judge-ready story")
st.markdown(
    """
1. Open **Command Center** and identify six simulated demonstration nodes.
2. Click **Simulate Chennai Storm** and watch independent routing decisions appear.
3. Open **Node Intelligence** to inspect one decision and its active water path.
4. Open **Physical Process** to show rain moving through first flush, filtration, the quality gate, and the active destination.
5. In **Scenario Lab**, choose contaminated first flush and verify recharge is blocked.
6. Choose full storage + saturated soil and verify controlled discharge.
7. Open **Impact Analytics** to compare immediate downstream runoff with and without the modelled Water Bank network.
8. Use **Try Breaking the System** to manipulate the constraints live.
"""
)
safety_notice()
