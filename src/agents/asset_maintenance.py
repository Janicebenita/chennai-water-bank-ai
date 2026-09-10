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
        relevant_evidence = self._relevant_evidence(state, str(facts["node_id"]))
        history_available = bool(relevant_evidence)
        summary = (
            f"Asset {facts['node_id']} is a fictional demonstration node; its configured "
            f"recharge pathway is {'available' if recharge_enabled else 'unavailable'}."
        )
        if history_available:
            summary += (
                f" Moss returned {len(relevant_evidence)} relevant asset or maintenance "
                "record(s)."
            )
        else:
            summary += " No relevant maintenance evidence retrieved."
        limitations = [
            "No physical inspection or verified Chennai asset telemetry is connected."
        ]
        if not history_available:
            limitations.append("No relevant maintenance evidence retrieved.")
        elapsed = (perf_counter_ns() - started) / 1_000_000
        return AgentFinding(
            self.name,
            "available" if history_available else "limited",
            summary,
            "Require a certified inspection before any real recharge operation.",
            state.authoritative_fact_refs
            + tuple(item.evidence_id for item in relevant_evidence),
            tuple(limitations),
            elapsed,
        )

    @staticmethod
    def _relevant_evidence(state: SharedAgentState, asset_id: str):
        maintenance_types = {
            "ASSET_UNAVAILABLE",
            "ASSET_FAILURE",
            "MAINTENANCE_EVENT",
            "MAINTENANCE_FAILURE",
        }
        return tuple(
            item
            for item in state.moss_context
            if str(item.metadata.get("asset_id", "")) == asset_id
            and str(item.metadata.get("event_type", "")).upper()
            in maintenance_types
        )[:2]
