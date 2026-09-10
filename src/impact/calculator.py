"""Carefully worded modelled-impact calculations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from src.models.decision import DecisionResult


@dataclass(frozen=True)
class ImpactSnapshot:
    stormwater_received_l: float = 0.0
    stored_l: float = 0.0
    recharged_l: float = 0.0
    diverted_l: float = 0.0
    controlled_discharge_l: float = 0.0
    overflow_l: float = 0.0
    available_capacity_l: float = 0.0

    @property
    def retained_l(self) -> float:
        return self.stored_l + self.recharged_l

    @property
    def immediate_runoff_reduction_l(self) -> float:
        return self.retained_l

    @property
    def immediate_downstream_l(self) -> float:
        return self.diverted_l + self.controlled_discharge_l + self.overflow_l

    @property
    def retention_percentage(self) -> float:
        if self.stormwater_received_l <= 0:
            return 0.0
        return 100.0 * self.retained_l / self.stormwater_received_l


def impact_from_decision(
    decision: DecisionResult, *, available_capacity_l: float = 0.0
) -> ImpactSnapshot:
    allocation = decision.allocation
    return ImpactSnapshot(
        stormwater_received_l=allocation.incoming_l,
        stored_l=allocation.stored_l,
        recharged_l=allocation.recharged_l,
        diverted_l=allocation.diverted_l,
        controlled_discharge_l=allocation.controlled_discharge_l,
        available_capacity_l=max(0.0, available_capacity_l),
    )


def aggregate_impacts(impacts: Iterable[ImpactSnapshot]) -> ImpactSnapshot:
    items = list(impacts)
    return ImpactSnapshot(
        stormwater_received_l=sum(item.stormwater_received_l for item in items),
        stored_l=sum(item.stored_l for item in items),
        recharged_l=sum(item.recharged_l for item in items),
        diverted_l=sum(item.diverted_l for item in items),
        controlled_discharge_l=sum(item.controlled_discharge_l for item in items),
        overflow_l=sum(item.overflow_l for item in items),
        available_capacity_l=sum(item.available_capacity_l for item in items),
    )

