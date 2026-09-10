"""Build evidence-linked semantic events from existing simulation results."""

from __future__ import annotations

from uuid import NAMESPACE_URL, uuid5

from src.config.settings import Settings, get_settings
from src.models.decision import DecisionAction
from src.models.node import WaterBankNode
from src.models.scenario import SimulationStep
from src.models.water_event import WaterEvent


class EventContextBuilder:
    """Create concise WaterEvents without changing authoritative source data."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def build(self, node: WaterBankNode, step: SimulationStep) -> WaterEvent | None:
        state = step.sensor_state
        allocation = step.decision.allocation
        meaningful = (
            allocation.incoming_l > 0
            or state.contamination_detected
            or state.first_flush_active
            or state.drain_stress_percent
            >= self.settings.decision.high_drain_stress_percent
        )
        if not meaningful:
            return None

        event_type, severity = self._classify(step)
        event_key = "|".join(
            (
                node.node_id,
                state.timestamp.isoformat(),
                str(step.step_index),
                event_type,
                step.decision.selected_action.value,
            )
        )
        event_id = str(uuid5(NAMESPACE_URL, f"chennai-water-bank:{event_key}"))
        operational_summary = (
            f"SIMULATED DATA at {node.name}: rainfall "
            f"{state.rainfall_intensity_mm_hr:.1f} mm/hr, tank after routing "
            f"{self._tank_percent(node, step):.1f}%, soil saturation "
            f"{state.soil_saturation_percent:.1f}%, and drain stress "
            f"{state.drain_stress_percent:.1f}%."
        )
        risk_context = (
            f"Water quality {state.water_quality_status.value}; "
            f"first flush {'active' if state.first_flush_active else 'cleared'}; "
            f"contamination {'detected' if state.contamination_detected else 'not detected'}."
        )
        outcome = (
            f"Of {allocation.incoming_l:.1f} L modelled runoff, "
            f"{allocation.stored_l:.1f} L stored, {allocation.recharged_l:.1f} L "
            f"routed toward modelled recharge, and {allocation.downstream_l:.1f} L downstream."
        )
        semantic_text = " ".join(
            (
                operational_summary,
                risk_context,
                f"Decision {step.decision.selected_action.value}.",
                outcome,
                "This is a fictional demonstration-node event, not a measured Chennai incident.",
            )
        )
        source_refs = (
            f"sensor:{node.node_id}:{state.timestamp.isoformat()}",
            f"decision:{node.node_id}:{step.step_index}",
        )
        return WaterEvent(
            event_id=event_id,
            timestamp=state.timestamp,
            asset_id=node.node_id,
            zone_id=node.zone,
            event_type=event_type,
            operational_summary=operational_summary,
            risk_context=risk_context,
            action=step.decision.selected_action.value,
            outcome=outcome,
            semantic_text=semantic_text,
            source_refs=source_refs,
            metadata={
                "severity": severity,
                "source": "digital_sensor_simulator",
                "simulated": True,
                "step_index": step.step_index,
            },
        )

    def _classify(self, step: SimulationStep) -> tuple[str, str]:
        state = step.sensor_state
        action = step.decision.selected_action
        if state.contamination_detected or state.first_flush_active:
            return "WATER_QUALITY_INTERVENTION", "high"
        if action == DecisionAction.CONTROLLED_DISCHARGE:
            return "CAPACITY_CONSTRAINT", "high"
        if state.drain_stress_percent >= self.settings.decision.high_drain_stress_percent:
            return "HIGH_DRAIN_STRESS", "high"
        if action in {DecisionAction.RECHARGE, DecisionAction.STORE_AND_RECHARGE}:
            return "RECHARGE_OPPORTUNITY", "moderate"
        return "STORAGE_ROUTING", "moderate"

    @staticmethod
    def _tank_percent(node: WaterBankNode, step: SimulationStep) -> float:
        if node.storage_capacity_l <= 0:
            return 100.0
        return 100.0 * step.storage_after_l / node.storage_capacity_l
