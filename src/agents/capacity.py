"""Deterministic capacity advisory agent using authoritative numeric facts."""

from __future__ import annotations

from time import perf_counter_ns

from src.models.agent_state import AgentFinding, SharedAgentState

from .base import AdvisoryAgent


class CapacityAgent(AdvisoryAgent):
    name = "capacity"

    async def analyze(self, state: SharedAgentState) -> AgentFinding:
        started = perf_counter_ns()
        facts = state.authoritative_facts
        storage = max(0.0, float(facts["available_storage_l"]))
        recharge_rate = max(0.0, float(facts["recharge_capacity_l_per_hour"]))
        recharge_enabled = bool(facts["recharge_available"])
        summary = (
            f"Authoritative model state reports {storage:,.0f} L tank headroom and "
            f"{recharge_rate:,.0f} L/hr configured recharge capacity "
            f"({'available' if recharge_enabled else 'disabled'})."
        )
        recommendation = (
            f"Retain the existing {facts['decision']} routing decision; it remains bounded "
            "by incoming runoff and configured capacity."
        )
        elapsed = (perf_counter_ns() - started) / 1_000_000
        return AgentFinding(
            self.name,
            "available",
            summary,
            recommendation,
            state.authoritative_fact_refs,
            ("Recharge capacity is a prototype estimate requiring site validation.",),
            elapsed,
        )
