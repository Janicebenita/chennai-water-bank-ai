"""In-process repository seeded from local demonstration nodes."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any
from uuid import uuid4

from src.models.node import WaterBankNode

from .repository import Repository


class MemoryRepository(Repository):
    backend_name = "memory"

    def __init__(self, nodes: list[WaterBankNode] | None = None) -> None:
        self._nodes = {node.node_id: deepcopy(node) for node in (nodes or [])}
        self._events: dict[str, list[dict[str, Any]]] = {}

    @classmethod
    def from_demo_data(cls) -> "MemoryRepository":
        data_path = Path(__file__).resolve().parents[2] / "data" / "demo_nodes.json"
        if not data_path.exists():
            return cls([])
        payload = json.loads(data_path.read_text(encoding="utf-8"))
        return cls([WaterBankNode.from_dict(item) for item in payload])

    def list_nodes(self) -> list[WaterBankNode]:
        return [deepcopy(node) for node in self._nodes.values()]

    def save_nodes(self, nodes: list[WaterBankNode]) -> None:
        self._nodes = {node.node_id: deepcopy(node) for node in nodes}

    def save_event(self, collection: str, payload: dict[str, Any]) -> str:
        event_id = str(uuid4())
        self._events.setdefault(collection, []).append({"id": event_id, **payload})
        return event_id

