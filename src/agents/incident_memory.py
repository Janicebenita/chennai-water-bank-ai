"""Asynchronous-context incident memory advisory agent."""

from __future__ import annotations

from time import perf_counter_ns

from src.models.agent_state import AgentFinding, SharedAgentState

from .base import AdvisoryAgent


class IncidentMemoryAgent(AdvisoryAgent):
    name = "incident_memory"

    async def analyze(self, state: SharedAgentState) -> AgentFinding:
        started = perf_counter_ns()
        if state.semantic_context_status != "available":
            elapsed = (perf_counter_ns() - started) / 1_000_000
            return AgentFinding(
                self.name,
                "unavailable",
                "Historical semantic context temporarily unavailable.",
                "Use authoritative facts and deterministic Water Bank logic only.",
                (),
                ("No historical analogue is claimed without retrieved evidence.",),
                elapsed,
            )
        if not state.moss_context:
            elapsed = (perf_counter_ns() - started) / 1_000_000
            return AgentFinding(
                self.name,
                "available",
                "Moss returned no matching WaterEvents.",
                "Do not infer a historical pattern; continue with live structured facts.",
                (),
                ("No matching evidence was retrieved.",),
                elapsed,
            )
        simulated_count = sum(
            1
            for item in state.moss_context
            if str(item.metadata.get("simulated", "")).lower() == "true"
        )
        summary = (
            f"Moss retrieved {len(state.moss_context)} relevant WaterEvent(s); "
            f"{simulated_count} are explicitly labelled simulated."
        )
        elapsed = (perf_counter_ns() - started) / 1_000_000
        return AgentFinding(
            self.name,
            "available",
            summary,
            "Review the retrieved event evidence before using it as operational context.",
            state.moss_context_refs,
            ("Similarity is contextual evidence, not proof of the same outcome.",),
            elapsed,
        )
