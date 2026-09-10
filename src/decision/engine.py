"""Deterministic, explainable Water Bank decision engine."""

from __future__ import annotations

from src.config.settings import Settings, get_settings
from src.hydrology.recharge import recharge_available_l
from src.models.decision import Allocation, DecisionAction, DecisionResult
from src.models.node import WaterBankNode
from src.models.sensor_state import SensorState, WaterQualityStatus

from .rules import evaluate_water_quality


def _clamp01(value: float) -> float:
    return min(1.0, max(0.0, value))


class DecisionEngine:
    """Allocate runoff after non-negotiable safety checks.

    All routing is deterministic. Scores communicate priority; physical capacity
    constraints determine the actual allocation.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def evaluate(
        self,
        node: WaterBankNode,
        state: SensorState,
        incoming_l: float,
        *,
        interval_minutes: float = 60.0,
    ) -> DecisionResult:
        if incoming_l < 0:
            raise ValueError("incoming_l cannot be negative")

        quality, safety_reasons = evaluate_water_quality(state, self.settings.quality)
        state.water_quality_status = quality
        storage_available = node.available_storage_l
        recharge_eligible = quality == WaterQualityStatus.SAFE_FOR_RECHARGE
        recharge_available = recharge_available_l(
            node.recharge_capacity_l_per_hour,
            interval_minutes,
            enabled=node.recharge_available,
            quality_allowed=recharge_eligible,
            first_flush_active=state.first_flush_active,
            soil_saturation_percent=state.soil_saturation_percent,
            saturation_block_percent=(
                self.settings.decision.soil_saturation_recharge_block_percent
            ),
        )
        scores = self._scores(node, state, incoming_l, storage_available, recharge_available)

        base_constraints = [
            "Allocation cannot exceed incoming runoff or configured physical capacity.",
            "Recharge is an estimated prototype pathway, not hydrogeological approval.",
        ]
        if quality == WaterQualityStatus.UNSAFE_DIVERT:
            allocation = Allocation(incoming_l=incoming_l, diverted_l=incoming_l)
            return DecisionResult(
                selected_action=DecisionAction.DIVERT,
                priority=1.0,
                reason_codes=safety_reasons + ("SAFETY_GATE_OVERRIDE",),
                human_explanation=(
                    "Recharge and beneficial storage were blocked by the prototype "
                    "water-quality safety gate. Incoming water is routed away from "
                    "recharge for appropriate drainage or treatment."
                ),
                rejected_alternatives={
                    "STORE": "Unsafe water is not accepted into the reusable-water tank.",
                    "RECHARGE": "The quality safety gate is non-negotiable.",
                },
                constraints=tuple(base_constraints + ["Unsafe water must never be recharged."]),
                scores=scores,
                allocation=allocation,
            )

        if state.first_flush_active:
            allocation = Allocation(incoming_l=incoming_l, diverted_l=incoming_l)
            return DecisionResult(
                selected_action=DecisionAction.DIVERT,
                priority=1.0,
                reason_codes=safety_reasons + ("FIRST_FLUSH_DIVERSION",),
                human_explanation=(
                    "The first flush is isolated because it can carry accumulated surface "
                    "pollutants. Direct recharge is blocked and this prototype diverts it "
                    "toward treatment or a safe downstream path."
                ),
                rejected_alternatives={
                    "STORE": "The demo node has no certified first-flush treatment train.",
                    "RECHARGE": "First flush always blocks direct recharge.",
                },
                constraints=tuple(base_constraints + ["First flush blocks direct recharge."]),
                scores=scores,
                allocation=allocation,
            )

        if incoming_l == 0:
            return DecisionResult(
                selected_action=DecisionAction.STORE,
                priority=0.0,
                reason_codes=("NO_INCOMING_RUNOFF", "READINESS_MODE"),
                human_explanation=(
                    "No runoff is arriving. Retained inventory is held while the node "
                    "reports available capacity for the next event."
                ),
                rejected_alternatives={
                    "RECHARGE": "No new inflow requires routing.",
                    "DIVERT": "There is no unsafe inflow to divert.",
                },
                constraints=tuple(base_constraints),
                scores=scores,
                allocation=Allocation(incoming_l=0.0),
            )

        if quality == WaterQualityStatus.SUITABLE_FOR_STORAGE_ONLY:
            stored = min(incoming_l, storage_available)
            diverted = incoming_l - stored
            action = DecisionAction.STORE if stored > 0 else DecisionAction.DIVERT
            explanation = (
                f"Water is suitable only for storage under the prototype quality rules. "
                f"{stored:,.0f} L is stored and {diverted:,.0f} L is diverted; recharge is blocked."
            )
            return DecisionResult(
                selected_action=action,
                priority=max(scores["storage"], 0.75),
                reason_codes=safety_reasons + ("STORAGE_ONLY_QUALITY",),
                human_explanation=explanation,
                rejected_alternatives={
                    "RECHARGE": "Quality did not pass the stricter recharge screen.",
                    "CONTROLLED_DISCHARGE": (
                        "Storage is used first." if stored else "No tank headroom remains."
                    ),
                },
                constraints=tuple(base_constraints + ["Recharge quality criteria were not met."]),
                scores=scores,
                allocation=Allocation(
                    incoming_l=incoming_l, stored_l=stored, diverted_l=diverted
                ),
            )

        stored, recharged, discharged = self._allocate_safe(
            node, incoming_l, storage_available, recharge_available
        )
        allocation = Allocation(
            incoming_l=incoming_l,
            stored_l=stored,
            recharged_l=recharged,
            controlled_discharge_l=discharged,
        )

        if stored > 0 and recharged > 0:
            action = DecisionAction.STORE_AND_RECHARGE
            reasons = ("DUAL_RETENTION_CAPACITY", "QUALITY_GATE_PASSED")
        elif recharged > 0:
            action = DecisionAction.RECHARGE
            reasons = ("RECHARGE_CAPACITY_AVAILABLE", "QUALITY_GATE_PASSED")
        elif stored > 0:
            action = DecisionAction.STORE
            reasons = ("STORAGE_CAPACITY_AVAILABLE", "QUALITY_GATE_PASSED")
        else:
            action = DecisionAction.CONTROLLED_DISCHARGE
            reasons = ("RETENTION_CAPACITY_EXHAUSTED",)

        if discharged > 0:
            reasons += ("RESIDUAL_CONTROLLED_DISCHARGE",)
        if state.soil_saturation_percent >= self.settings.decision.soil_saturation_recharge_block_percent:
            reasons += ("SOIL_SATURATION_BLOCKS_RECHARGE",)
        if not node.recharge_available:
            reasons += ("RECHARGE_PATH_DISABLED",)

        explanation = self._explain_allocation(
            action, allocation, storage_available, recharge_available, state
        )
        rejected = self._rejected(action, node, state, storage_available, recharge_available)
        score_key = {
            DecisionAction.STORE: "storage",
            DecisionAction.RECHARGE: "recharge",
            DecisionAction.STORE_AND_RECHARGE: "retention",
            DecisionAction.CONTROLLED_DISCHARGE: "discharge",
        }[action]
        priority = scores.get(score_key, max(scores["storage"], scores["recharge"]))
        return DecisionResult(
            selected_action=action,
            priority=priority,
            reason_codes=reasons,
            human_explanation=explanation,
            rejected_alternatives=rejected,
            constraints=tuple(base_constraints),
            scores=scores,
            allocation=allocation,
        )

    def _allocate_safe(
        self,
        node: WaterBankNode,
        incoming_l: float,
        storage_available: float,
        recharge_available: float,
    ) -> tuple[float, float, float]:
        if storage_available <= 0:
            recharged = min(incoming_l, recharge_available)
            return 0.0, recharged, incoming_l - recharged
        if recharge_available <= 0:
            stored = min(incoming_l, storage_available)
            return stored, 0.0, incoming_l - stored

        # Preserve the simple preference to fill a tank when it has ample room.
        if node.storage_percent < 75 and incoming_l <= storage_available:
            return incoming_l, 0.0, 0.0

        store_share = 0.35 if node.storage_percent >= 75 else 0.60
        stored = min(storage_available, incoming_l * store_share)
        recharged = min(incoming_l - stored, recharge_available)
        # If recharge capacity was small, use any remaining tank headroom.
        extra_storage = min(
            storage_available - stored, incoming_l - stored - recharged
        )
        stored += max(0.0, extra_storage)
        discharged = max(0.0, incoming_l - stored - recharged)
        return stored, recharged, discharged

    def _scores(
        self,
        node: WaterBankNode,
        state: SensorState,
        incoming_l: float,
        storage_available: float,
        recharge_available: float,
    ) -> dict[str, float]:
        weights = self.settings.weights
        incoming_reference = max(1.0, incoming_l)
        storage_ratio = _clamp01(storage_available / incoming_reference)
        recharge_ratio = _clamp01(recharge_available / incoming_reference)
        drain = _clamp01(state.drain_stress_percent / 100.0)
        soil = _clamp01(state.soil_saturation_percent / 100.0)
        tank_pressure = _clamp01(node.storage_percent / 100.0)
        headroom = 1.0 - tank_pressure
        storage_score = (
            weights.storage_capacity * storage_ratio
            + weights.storage_drain_stress * drain
            + weights.storage_headroom * headroom
        )
        recharge_score = (
            weights.recharge_capacity * recharge_ratio
            + weights.recharge_soil * (1.0 - soil)
            + weights.recharge_drain_stress * drain
            + weights.recharge_tank_pressure * tank_pressure
        )
        discharge_score = (
            weights.discharge_capacity_pressure * (1.0 - max(storage_ratio, recharge_ratio))
            + weights.discharge_soil * soil
            + weights.discharge_drain_stress * drain
        )
        if recharge_available <= 0:
            recharge_score = 0.0
        scores = {
            "storage": round(_clamp01(storage_score), 3),
            "recharge": round(_clamp01(recharge_score), 3),
            "discharge": round(_clamp01(discharge_score), 3),
        }
        scores["retention"] = round(max(scores["storage"], scores["recharge"]), 3)
        return scores

    @staticmethod
    def _explain_allocation(
        action: DecisionAction,
        allocation: Allocation,
        storage_available: float,
        recharge_available: float,
        state: SensorState,
    ) -> str:
        return (
            f"{action.value.replace('_', ' ').title()} is selected after the quality gate passed. "
            f"Of {allocation.incoming_l:,.0f} L of modelled runoff, "
            f"{allocation.stored_l:,.0f} L goes to storage and "
            f"{allocation.recharged_l:,.0f} L goes toward the modelled recharge pathway. "
            f"{allocation.controlled_discharge_l:,.0f} L requires controlled discharge. "
            f"Before routing, tank headroom was {storage_available:,.0f} L, estimated "
            f"interval recharge capacity was {recharge_available:,.0f} L, soil saturation "
            f"was {state.soil_saturation_percent:.0f}%, and drain stress was "
            f"{state.drain_stress_percent:.0f}%."
        )

    @staticmethod
    def _rejected(
        action: DecisionAction,
        node: WaterBankNode,
        state: SensorState,
        storage_available: float,
        recharge_available: float,
    ) -> dict[str, str]:
        rejected: dict[str, str] = {}
        if action not in {DecisionAction.STORE, DecisionAction.STORE_AND_RECHARGE}:
            rejected["STORE"] = (
                "No tank headroom remains."
                if storage_available <= 0
                else "Another route better matches current constraints."
            )
        if action not in {DecisionAction.RECHARGE, DecisionAction.STORE_AND_RECHARGE}:
            if not node.recharge_available:
                rejected["RECHARGE"] = "Recharge is not configured at this node."
            elif recharge_available <= 0:
                rejected["RECHARGE"] = (
                    "Soil saturation or interval capacity blocks recharge."
                )
            else:
                rejected["RECHARGE"] = "Storage can safely accept the current inflow."
        if action != DecisionAction.DIVERT:
            rejected["DIVERT"] = "The water-quality safety gate passed."
        if action != DecisionAction.CONTROLLED_DISCHARGE:
            rejected["CONTROLLED_DISCHARGE"] = (
                "Useful retention capacity is used before discharge."
            )
        return rejected

