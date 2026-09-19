"""Scenario and simulation result models."""

from __future__ import annotations

from dataclasses import dataclass

from .decision import DecisionResult
from .sensor_state import SensorState


@dataclass(frozen=True)
class ScenarioDefinition:
    scenario_id: str
    name: str
    description: str
    rainfall_mm: float
    rainfall_intensity_mm_hr: float
    catchment_area_m2: float
    runoff_coefficient: float
    storage_capacity_l: float
    current_storage_l: float
    recharge_capacity_l_per_hour: float
    recharge_available: bool
    soil_saturation_percent: float
    drain_stress_percent: float
    turbidity_ntu: float
    ph: float
    contamination_detected: bool = False
    first_flush_active: bool = False
    duration_minutes: int = 60
    expected_tendency: str = ""


@dataclass(frozen=True)
class SimulationStep:
    step_index: int
    node_id: str
    rainfall_depth_mm: float
    sensor_state: SensorState
    decision: DecisionResult
    storage_before_l: float
    storage_after_l: float

