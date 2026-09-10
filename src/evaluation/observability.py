"""Credential-free structured logs for AI-path timing and health."""

from __future__ import annotations

import json
import logging
from typing import Any


LOGGER = logging.getLogger("chennai_water_bank.ai")


def log_orchestration_metrics(payload: dict[str, Any]) -> None:
    allowed = {
        "request_id",
        "moss_retrieval_ms",
        "moss_results_count",
        "moss_status",
        "agent_rain_risk_ms",
        "agent_incident_memory_ms",
        "agent_capacity_ms",
        "agent_asset_maintenance_ms",
        "agent_failures",
        "orchestrator_ms",
        "total_request_ms",
        "evidence_count",
        "data_freshness",
    }
    sanitized = {key: payload[key] for key in allowed if key in payload}
    LOGGER.info(json.dumps({"event": "ai_orchestration", **sanitized}, sort_keys=True))
