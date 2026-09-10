"""Auditable methodology, equations, scores and safety hierarchy."""

import pandas as pd
import streamlit as st

from src.decision.explainer import METHODOLOGY, SCORE_FORMULAS
from src.ui.components import hero, safety_notice, section_heading
from src.ui.theme import configure_page, render_sidebar_context


configure_page("Decision Explainer")
render_sidebar_context()
hero(
    "DECISION EXPLAINER",
    "No black box. Safety gates, engineering equations, normalized scores and physical allocations remain visible and testable.",
    "ENGINEERING TRANSPARENCY",
)

section_heading("DECISION ORDER", "Safety before optimization")
st.markdown(
    """
1. **Safety gate** — contamination, out-of-range pH and excessive turbidity can force diversion.
2. **First-flush gate** — direct recharge is blocked during first flush.
3. **Physical capacity** — tank headroom and interval recharge capacity cap allocations.
4. **Beneficial retention** — safe storage and eligible recharge are used before discharge.
5. **Controlled discharge** — residual flow is explicitly reported when local capacity is finite.
"""
)

section_heading("HYDROLOGY", "Show the mathematics")
formula_rows = [{"Model": name.title(), "Formula": formula} for name, formula in METHODOLOGY.items()]
st.dataframe(pd.DataFrame(formula_rows), hide_index=True, width="stretch")
st.markdown(
    """
**Unit identity:** 1 mm of rainfall over 1 m² equals 1 litre.

**Runoff assumption:** a dimensionless runoff coefficient represents the share of rainfall becoming direct runoff at the modelled catchment. This simplified volume model does not calculate pipe hydraulics, flood depth, travel time, tidal effects, or catchment interactions.
"""
)

section_heading("PRIORITY SCORES", "Exact transparent formulas")
score_rows = [{"Priority": name.title(), "Normalized formula": formula} for name, formula in SCORE_FORMULAS.items()]
st.dataframe(pd.DataFrame(score_rows), hide_index=True, width="stretch")
st.caption(
    "Inputs are normalized to 0–1. Scores communicate routing priority; actual litres are always limited by incoming runoff and configured capacity. Safety gates override all scores."
)

left, right = st.columns(2)
with left:
    st.markdown("#### Prototype quality thresholds")
    st.code(
        """Recharge-screen turbidity  ≤ 5 NTU
Storage-screen turbidity   ≤ 25 NTU
Illustrative pH range       6.5–8.5
Soil saturation block      ≥ 85%
First flush                 recharge blocked
Contamination detected     divert""",
        language="text",
    )
with right:
    st.markdown("#### Mass balance")
    st.code(
        """incoming runoff
= stored
+ recharged
+ diverted
+ controlled discharge

retained = stored + recharged""",
        language="text",
    )

with st.expander("Important assumptions and limitations", expanded=True):
    st.markdown(
        """
- All displayed node and environmental values are simulated.
- Recharge capacity is an illustrative interval estimate, not proof of aquifer suitability.
- Certified sampling, treatment design, geotechnical review and regulatory approval are required for real deployment.
- Retention volume is not the same as flood damage avoided.
- Distributed nodes complement—but do not replace—drainage, wetlands, reservoirs, watershed management or major flood-control infrastructure.
"""
    )
safety_notice()
