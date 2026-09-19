"""Compact Moss-enhanced advisory panel for the existing Command Center."""

from __future__ import annotations

import asyncio

import pandas as pd
import streamlit as st

from src.config.settings import get_settings
from src.memory import get_semantic_memory
from src.models.agent_state import OrchestratorResult
from src.models.node import WaterBankNode
from src.models.scenario import SimulationStep
from src.orchestration import WaterBankOrchestrator
from src.ui.runtime import repository


@st.cache_resource
def _semantic_memory():
    return get_semantic_memory()


def _run_analysis(node: WaterBankNode, step: SimulationStep, intent: str) -> OrchestratorResult:
    settings = get_settings()
    orchestrator = WaterBankOrchestrator(
        _semantic_memory(),
        repository=repository(),
        retrieval_limit=settings.moss_top_k,
    )
    return asyncio.run(orchestrator.analyze(node, step, intent))


def render_ai_operations(
    nodes: list[WaterBankNode], latest: dict[str, SimulationStep]
) -> None:
    """Render an additive advisory workflow without issuing control commands."""
    st.markdown('<div class="section-label">COLLABORATIVE AI</div>', unsafe_allow_html=True)
    with st.expander("AI Operations Guidance · Moss evidence + four advisory agents"):
        st.caption(
            "Authoritative values stay in the Water Bank core. Moss contributes only "
            "retrieved WaterEvent context. All recommendations require human review."
        )
        eligible = [node for node in nodes if node.node_id in latest]
        if not eligible:
            st.info("No simulated node snapshot is available for analysis.")
            return
        left, right = st.columns([1, 1.5])
        selected_id = left.selectbox(
            "Demonstration node",
            [node.node_id for node in eligible],
            format_func=lambda node_id: next(
                node.name for node in eligible if node.node_id == node_id
            ),
            key="ai_node_id",
        )
        intent = right.text_input(
            "Operations question",
            "Assess current risk, capacity, incident context and asset readiness",
            key="ai_user_intent",
        )
        if st.button("RUN COLLABORATIVE ANALYSIS", key="run_ai_analysis"):
            node = next(item for item in eligible if item.node_id == selected_id)
            with st.spinner("Combining structured facts, Moss context and agent findings…"):
                st.session_state["ai_orchestration_result"] = _run_analysis(
                    node, latest[node.node_id], intent
                )
                st.session_state["ai_human_review"] = "pending"

        result: OrchestratorResult | None = st.session_state.get(
            "ai_orchestration_result"
        )
        if result is None:
            settings = get_settings()
            status = "enabled" if settings.moss_enabled else "disabled"
            st.info(f"Moss is currently {status}. Run analysis to produce measured results.")
            return
        _render_result(result)


def _render_result(result: OrchestratorResult) -> None:
    metrics = st.columns(4)
    metrics[0].metric("Moss status", result.moss_status.upper())
    metrics[1].metric("Evidence", str(result.moss_results_count))
    metrics[2].metric(
        "Moss retrieval",
        _milliseconds(result.latency.moss_retrieval_ms),
    )
    metrics[3].metric("Total analysis", _milliseconds(result.latency.total_request_ms))

    st.markdown("#### AI recommendation")
    st.write(result.recommendation)
    st.warning("HUMAN REVIEW REQUIRED · No valve, pump, gate or recharge equipment is commanded.")

    if result.warnings:
        for warning in result.warnings:
            st.info(warning)

    facts_tab, context_tab, evidence_tab, agents_tab, latency_tab = st.tabs(
        ["Live facts", "Moss context", "Evidence", "Agent findings", "Latency"]
    )
    with facts_tab:
        st.caption("AUTHORITATIVE · SIMULATED DATA")
        fact_rows = [
            {"Fact": key.replace("_", " ").title(), "Value": _display_value(value)}
            for key, value in result.live_facts.items()
            if key not in {"reason_codes"}
        ]
        st.dataframe(pd.DataFrame(fact_rows), hide_index=True, width="stretch")
    with context_tab:
        if not result.semantic_context:
            st.write("Historical semantic context temporarily unavailable.")
        for item in result.semantic_context:
            is_simulated = str(item.metadata.get("simulated", "")).lower() == "true"
            label = "SIMULATED DATA" if is_simulated else "SOURCE DATA"
            st.markdown(f"**{label} · Evidence `{item.evidence_id}`**")
            st.write(item.text)
            st.caption(
                f"Timestamp: {item.metadata.get('timestamp', '—')} · "
                f"Event: {item.metadata.get('event_type', '—')} · "
                f"Zone: {item.metadata.get('zone_id', '—')} · "
                f"Asset: {item.metadata.get('asset_id', '—')} · "
                f"Relevance: {_score(item.relevance)}"
            )
    with evidence_tab:
        evidence_rows = _evidence_rows(result.evidence)
        if evidence_rows:
            st.dataframe(pd.DataFrame(evidence_rows), hide_index=True, width="stretch")
        else:
            st.write("No semantic evidence was retrieved for this analysis.")
    with agents_tab:
        for finding in result.agent_findings.values():
            st.markdown(
                f"**{finding.agent.replace('_', ' ').title()} · {finding.status.upper()}**"
            )
            st.write(finding.summary)
            st.caption(f"Recommendation: {finding.recommendation}")
            for limitation in finding.limitations:
                st.caption(f"Limitation: {limitation}")
    with latency_tab:
        rows = [
            ("Moss retrieval", result.latency.moss_retrieval_ms),
            ("Rain & Risk Agent", result.latency.agent_rain_risk_ms),
            ("Incident Memory Agent", result.latency.agent_incident_memory_ms),
            ("Capacity Agent", result.latency.agent_capacity_ms),
            ("Asset & Maintenance Agent", result.latency.agent_asset_maintenance_ms),
            ("Orchestrator", result.latency.orchestrator_ms),
            ("Total request", result.latency.total_request_ms),
        ]
        st.dataframe(
            pd.DataFrame(
                [{"Stage": name, "Measured milliseconds": value} for name, value in rows]
            ),
            hide_index=True,
            width="stretch",
        )
        st.caption(
            "Moss retrieval uses the SDK-reported query time when available, with a "
            "measured monotonic compatibility fallback. No demo values are hard-coded."
        )
        st.caption(
            "Orchestrator time includes the concurrent agent stage and recommendation assembly. "
            "Total request measures advisory analysis, including event persistence, indexing and "
            "retrieval; it excludes earlier simulation, page rendering and human review. "
            "Agent durations overlap and should not be added to orchestration time."
        )

    st.markdown("#### Human operations review")
    accept, reject, evidence = st.columns(3)
    if accept.button("Accept advisory", width="stretch"):
        st.session_state["ai_human_review"] = "accepted"
    if reject.button("Reject advisory", width="stretch"):
        st.session_state["ai_human_review"] = "rejected"
    if evidence.button("Request more evidence", width="stretch"):
        st.session_state["ai_human_review"] = "more_evidence_requested"
    st.write(f"Review state: **{st.session_state.get('ai_human_review', 'pending').upper()}**")


def _milliseconds(value: float | None) -> str:
    return "—" if value is None else f"{value:.3f} ms"


def _score(value: float | None) -> str:
    return "not reported" if value is None else f"{value:.3f}"


def _display_value(value: object) -> str:
    if isinstance(value, bool):
        return "YES" if value else "NO"
    if value is None:
        return "—"
    return str(value)


def _evidence_rows(evidence) -> list[dict[str, str]]:
    return [
        {
            "WaterEvent ID": item.evidence_id,
            "Timestamp": str(item.metadata.get("timestamp", "—")),
            "Event type": str(item.metadata.get("event_type", "—")),
            "Zone": str(item.metadata.get("zone_id", "—")),
            "Asset": str(item.metadata.get("asset_id", "—")),
            "Relevance": _score(item.relevance),
            "Action": str(item.metadata.get("action", "—")),
            "Outcome": str(item.metadata.get("outcome", "—")),
        }
        for item in evidence
    ]
