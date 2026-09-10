"""Advisory orchestration without changing deterministic Water Bank control."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from time import perf_counter_ns
from types import MappingProxyType
from uuid import uuid4

from src.agents import (
    AdvisoryAgent,
    AssetMaintenanceAgent,
    CapacityAgent,
    IncidentMemoryAgent,
    RainRiskAgent,
)
from src.evaluation import log_orchestration_metrics
from src.events import EventContextBuilder
from src.memory.semantic_memory import SemanticMemory
from src.models.agent_state import (
    AgentFinding,
    LatencyMetrics,
    OrchestratorResult,
    SharedAgentState,
)
from src.models.node import WaterBankNode
from src.models.scenario import SimulationStep
from src.persistence.repository import Repository


class WaterBankOrchestrator:
    """Combine live facts, Moss context and isolated agent findings.

    The output is advisory. Existing decision results are copied into immutable
    authoritative facts and are never recomputed or overwritten here.
    """

    def __init__(
        self,
        semantic_memory: SemanticMemory,
        *,
        repository: Repository | None = None,
        event_builder: EventContextBuilder | None = None,
        agents: tuple[AdvisoryAgent, ...] | None = None,
        retrieval_limit: int = 4,
    ) -> None:
        self.semantic_memory = semantic_memory
        self.repository = repository
        self.event_builder = event_builder or EventContextBuilder()
        self.agents = agents or (
            RainRiskAgent(),
            IncidentMemoryAgent(),
            CapacityAgent(),
            AssetMaintenanceAgent(),
        )
        self.retrieval_limit = max(1, min(10, retrieval_limit))

    async def analyze(
        self,
        node: WaterBankNode,
        step: SimulationStep,
        user_intent: str = "Assess current Water Bank conditions",
    ) -> OrchestratorResult:
        total_started = perf_counter_ns()
        request_id = str(uuid4())
        now = datetime.now(timezone.utc)
        facts = self._authoritative_facts(node, step)
        fact_refs = (
            f"sensor:{node.node_id}:{step.sensor_state.timestamp.isoformat()}",
            f"decision:{node.node_id}:{step.step_index}",
        )
        event = self.event_builder.build(node, step)
        warnings: list[str] = []
        if event is not None:
            if self.repository is not None:
                try:
                    self.repository.save_event("node_events", event.to_dict())
                except Exception:
                    warnings.append("Structured WaterEvent persistence was unavailable.")
            index_result = await self.semantic_memory.index_event(event)
            if index_result.status == "unavailable":
                warnings.append("WaterEvent could not be indexed in Moss.")

        query = self._semantic_query(
            node,
            step,
            user_intent,
            event.event_type if event is not None else "NO_MEANINGFUL_EVENT",
        )
        retrieval = await self.semantic_memory.retrieve_context(
            query,
            filters={"zone_id": node.zone},
            limit=self.retrieval_limit,
        )
        if retrieval.status == "unavailable":
            warnings.append("Historical semantic context temporarily unavailable.")
        elif retrieval.status == "disabled":
            warnings.append("Moss semantic context is disabled; baseline behavior is active.")

        shared = SharedAgentState(
            request_id=request_id,
            timestamp=now,
            zone_id=node.zone,
            asset_ids=(node.node_id,),
            user_intent=user_intent,
            authoritative_facts=MappingProxyType(facts),
            authoritative_fact_refs=fact_refs,
            moss_query=query,
            moss_context=retrieval.contexts,
            moss_context_refs=tuple(item.evidence_id for item in retrieval.contexts),
            moss_retrieval_ms=retrieval.retrieval_ms,
            evidence=retrieval.contexts,
            semantic_context_status=retrieval.status,
        )

        orchestration_started = perf_counter_ns()
        findings = await self._run_agents(shared)
        shared.findings = findings
        failures = sum(1 for item in findings.values() if item.status == "failed")
        if failures:
            warnings.append(f"{failures} advisory agent(s) failed; available findings were preserved.")
        recommendation = self._recommendation(step, findings)
        orchestrator_ms = (perf_counter_ns() - orchestration_started) / 1_000_000
        total_ms = (perf_counter_ns() - total_started) / 1_000_000
        latency = LatencyMetrics(
            moss_retrieval_ms=retrieval.retrieval_ms,
            agent_rain_risk_ms=self._latency(findings, "rain_risk"),
            agent_incident_memory_ms=self._latency(findings, "incident_memory"),
            agent_capacity_ms=self._latency(findings, "capacity"),
            agent_asset_maintenance_ms=self._latency(findings, "asset_maintenance"),
            orchestrator_ms=orchestrator_ms,
            total_request_ms=total_ms,
        )
        freshness = self._freshness(step, now)
        limitations = (
            "All current node and environmental values are simulated prototype data.",
            "Semantic similarity is supporting evidence, not authoritative live state.",
            "Certified site testing and human review are required before real recharge.",
        )
        result = OrchestratorResult(
            recommendation=recommendation,
            live_facts=dict(facts),
            semantic_context=retrieval.contexts,
            agent_findings=findings,
            evidence=retrieval.contexts,
            uncertainty=("No physical Chennai sensor or verified incident feed is connected.",),
            limitations=limitations,
            warnings=tuple(warnings),
            data_freshness=freshness,
            latency=latency,
            moss_status=retrieval.status,
            moss_results_count=len(retrieval.contexts),
        )
        log_orchestration_metrics(
            {
                "request_id": request_id,
                "moss_retrieval_ms": retrieval.retrieval_ms,
                "moss_results_count": len(retrieval.contexts),
                "moss_status": retrieval.status,
                "agent_rain_risk_ms": latency.agent_rain_risk_ms,
                "agent_incident_memory_ms": latency.agent_incident_memory_ms,
                "agent_capacity_ms": latency.agent_capacity_ms,
                "agent_asset_maintenance_ms": latency.agent_asset_maintenance_ms,
                "agent_failures": failures,
                "orchestrator_ms": orchestrator_ms,
                "total_request_ms": total_ms,
                "evidence_count": len(retrieval.contexts),
                "data_freshness": freshness["status"],
            }
        )
        return result

    async def _run_agents(self, state: SharedAgentState) -> dict[str, AgentFinding]:
        async def run(agent: AdvisoryAgent) -> AgentFinding:
            started = perf_counter_ns()
            try:
                return await agent.analyze(state)
            except Exception:
                elapsed = (perf_counter_ns() - started) / 1_000_000
                return AgentFinding(
                    agent.name,
                    "failed",
                    "Agent finding unavailable.",
                    "Continue only with authoritative facts and available findings.",
                    (),
                    ("This agent failed during the current request.",),
                    elapsed,
                )

        results = await asyncio.gather(*(run(agent) for agent in self.agents))
        return {item.agent: item for item in results}

    @staticmethod
    def _authoritative_facts(
        node: WaterBankNode, step: SimulationStep
    ) -> dict[str, object]:
        allocation = step.decision.allocation
        storage_percent = (
            100.0
            if node.storage_capacity_l <= 0
            else 100.0 * step.storage_after_l / node.storage_capacity_l
        )
        return {
            "node_id": node.node_id,
            "node_name": node.name,
            "zone": node.zone,
            "timestamp": step.sensor_state.timestamp.isoformat(),
            "rainfall_intensity_mm_hr": step.sensor_state.rainfall_intensity_mm_hr,
            "rainfall_forecast_mm": step.sensor_state.rainfall_forecast_mm,
            "soil_saturation_percent": step.sensor_state.soil_saturation_percent,
            "drain_stress_percent": step.sensor_state.drain_stress_percent,
            "water_quality_status": step.sensor_state.water_quality_status.value,
            "contamination_detected": step.sensor_state.contamination_detected,
            "first_flush_active": step.sensor_state.first_flush_active,
            "storage_capacity_l": node.storage_capacity_l,
            "storage_after_l": step.storage_after_l,
            "available_storage_l": max(0.0, node.storage_capacity_l - step.storage_after_l),
            "storage_percent": storage_percent,
            "recharge_capacity_l_per_hour": node.recharge_capacity_l_per_hour,
            "recharge_available": node.recharge_available,
            "incoming_l": allocation.incoming_l,
            "stored_l": allocation.stored_l,
            "recharged_l": allocation.recharged_l,
            "downstream_l": allocation.downstream_l,
            "decision": step.decision.selected_action.value,
            "reason_codes": step.decision.reason_codes,
        }

    @staticmethod
    def _semantic_query(
        node: WaterBankNode,
        step: SimulationStep,
        user_intent: str,
        event_type: str,
    ) -> str:
        state = step.sensor_state
        storage_percent = (
            100.0
            if node.storage_capacity_l <= 0
            else 100.0 * step.storage_after_l / node.storage_capacity_l
        )
        return (
            f"{user_intent}. Find WaterEvents relevant to zone {node.zone}, asset "
            f"{node.node_id}, rainfall {state.rainfall_intensity_mm_hr:.1f} mm/hr, "
            f"storage {storage_percent:.1f}% full with "
            f"{max(0.0, node.storage_capacity_l - step.storage_after_l):.1f} L available, "
            f"recharge capacity {node.recharge_capacity_l_per_hour:.1f} L/hr, "
            f"asset availability {'available' if node.recharge_available else 'unavailable'}, "
            f"water quality {state.water_quality_status.value}, event type {event_type}, "
            f"and current decision {step.decision.selected_action.value}."
        )

    @staticmethod
    def _recommendation(
        step: SimulationStep, findings: dict[str, AgentFinding]
    ) -> str:
        available = sum(1 for item in findings.values() if item.status != "failed")
        return (
            f"Maintain the existing deterministic {step.decision.selected_action.value.replace('_', ' ')} "
            f"decision for this simulated pulse. {available} of {len(findings)} advisory "
            "findings are available. Review evidence and limitations before any action."
        )

    @staticmethod
    def _latency(findings: dict[str, AgentFinding], name: str) -> float | None:
        finding = findings.get(name)
        return finding.latency_ms if finding else None

    @staticmethod
    def _freshness(step: SimulationStep, now: datetime) -> dict[str, object]:
        age = max(0.0, (now - step.sensor_state.timestamp).total_seconds())
        return {
            "status": "simulated_snapshot",
            "timestamp": step.sensor_state.timestamp.isoformat(),
            "age_seconds": round(age, 3),
        }
