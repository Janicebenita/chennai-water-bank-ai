"""Scenario execution and transparent mathematics UI."""

from __future__ import annotations

import streamlit as st

from src.decision.engine import DecisionEngine
from src.hydrology.runoff import runoff_volume_l
from src.models.node import WaterBankNode
from src.models.scenario import ScenarioDefinition
from src.models.sensor_state import SensorState


def run_scenario(scenario: ScenarioDefinition):
    node = WaterBankNode(
        node_id=f"SC-{scenario.scenario_id}",
        name=scenario.name,
        zone="Judge Lab",
        latitude=13.0827,
        longitude=80.2707,
        catchment_area_m2=scenario.catchment_area_m2,
        runoff_coefficient=scenario.runoff_coefficient,
        storage_capacity_l=scenario.storage_capacity_l,
        current_storage_l=scenario.current_storage_l,
        recharge_capacity_l_per_hour=scenario.recharge_capacity_l_per_hour,
        recharge_available=scenario.recharge_available,
    )
    runoff = runoff_volume_l(
        scenario.rainfall_mm, scenario.catchment_area_m2, scenario.runoff_coefficient
    )
    state = SensorState(
        node_id=node.node_id,
        rainfall_intensity_mm_hr=scenario.rainfall_intensity_mm_hr,
        rainfall_forecast_mm=scenario.rainfall_mm,
        incoming_flow_l_per_min=(
            runoff / scenario.duration_minutes if scenario.duration_minutes > 0 else 0.0
        ),
        soil_saturation_percent=scenario.soil_saturation_percent,
        drain_stress_percent=scenario.drain_stress_percent,
        turbidity_ntu=scenario.turbidity_ntu,
        ph=scenario.ph,
        contamination_detected=scenario.contamination_detected,
        first_flush_active=scenario.first_flush_active,
    )
    decision = DecisionEngine().evaluate(
        node, state, runoff, interval_minutes=scenario.duration_minutes
    )
    return node, state, runoff, decision


def show_mathematics(scenario: ScenarioDefinition, runoff: float, decision) -> None:
    with st.expander("Show the Mathematics", expanded=False):
        allocation = decision.allocation
        st.code(
            f"""Rainfall depth          = {scenario.rainfall_mm:,.2f} mm
Catchment area         = {scenario.catchment_area_m2:,.2f} m²
Runoff coefficient     = {scenario.runoff_coefficient:.2f}

Calculated runoff      = rainfall × area × coefficient
                       = {scenario.rainfall_mm:,.2f} × {scenario.catchment_area_m2:,.2f} × {scenario.runoff_coefficient:.2f}
                       = {runoff:,.2f} L

Available storage      = {scenario.storage_capacity_l:,.2f} − {scenario.current_storage_l:,.2f}
                       = {scenario.storage_capacity_l - scenario.current_storage_l:,.2f} L
Stored                 = {allocation.stored_l:,.2f} L
Recharged (estimated)  = {allocation.recharged_l:,.2f} L
Diverted               = {allocation.diverted_l:,.2f} L
Controlled discharge   = {allocation.controlled_discharge_l:,.2f} L
Mass-balance error     = {allocation.mass_balance_error_l:,.6f} L""",
            language="text",
        )
