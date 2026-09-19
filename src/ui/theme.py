"""Premium environmental civic-tech visual system for Streamlit."""

from __future__ import annotations

import streamlit as st


CSS = r"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
:root {
  --ink: #e8f7f4;
  --muted: #8ba9a5;
  --panel: rgba(12, 35, 39, .86);
  --panel-2: rgba(16, 48, 51, .78);
  --line: rgba(135, 222, 205, .14);
  --cyan: #5ce1d4;
  --blue: #4aa8ff;
  --green: #69d39c;
  --amber: #f7bd58;
  --red: #ff6b6b;
}
.stApp {
  background:
    radial-gradient(circle at 8% 0%, rgba(24,117,123,.22), transparent 35%),
    radial-gradient(circle at 90% 10%, rgba(33,85,122,.18), transparent 32%),
    linear-gradient(145deg, #061417 0%, #071d21 55%, #071619 100%);
  color: var(--ink);
  font-family: 'DM Sans', sans-serif;
}
[data-testid="stHeader"] { background: transparent; }
[data-testid="stSidebar"] { background: #07171a; border-right: 1px solid var(--line); }
[data-testid="stSidebarNav"] span { color: #cce3df; }
h1, h2, h3, h4 { font-family: 'Manrope', sans-serif !important; letter-spacing: -0.025em; }
h1 { color: #f1fffc !important; }
p, label, li { color: #bdd0cd; line-height: 1.5; }
h2 { font-size: clamp(1.45rem, 2.1vw, 1.8rem) !important; line-height: 1.2 !important; }
h3 { font-size: clamp(1.2rem, 1.65vw, 1.45rem) !important; line-height: 1.25 !important; }
h4 { font-size: 1.08rem !important; line-height: 1.3 !important; }
.block-container { max-width: 1480px; padding-top: 1.4rem; padding-bottom: 4rem; }
.hero {
  position: relative; overflow: hidden; padding: 1.55rem 1.8rem; border: 1px solid var(--line);
  border-radius: 22px; background: linear-gradient(118deg, rgba(12,45,49,.96), rgba(9,29,35,.88));
  box-shadow: 0 28px 80px rgba(0,0,0,.24); margin-bottom: 1.15rem;
}
.hero:after { content:""; position:absolute; width:380px; height:380px; right:-110px; top:-220px;
  border-radius:50%; background:radial-gradient(circle,rgba(92,225,212,.22),transparent 68%); }
.eyebrow { color: var(--cyan); text-transform: uppercase; letter-spacing: .16em; font-size: .72rem; font-weight: 700; }
.hero h1 { font-size: clamp(2rem,3.2vw,3.15rem); line-height: 1.04; margin: .4rem 0 .7rem; }
.hero p { font-size: .98rem; line-height: 1.55; max-width: 780px; margin: 0; color: #a9c6c1; }
.pill { display:inline-block; padding:.28rem .65rem; margin:.85rem .35rem 0 0; border-radius:999px;
  border:1px solid rgba(92,225,212,.25); background:rgba(92,225,212,.08); color:#8de9df; font-size:.72rem; font-weight:700; letter-spacing:.04em; }
.kpi { min-height: 120px; padding: .95rem 1rem; border-radius: 16px; border: 1px solid var(--line);
  background: linear-gradient(150deg, rgba(17,49,51,.9), rgba(10,31,35,.86)); box-shadow:0 10px 30px rgba(0,0,0,.12); }
.kpi-label { color:#91afaa; font-size:.78rem; line-height:1.35; text-transform:uppercase; letter-spacing:.075em; font-weight:700; }
.kpi-value { color:#f2fffd; font-family:'Manrope'; font-weight:750; font-size:clamp(1.35rem,1.8vw,1.8rem); line-height:1.15; margin:.32rem 0 .14rem; overflow-wrap:anywhere; }
.kpi-note { color:#799b96; font-size:.77rem; line-height:1.35; }
.section-label { color: var(--cyan); font-size:.76rem; letter-spacing:.12em; text-transform:uppercase; font-weight:700; margin-top:.5rem; }
.decision { padding: 1.3rem; border-radius:18px; border:1px solid rgba(92,225,212,.25);
 background:linear-gradient(135deg,rgba(23,73,72,.65),rgba(12,36,41,.9)); text-align:center; }
.decision small { color:#8aa9a5; letter-spacing:.12em; text-transform:uppercase; }
.decision strong { display:block; font-family:'Manrope'; font-size:clamp(1.65rem,2.7vw,2.35rem); line-height:1.15; color:#8ef0d8; margin:.25rem 0; }
.notice { padding:.85rem 1rem; border-left:3px solid var(--amber); background:rgba(247,189,88,.07); border-radius:0 10px 10px 0; color:#d9c49c; font-size:.82rem; }
.safe-note { padding:.85rem 1rem; border-left:3px solid var(--cyan); background:rgba(92,225,212,.06); border-radius:0 10px 10px 0; color:#a8d3cd; font-size:.82rem; }
.flow { display:flex; flex-wrap:wrap; gap:.45rem; align-items:center; justify-content:center; padding:1.25rem .5rem; }
.flow-node { border:1px solid var(--line); background:rgba(13,44,47,.75); color:#a9c8c3; border-radius:10px; padding:.62rem .78rem; font-weight:700; font-size:.74rem; }
.flow-node.active { border-color:var(--cyan); color:#e8fffb; box-shadow:0 0 24px rgba(92,225,212,.18); background:rgba(37,110,104,.45); }
.flow-arrow { color:#557974; }
.report { border:1px solid rgba(74,168,255,.2); border-radius:18px; padding:1.25rem 1.4rem;
  background:linear-gradient(140deg,rgba(18,49,61,.88),rgba(9,30,35,.88)); }
.report h3 { margin-top:0; }
.sim-banner { display:flex; gap:.6rem; align-items:center; padding:.55rem .8rem; border-radius:10px;
  background:rgba(74,168,255,.08); border:1px solid rgba(74,168,255,.18); color:#9fcdf6; font-size:.75rem; font-weight:700; }
div[data-testid="stMetric"] { border:1px solid var(--line); background:rgba(12,39,42,.6); padding:.75rem; border-radius:14px; }
[data-testid="stMetricLabel"] p { font-size:.8rem !important; line-height:1.3 !important; }
[data-testid="stMetricValue"] { font-size:clamp(1.18rem,1.7vw,1.55rem) !important; line-height:1.2 !important; overflow-wrap:anywhere; }
[data-testid="stMetricDelta"] { font-size:.78rem !important; }
[data-testid="stCaptionContainer"] p { font-size:.82rem !important; line-height:1.45 !important; }
[data-testid="stExpander"] summary p { font-size:.92rem !important; }
.stButton > button { min-height: 2.8rem; border-radius: 10px; border:1px solid rgba(92,225,212,.24); font-size:.9rem; font-weight:700; }
.stButton > button[kind="primary"] { background:linear-gradient(100deg,#21a59a,#2579a9); color:white; border:0; box-shadow:0 10px 30px rgba(25,142,147,.25); }
[data-testid="stPlotlyChart"] { border:1px solid var(--line); border-radius:16px; overflow:hidden; background:rgba(8,29,33,.55); }
@media (max-width: 700px) {
  .hero { padding:1.25rem; }
  .hero h1 { font-size:clamp(1.8rem,8.5vw,2.45rem); }
  .block-container { padding-left:.8rem; padding-right:.8rem; }
  [data-testid="stMetricValue"] { font-size:1.28rem !important; }
}
</style>
"""


def configure_page(title: str, icon: str = "💧") -> None:
    st.set_page_config(
        page_title=f"{title} · Chennai Water Bank",
        page_icon=icon,
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(CSS, unsafe_allow_html=True)


def render_sidebar_context() -> bool:
    with st.sidebar:
        st.markdown("### CHENNAI WATER BANK")
        st.caption("Bank the Rain. Reduce the Flood. Secure the Future.")
        st.markdown("---")
        presentation_mode = st.toggle("Presentation Mode", value=False)
        st.markdown(
            '<div class="sim-banner">● SIMULATION MODE<br>NO PHYSICAL IOT SENSOR CONNECTED</div>',
            unsafe_allow_html=True,
        )
        st.caption("All rainfall, node, quality and impact values are simulated prototype data.")
        # Poll the cached adapter so an outage during this session remains visible.
        from src.ui.runtime import repository

        @st.fragment(run_every="5s")
        def persistence_status() -> None:
            repo = repository()
            st.caption(f"Persistence: {repo.persistence_status}")
            if repo.degraded_reason:
                st.warning(repo.degraded_reason)

        persistence_status()
    if presentation_mode:
        st.markdown(
            "<style>.block-container{max-width:1600px}.kpi{min-height:135px}.kpi-value{font-size:1.95rem}</style>",
            unsafe_allow_html=True,
        )
    return presentation_mode
