"""Auditable water-quality and recharge safety gates."""

from __future__ import annotations

from src.config.settings import QualityThresholds
from src.models.sensor_state import SensorState, WaterQualityStatus


def evaluate_water_quality(
    state: SensorState, thresholds: QualityThresholds
) -> tuple[WaterQualityStatus, tuple[str, ...]]:
    """Classify simulated water quality using deliberately conservative rules."""
    reasons: list[str] = []
    if state.contamination_detected:
        return WaterQualityStatus.UNSAFE_DIVERT, ("CONTAMINATION_DETECTED",)
    if not thresholds.ph_min <= state.ph <= thresholds.ph_max:
        return WaterQualityStatus.UNSAFE_DIVERT, ("PH_OUT_OF_SAFE_RANGE",)
    if state.first_flush_active:
        reasons.append("FIRST_FLUSH_BLOCKS_RECHARGE")
        return WaterQualityStatus.SUITABLE_FOR_STORAGE_ONLY, tuple(reasons)
    if state.turbidity_ntu <= thresholds.recharge_turbidity_max_ntu:
        return WaterQualityStatus.SAFE_FOR_RECHARGE, ("QUALITY_GATE_PASSED",)
    if state.turbidity_ntu <= thresholds.storage_turbidity_max_ntu:
        return WaterQualityStatus.SUITABLE_FOR_STORAGE_ONLY, (
            "TURBIDITY_BLOCKS_RECHARGE",
        )
    return WaterQualityStatus.UNSAFE_DIVERT, ("TURBIDITY_UNSAFE",)

