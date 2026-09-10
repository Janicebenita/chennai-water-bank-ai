"""Digital sensor source and network storm simulator."""

from __future__ import annotations

from abc import ABC, abstractmethod
from copy import deepcopy
from datetime import datetime, timezone
from typing import Iterable

from src.config.settings import Settings, get_settings
from src.decision.engine import DecisionEngine
from src.hydrology.runoff import runoff_volume_l
from src.models.node import WaterBankNode
from src.models.scenario import SimulationStep
from src.models.sensor_state import SensorState

from .rainfall import CHENNAI_STORM_PROFILE_MM_HR, rainfall_depth_for_interval


class SensorDataSource(ABC):
    """Normalized input contract implemented by simulator and future IoT adapters."""

    @abstractmethod
    def read(self, node: WaterBankNode, step_index: int) -> SensorState:
        """Return one normalized reading for a node."""


class DigitalSensorSimulator(SensorDataSource):
    """Deterministic simulated sensor source for repeatable demos and tests."""

    def __init__(
        self,
        rainfall_profile_mm_hr: Iterable[float] = CHENNAI_STORM_PROFILE_MM_HR,
        settings: Settings | None = None,
    ) -> None:
        self.profile = tuple(rainfall_profile_mm_hr)
        if not self.profile:
            raise ValueError("rainfall profile cannot be empty")
        self.settings = settings or get_settings()
        self.engine = DecisionEngine(self.settings)

    def read(self, node: WaterBankNode, step_index: int) -> SensorState:
        intensity = self.profile[min(step_index, len(self.profile) - 1)]
        node_bias = (sum(ord(char) for char in node.node_id) % 13) - 6
        intensity = max(0.0, intensity * (1.0 + node_bias / 100.0))
        soil = min(98.0, 28.0 + step_index * 6.0 + max(node_bias, 0))
        drain = min(100.0, 20.0 + intensity * 0.70 + node.storage_percent * 0.15)
        first_flush = step_index == 0
        # One demonstration node intentionally exercises the safety intervention.
        contamination = node.node_id == "WB-PER-05" and step_index in {
            0,
            1,
            len(self.profile) - 1,
        }
        turbidity = 42.0 if contamination else (18.0 if first_flush else 3.2)
        return SensorState(
            node_id=node.node_id,
            rainfall_intensity_mm_hr=intensity,
            rainfall_forecast_mm=sum(self.profile[step_index + 1 :])
            * self.settings.simulation_interval_minutes
            / 60.0,
            incoming_flow_l_per_min=(
                intensity * node.catchment_area_m2 * node.runoff_coefficient / 60.0
            ),
            soil_saturation_percent=soil,
            drain_stress_percent=drain,
            turbidity_ntu=turbidity,
            ph=6.2 if contamination else 7.2,
            contamination_detected=contamination,
            first_flush_active=first_flush,
            timestamp=datetime.now(timezone.utc),
        )

    def simulate_network(
        self,
        nodes: Iterable[WaterBankNode],
        *,
        steps: int | None = None,
    ) -> list[SimulationStep]:
        working_nodes = [deepcopy(node) for node in nodes]
        step_count = min(steps or len(self.profile), len(self.profile))
        results: list[SimulationStep] = []
        for step_index in range(step_count):
            for node in working_nodes:
                state = self.read(node, step_index)
                rainfall_depth = rainfall_depth_for_interval(
                    state.rainfall_intensity_mm_hr,
                    self.settings.simulation_interval_minutes,
                )
                runoff = runoff_volume_l(
                    rainfall_depth, node.catchment_area_m2, node.runoff_coefficient
                )
                storage_before = node.current_storage_l
                decision = self.engine.evaluate(
                    node,
                    state,
                    runoff,
                    interval_minutes=self.settings.simulation_interval_minutes,
                )
                node.current_storage_l = min(
                    node.storage_capacity_l,
                    node.current_storage_l + decision.allocation.stored_l,
                )
                results.append(
                    SimulationStep(
                        step_index=step_index,
                        node_id=node.node_id,
                        rainfall_depth_mm=rainfall_depth,
                        sensor_state=state,
                        decision=decision,
                        storage_before_l=storage_before,
                        storage_after_l=node.current_storage_l,
                    )
                )
        return results
