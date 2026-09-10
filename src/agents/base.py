"""Contract shared by the four Water Bank advisory agents."""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.models.agent_state import AgentFinding, SharedAgentState


class AdvisoryAgent(ABC):
    name: str

    @abstractmethod
    async def analyze(self, state: SharedAgentState) -> AgentFinding:
        pass
