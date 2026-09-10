"""Streamlit runtime state and simulation helpers."""

from __future__ import annotations

import streamlit as st

from src.impact.calculator import ImpactSnapshot, aggregate_impacts, impact_from_decision
from src.models.node import WaterBankNode
from src.models.scenario import SimulationStep
from src.persistence.memory_repository import MemoryRepository
from src.persistence.repository import get_repository
from src.simulation.simulator import DigitalSensorSimulator


@st.cache_resource
def repository():
    return get_repository()


def load_nodes() -> list[WaterBankNode]:
    repo = repository()
    nodes = repo.list_nodes()
    if not nodes:
        nodes = MemoryRepository.from_demo_data().list_nodes()
    return nodes


@st.cache_data(show_spinner=False)
def baseline_steps() -> list[SimulationStep]:
    # Four pulses create a varied, populated command center on first launch.
    return DigitalSensorSimulator().simulate_network(load_nodes(), steps=4)


def get_active_steps() -> list[SimulationStep]:
    return st.session_state.get("storm_steps", baseline_steps())


def run_full_storm() -> list[SimulationStep]:
    steps = DigitalSensorSimulator().simulate_network(load_nodes())
    st.session_state["storm_steps"] = steps
    st.session_state["storm_complete"] = True
    return steps


def reset_storm() -> None:
    st.session_state.pop("storm_steps", None)
    st.session_state["storm_complete"] = False
    st.session_state["storm_running"] = False


def network_impact(steps: list[SimulationStep]) -> ImpactSnapshot:
    return aggregate_impacts(impact_from_decision(step.decision) for step in steps)

