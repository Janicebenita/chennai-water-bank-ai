"""Synchronous-context rainfall and risk advisory agent."""

from __future__ import annotations

from time import perf_counter_ns

from src.config.settings import Settings, get_settings
from src.models.agent_state import AgentFinding, SharedAgentState

from .base import AdvisoryAgent


class RainRiskAgent(AdvisoryAgent):
    name = "rain_risk"

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    async def analyze(self, state: SharedAgentState) -> AgentFinding:
        started = perf_counter_ns()
        facts = state.authoritative_facts
        drain_stress = float(facts["drain_stress_percent"])
        elevated = (
            drain_stress >= self.settings.decision.high_drain_stress_percent
            or bool(facts["contamination_detected"])
            or bool(facts["first_flush_active"])
        )
        level = "ELEVATED" if elevated else "MONITORED"
        summary = (
            f"{level} simulated risk context for {state.zone_id}: rainfall is "
            f"{float(facts['rainfall_intensity_mm_hr']):.1f} mm/hr and drain stress is "
            f"{drain_stress:.1f}%."
        )
        relevant_context = self._relevant_context(state)
        if relevant_context:
            closest = relevant_context[0]
            action = closest.metadata.get("action", "not supplied")
            outcome = closest.metadata.get("outcome", "not supplied")
            summary += (
                f" Moss supplied {len(relevant_context)} bounded related event(s); "
                f"closest evidence {closest.evidence_id} records action {action} and "
                f"outcome {outcome}."
            )
        recommendation = (
            "Prioritize the deterministic safety decision and review affected capacity."
            if elevated
            else "Continue monitoring the current simulated rainfall pulse."
        )
        elapsed = (perf_counter_ns() - started) / 1_000_000
        return AgentFinding(
            self.name,
            "available",
            summary,
            recommendation,
            state.authoritative_fact_refs
            + tuple(item.evidence_id for item in relevant_context),
            ("Risk is derived from simulated prototype inputs, not a Chennai forecast.",),
            elapsed,
        )

    @staticmethod
    def _relevant_context(state: SharedAgentState):
        risk_types = {
            "HIGH_DRAIN_STRESS",
            "CAPACITY_CONSTRAINT",
            "WATER_QUALITY_INTERVENTION",
            "HISTORICAL_INCIDENT",
        }
        return tuple(
            item
            for item in state.moss_context
            if str(item.metadata.get("event_type", "")).upper() in risk_types
            and str(item.metadata.get("zone_id", state.zone_id)) == state.zone_id
        )[:2]
