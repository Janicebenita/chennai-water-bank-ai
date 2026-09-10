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
            state.authoritative_fact_refs + state.moss_context_refs[:2],
            ("Risk is derived from simulated prototype inputs, not a Chennai forecast.",),
            elapsed,
        )
