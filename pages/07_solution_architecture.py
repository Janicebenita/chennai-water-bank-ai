"""Current and future IoT-ready system architecture."""

import streamlit as st

from src.ui.components import hero, section_heading
from src.ui.theme import configure_page, render_sidebar_context


configure_page("Solution Architecture")
render_sidebar_context()
hero(
    "SOLUTION ARCHITECTURE",
    "The simulator and future physical sensors meet the platform through the same normalized data contract, preserving the decision core.",
    "MODULAR BY DESIGN",
)

section_heading("CURRENT PROTOTYPE", "Actual software flow")
st.code(
    """DIGITAL SENSOR SIMULATOR
          │
          ▼
NORMALIZED SENSOR DATA INTERFACE ───► SIMULATION CLOCK
          │
          ▼
WATER-QUALITY + FIRST-FLUSH SAFETY GATE
          │
          ▼
EXPLAINABLE DECISION ENGINE
          │
    ┌─────┼──────────┬──────────────┐
    ▼     ▼          ▼              ▼
  STORE  RECHARGE   DIVERT   CONTROLLED DISCHARGE
    └─────┴──────────┴──────────────┘
          │
          ▼
HYDROLOGY / STORAGE MODEL ───► IMPACT ENGINE
          │
          ├──► MEMORY BACKEND (default + resilient fallback)
          └──► FIRESTORE (optional)
          │
          ▼
STREAMLIT DASHBOARD""",
    language="text",
)
st.caption(
    "Safety classification occurs before beneficial routing. Hydrology calculates incoming volume; the engine then applies safety and capacity constraints to preserve mass balance."
)

section_heading("FUTURE DEPLOYMENT", "IoT-ready ingestion boundary")
st.code(
    """Rain gauge · level sensor · flow meter · soil moisture · quality sensors
                                │
                                ▼
                       ESP32 / edge gateway
                                │
                         MQTT / HTTPS
                                │
                                ▼
                       Ingestion adapter
                                │
                                ▼
                  Normalized SensorData interface
                                │
                                ▼
               EXISTING WATER BANK DECISION PLATFORM""",
    language="text",
)

left, right = st.columns(2)
with left:
    st.markdown("#### Current intelligence")
    st.markdown(
        """
- Explainable rules
- Transparent engineering calculations
- Deterministic safety gates
- Capacity-constrained allocation
- Repeatable digital sensor simulation
"""
    )
with right:
    st.markdown("#### Optional AI operations layer")
    st.markdown(
        """
- Structured WaterEvents derived from existing decisions
- Moss semantic retrieval of relevant prior events
- Four isolated advisory agents
- Human approval before any operational response
- Deterministic Water Bank decisions remain authoritative
"""
    )
st.info(
    "The collaborative layer is advisory and disabled safely when Moss is not configured. "
    "It does not command infrastructure or replace the deterministic decision engine."
)

section_heading("PERSISTENCE", "Graceful cloud fallback")
st.markdown(
    """
Firestore mode uses `nodes`, `simulation_runs`, `node_events`, `decisions`, and `impact_snapshots`. If credentials or the service are unavailable, the repository factory falls back to seeded in-memory demo data so the presentation never opens to a blank screen.
"""
)
