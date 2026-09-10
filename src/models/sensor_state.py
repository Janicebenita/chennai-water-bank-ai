"""Normalized sensor data shared by simulator and future IoT adapters."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class WaterQualityStatus(str, Enum):
    SAFE_FOR_RECHARGE = "SAFE_FOR_RECHARGE"
    SUITABLE_FOR_STORAGE_ONLY = "SUITABLE_FOR_STORAGE_ONLY"
    UNSAFE_DIVERT = "UNSAFE_DIVERT"
    UNKNOWN = "UNKNOWN"


@dataclass
class SensorState:
    node_id: str
    rainfall_intensity_mm_hr: float = 0.0
    rainfall_forecast_mm: float = 0.0
    incoming_flow_l_per_min: float = 0.0
    soil_saturation_percent: float = 35.0
    drain_stress_percent: float = 25.0
    turbidity_ntu: float = 3.0
    ph: float = 7.2
    contamination_detected: bool = False
    first_flush_active: bool = False
    water_quality_status: WaterQualityStatus = WaterQualityStatus.UNKNOWN
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        numeric_nonnegative = (
            "rainfall_intensity_mm_hr",
            "rainfall_forecast_mm",
            "incoming_flow_l_per_min",
            "turbidity_ntu",
        )
        for name in numeric_nonnegative:
            if getattr(self, name) < 0:
                raise ValueError(f"{name} cannot be negative")
        self.soil_saturation_percent = min(100.0, max(0.0, self.soil_saturation_percent))
        self.drain_stress_percent = min(100.0, max(0.0, self.drain_stress_percent))

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["timestamp"] = self.timestamp.isoformat()
        payload["water_quality_status"] = self.water_quality_status.value
        return payload
