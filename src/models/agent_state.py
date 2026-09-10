"""Typed shared state and outputs for collaborative advisory agents."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from collections.abc import Mapping
from typing import Any


@dataclass(frozen=True)
class SemanticEvidence:
    evidence_id: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)
    relevance: float | None = None


@dataclass(frozen=True)
class AgentFinding:
    agent: str
    status: str
    summary: str
    recommendation: str
    evidence_refs: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    latency_ms: float = 0.0


@dataclass(frozen=True)
class LatencyMetrics:
    moss_retrieval_ms: float | None = None
    agent_rain_risk_ms: float | None = None
    agent_incident_memory_ms: float | None = None
    agent_capacity_ms: float | None = None
    agent_asset_maintenance_ms: float | None = None
    orchestrator_ms: float = 0.0
    total_request_ms: float = 0.0


@dataclass
class SharedAgentState:
    request_id: str
    timestamp: datetime
    zone_id: str
    asset_ids: tuple[str, ...]
    user_intent: str
    authoritative_facts: Mapping[str, Any]
    authoritative_fact_refs: tuple[str, ...]
    moss_query: str
    moss_context: tuple[SemanticEvidence, ...] = ()
    moss_context_refs: tuple[str, ...] = ()
    moss_retrieval_ms: float | None = None
    findings: dict[str, AgentFinding] = field(default_factory=dict)
    evidence: tuple[SemanticEvidence, ...] = ()
    limitations: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    status: str = "pending"
    semantic_context_status: str = "disabled"
    human_approval_state: str = "pending"


@dataclass(frozen=True)
class OrchestratorResult:
    recommendation: str
    live_facts: dict[str, Any]
    semantic_context: tuple[SemanticEvidence, ...]
    agent_findings: dict[str, AgentFinding]
    evidence: tuple[SemanticEvidence, ...]
    uncertainty: tuple[str, ...]
    limitations: tuple[str, ...]
    warnings: tuple[str, ...]
    data_freshness: dict[str, Any]
    latency: LatencyMetrics
    moss_status: str
    moss_results_count: int
    human_approval_state: str = "pending"
