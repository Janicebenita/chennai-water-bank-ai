"""Closed-loop physical and digital system explainer.

The visual consumes the same ``DecisionResult`` and simulated sensor values as
the rest of the application. It does not create or mutate simulation state.
"""

from __future__ import annotations

import html
import json
from functools import lru_cache
from pathlib import Path

import streamlit as st

from src.models.decision import DecisionAction, DecisionResult


TEMPLATE_PATH = Path(__file__).with_name("templates") / "physical_process.html"


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return min(high, max(low, value))


@lru_cache(maxsize=1)
def _template() -> str:
    return TEMPLATE_PATH.read_text(encoding="utf-8")


def _command_for(action: DecisionAction) -> tuple[str, str, float]:
    return {
        DecisionAction.STORE: ("ROUTE_TO_STORE", "STORE", -42.0),
        DecisionAction.RECHARGE: ("ROUTE_TO_RECHARGE", "RECHARGE", 0.0),
        DecisionAction.STORE_AND_RECHARGE: (
            "SPLIT_STORE_RECHARGE",
            "SPLIT",
            -12.0,
        ),
        DecisionAction.DIVERT: ("ISOLATE_AND_DIVERT", "DIVERT", 42.0),
        DecisionAction.CONTROLLED_DISCHARGE: (
            "OPEN_CONTROLLED_DISCHARGE",
            "DISCHARGE",
            42.0,
        ),
    }[action]


def _human_reason(reason_code: str) -> str:
    labels = {
        "QUALITY_GATE_PASSED": "Water quality passed the applicable prototype screen",
        "STORAGE_CAPACITY_AVAILABLE": "Storage capacity is available",
        "RECHARGE_CAPACITY_AVAILABLE": "Estimated recharge capacity is available",
        "DUAL_RETENTION_CAPACITY": "Storage and modelled recharge can operate together",
        "SAFETY_GATE_OVERRIDE": "Safety gate overrides beneficial retention",
        "FIRST_FLUSH_DIVERSION": "First flush is isolated from direct recharge",
        "RETENTION_CAPACITY_EXHAUSTED": "Local retention capacity is exhausted",
        "RESIDUAL_CONTROLLED_DISCHARGE": "Residual flow requires controlled discharge",
        "SOIL_SATURATION_BLOCKS_RECHARGE": "Soil saturation blocks modelled recharge",
        "RECHARGE_PATH_DISABLED": "Recharge infrastructure is unavailable",
        "STORAGE_ONLY_QUALITY": "Quality permits storage but blocks recharge",
        "NO_INCOMING_RUNOFF": "No incoming runoff requires routing",
        "READINESS_MODE": "Node is reporting next-event readiness",
    }
    return labels.get(reason_code, reason_code.replace("_", " ").title())


def physical_process_animation(
    decision: DecisionResult,
    *,
    tank_fill_percent: float,
    soil_saturation_percent: float,
    node_name: str,
    tank_before_percent: float | None = None,
    rainfall_intensity_mm_hr: float | None = None,
    turbidity_ntu: float | None = None,
    ph: float | None = None,
    flow_rate_l_s: float | None = None,
    available_storage_l: float | None = None,
    drain_stress_percent: float | None = None,
    quality_status: str | None = None,
) -> None:
    """Render the deterministic eight-scene system story.

    All numeric values come from the caller's current simulation state. The
    embedded JavaScript only controls presentation scenes and never performs a
    second hydrology or decision calculation.
    """
    allocation = decision.allocation
    action = decision.selected_action
    command, router_target, router_angle = _command_for(action)
    store_active = action in {DecisionAction.STORE, DecisionAction.STORE_AND_RECHARGE}
    recharge_active = action in {
        DecisionAction.RECHARGE,
        DecisionAction.STORE_AND_RECHARGE,
    }
    downstream_active = action in {
        DecisionAction.DIVERT,
        DecisionAction.CONTROLLED_DISCHARGE,
    }
    downstream_l = allocation.diverted_l + allocation.controlled_discharge_l
    downstream_label = (
        "SAFETY DIVERSION"
        if action == DecisionAction.DIVERT
        else "CONTROLLED DISCHARGE"
    )
    downstream_detail = (
        "To treatment or an approved drainage path — never direct recharge"
        if action == DecisionAction.DIVERT
        else "Metered residual flow after useful local capacity is exhausted"
    )
    downstream_color = "#ff6b6b" if action == DecisionAction.DIVERT else "#f7bd58"
    quality_passed = action != DecisionAction.DIVERT
    gate_color = "#69d39c" if quality_passed else "#ff6b6b"
    gate_symbol = "✓" if quality_passed else "!"
    gate_detail = (
        "Passed for selected route" if quality_passed else "Unsafe input blocks retention"
    )

    tank_after = _clamp(tank_fill_percent)
    tank_before = _clamp(
        tank_before_percent if tank_before_percent is not None else tank_after
    )
    soil = _clamp(soil_saturation_percent)
    rainfall = max(0.0, rainfall_intensity_mm_hr or 0.0)
    turbidity = max(0.0, turbidity_ntu or 0.0)
    current_ph = ph if ph is not None else 7.2
    flow_rate = max(
        0.0,
        flow_rate_l_s
        if flow_rate_l_s is not None
        else allocation.incoming_l / 3600.0,
    )
    storage_available = max(0.0, available_storage_l or 0.0)
    drain_stress = _clamp(drain_stress_percent or 0.0)
    quality = quality_status or (
        "UNSAFE_DIVERT" if action == DecisionAction.DIVERT else "SAFE"
    )
    quality_display = quality.replace("_", " ")
    action_display = action.value.replace("_", " ")
    reasons = decision.reason_codes[:4] or ("CAPACITY_CONSTRAINED_ROUTING",)
    reasons_html = "".join(
        f'<li><span aria-hidden="true">✓</span>{html.escape(_human_reason(reason))}</li>'
        for reason in reasons
    )

    system_data = {
        "action": action_display,
        "command": command,
        "routerTarget": router_target,
        "routerAngle": router_angle,
        "tankBefore": round(tank_before, 1),
        "tankAfter": round(tank_after, 1),
        "qualityPassed": quality_passed,
        "captions": [
            "Rainfall is collected, first-flush water is separated, and the remaining flow is filtered and prepared for routing.",
            "Simulated field sensors measure rainfall, tank level, water quality, soil saturation, flow, and actuator position.",
            "The edge controller normalizes field readings into one node-telemetry packet and sends it to the software.",
            "The software combines telemetry with transparent hydrology calculations, safety gates, physical capacity, and network context.",
            f"The explainable engine selects {action_display}. The decision is deterministic and its reasons remain visible.",
            f"The software emits {command}; the edge controller, motor driver, and relay translate it into an electrical actuator command.",
            f"The motorized router moves from NEUTRAL to {router_target}, physically changing the water path while the selected route begins flowing.",
            "Position, flow, and destination sensors report the result. The software verifies the command and uses that feedback for the next cycle.",
        ],
    }
    system_data_json = json.dumps(system_data, separators=(",", ":")).replace(
        "<", "\\u003c"
    )

    replacements = {
        "NODE_NAME": html.escape(node_name),
        "ACTION": html.escape(action_display),
        "COMMAND": html.escape(command),
        "ROUTER_TARGET": html.escape(router_target),
        "ROUTER_ANGLE": f"{router_angle:.0f}deg",
        "INCOMING_L": f"{allocation.incoming_l:,.0f}",
        "STORED_L": f"{allocation.stored_l:,.0f}",
        "RECHARGED_L": f"{allocation.recharged_l:,.0f}",
        "DOWNSTREAM_L": f"{downstream_l:,.0f}",
        "TANK_BEFORE": f"{tank_before:.0f}",
        "TANK_AFTER": f"{tank_after:.0f}",
        "SOIL": f"{soil:.0f}",
        "RAINFALL": f"{rainfall:.1f}",
        "TURBIDITY": f"{turbidity:.1f}",
        "PH": f"{current_ph:.1f}",
        "FLOW": f"{flow_rate:.2f}",
        "AVAILABLE_STORAGE": f"{storage_available / 1000:,.1f}",
        "DRAIN_STRESS": f"{drain_stress:.0f}",
        "QUALITY": html.escape(quality_display),
        "QUALITY_SHORT": "SAFE" if quality_passed else "BLOCKED",
        "GATE_COLOR": gate_color,
        "GATE_SYMBOL": gate_symbol,
        "GATE_DETAIL": gate_detail,
        "STORE_CLASS": "active" if store_active else "inactive",
        "RECHARGE_CLASS": "active" if recharge_active else "inactive",
        "DOWNSTREAM_CLASS": "active" if downstream_active else "inactive",
        "STORE_STATUS": "ACTIVE PATH" if store_active else "IDLE THIS PULSE",
        "RECHARGE_STATUS": (
            "ACTIVE ESTIMATED PATH" if recharge_active else "BLOCKED / IDLE"
        ),
        "DOWNSTREAM_STATUS": (
            "ACTIVE SAFETY / CAPACITY PATH" if downstream_active else "NOT REQUIRED"
        ),
        "DOWNSTREAM_LABEL": downstream_label,
        "DOWNSTREAM_DETAIL": downstream_detail,
        "DOWNSTREAM_COLOR": downstream_color,
        "REASONS_HTML": reasons_html,
        "SYSTEM_DATA_JSON": system_data_json,
    }
    markup = _template()
    for key, value in replacements.items():
        markup = markup.replace(f"@@{key}@@", str(value))
    if "@@" in markup:
        raise RuntimeError("Physical-process template contains an unresolved token")
    st.iframe(markup, height=1460, width="stretch", tab_index=0)
