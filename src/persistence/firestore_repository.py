"""Optional Google Cloud Firestore adapter using Application Default Credentials."""

from __future__ import annotations

from typing import Any

from src.config.settings import Settings
from src.models.node import WaterBankNode

from .repository import Repository


class FirestoreRepository(Repository):
    backend_name = "firestore"
    allowed_event_collections = {
        "simulation_runs",
        "node_events",
        "decisions",
        "impact_snapshots",
    }

    def __init__(self, settings: Settings) -> None:
        from google.cloud import firestore

        self.client = firestore.Client(
            project=settings.gcp_project, database=settings.firestore_database
        )

    def health_check(self) -> None:
        # A bounded read validates credentials without writing cloud state.
        next(iter(self.client.collection("nodes").limit(1).stream()), None)

    def list_nodes(self) -> list[WaterBankNode]:
        return [WaterBankNode.from_dict(item.to_dict()) for item in self.client.collection("nodes").stream()]

    def save_nodes(self, nodes: list[WaterBankNode]) -> None:
        batch = self.client.batch()
        for node in nodes:
            batch.set(self.client.collection("nodes").document(node.node_id), node.to_dict())
        batch.commit()

    def save_event(self, collection: str, payload: dict[str, Any]) -> str:
        if collection not in self.allowed_event_collections:
            raise ValueError(f"Unsupported event collection: {collection}")
        _, reference = self.client.collection(collection).add(payload)
        return reference.id

