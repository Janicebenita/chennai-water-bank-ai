"""Explainable routing decision models."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class DecisionAction(str, Enum):
    STORE = "STORE"
    RECHARGE = "RECHARGE"
    STORE_AND_RECHARGE = "STORE_AND_RECHARGE"
    DIVERT = "DIVERT"
    CONTROLLED_DISCHARGE = "CONTROLLED_DISCHARGE"


@dataclass(frozen=True)
class Allocation:
    incoming_l: float
    stored_l: float = 0.0
    recharged_l: float = 0.0
    diverted_l: float = 0.0
    controlled_discharge_l: float = 0.0

    @property
    def retained_l(self) -> float:
        return self.stored_l + self.recharged_l

    @property
    def downstream_l(self) -> float:
        return self.diverted_l + self.controlled_discharge_l

    @property
    def mass_balance_error_l(self) -> float:
        allocated = self.retained_l + self.downstream_l
        return self.incoming_l - allocated


@dataclass(frozen=True)
class DecisionResult:
    selected_action: DecisionAction
    priority: float
    reason_codes: tuple[str, ...]
    human_explanation: str
    rejected_alternatives: dict[str, str]
    constraints: tuple[str, ...]
    scores: dict[str, float]
    allocation: Allocation

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["selected_action"] = self.selected_action.value
        return payload

