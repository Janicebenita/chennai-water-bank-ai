"""Asset readiness advisory agent."""

from __future__ import annotations

from time import perf_counter_ns

from src.models.agent_state import AgentFinding, SharedAgentState

from .base import AdvisoryAgent


class AssetMaintenanceAgent(AdvisoryAgent):
    name = "asset_maintenance"

    async def analyze(self, state: SharedAgentState) -> AgentFinding:
        started = perf_counter_ns()
        facts = state.authoritative_facts
        recharge_enabled = bool(facts["recharge_available"])
        history_available = state.semantic_context_status == "available" and bool(
            state.moss_context
        )
        summary = (
            f"Asset {facts['node_id']} is a fictional demonstration node; its configured "
            f"recharge pathway is {'available' if recharge_enabled else 'unavailable'}."
        )
        limitations = [
            "No physical inspection or verified Chennai asset telemetry is connected."
        ]
        if not history_available:
            limitations.append("No retrieved maintenance history is available.")
        elapsed = (perf_counter_ns() - started) / 1_000_000
        return AgentFinding(
            self.name,
            "available" if history_available else "limited",
            summary,
            "Require a certified inspection before any real recharge operation.",
            state.authoritative_fact_refs + state.moss_context_refs[:2],
            tuple(limitations),
            elapsed,
        )
