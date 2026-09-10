"""Water Bank node configuration and mutable storage state."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class WaterBankNode:
    node_id: str
    name: str
    zone: str
    latitude: float
    longitude: float
    catchment_area_m2: float
    runoff_coefficient: float
    storage_capacity_l: float
    current_storage_l: float
    recharge_capacity_l_per_hour: float
    recharge_available: bool = True

    def __post_init__(self) -> None:
        if self.catchment_area_m2 <= 0:
            raise ValueError("catchment_area_m2 must be positive")
        if not 0 <= self.runoff_coefficient <= 1:
            raise ValueError("runoff_coefficient must be between 0 and 1")
        if self.storage_capacity_l < 0 or self.recharge_capacity_l_per_hour < 0:
            raise ValueError("capacities cannot be negative")
        self.current_storage_l = min(
            self.storage_capacity_l, max(0.0, self.current_storage_l)
        )

    @property
    def available_storage_l(self) -> float:
        return max(0.0, self.storage_capacity_l - self.current_storage_l)

    @property
    def storage_percent(self) -> float:
        if self.storage_capacity_l == 0:
            return 100.0
        return 100.0 * self.current_storage_l / self.storage_capacity_l

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "WaterBankNode":
        allowed = cls.__dataclass_fields__.keys()
        return cls(**{key: payload[key] for key in allowed})

