"""Semantic event representation derived from authoritative Water Bank facts."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class WaterEvent:
    """An additive, evidence-linked representation for semantic retrieval.

    This model never replaces the structured operational record. Its text is a
    derived search document and ``source_refs`` point back to that record.
    """

    event_id: str
    timestamp: datetime
    asset_id: str
    zone_id: str
    event_type: str
    operational_summary: str
    risk_context: str
    action: str
    outcome: str
    semantic_text: str
    source_refs: tuple[str, ...] = ()
    metadata: dict[str, str | int | float | bool] = field(default_factory=dict)

    def __post_init__(self) -> None:
        required = {
            "event_id": self.event_id,
            "asset_id": self.asset_id,
            "zone_id": self.zone_id,
            "event_type": self.event_type,
            "semantic_text": self.semantic_text,
        }
        missing = [name for name, value in required.items() if not str(value).strip()]
        if missing:
            raise ValueError(f"WaterEvent requires: {', '.join(missing)}")
        if self.timestamp.tzinfo is None:
            raise ValueError("WaterEvent timestamp must be timezone-aware")

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp.astimezone(timezone.utc).isoformat(),
            "asset_id": self.asset_id,
            "zone_id": self.zone_id,
            "event_type": self.event_type,
            "operational_summary": self.operational_summary,
            "risk_context": self.risk_context,
            "action": self.action,
            "outcome": self.outcome,
            "semantic_text": self.semantic_text,
            "source_refs": list(self.source_refs),
            "metadata": dict(self.metadata),
        }

    def moss_metadata(self) -> dict[str, str]:
        """Return Moss-compatible string metadata without changing source types."""
        values = {
            "event_id": self.event_id,
            "timestamp": self.timestamp.astimezone(timezone.utc).isoformat(),
            "zone_id": self.zone_id,
            "asset_id": self.asset_id,
            "event_type": self.event_type,
            "action": self.action,
            **self.metadata,
        }
        return {
            key: str(value).lower() if isinstance(value, bool) else str(value)
            for key, value in values.items()
        }
