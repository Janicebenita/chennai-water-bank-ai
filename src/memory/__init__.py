"""Semantic-memory selection with safe disabled and failure modes."""

from __future__ import annotations

from src.config.settings import Settings, get_settings

from .null_semantic_memory import NullSemanticMemory
from .semantic_memory import SemanticMemory


def get_semantic_memory(settings: Settings | None = None) -> SemanticMemory:
    active = settings or get_settings()
    if not active.moss_enabled:
        return NullSemanticMemory()
    if not active.moss_project_id or not active.moss_project_key:
        return NullSemanticMemory(
            "unavailable",
            "Moss is enabled but required credentials are not configured.",
        )
    try:
        from .moss_semantic_memory import MossSemanticMemory

        return MossSemanticMemory(
            active.moss_project_id,
            active.moss_project_key,
            active.moss_index_name,
        )
    except Exception:
        return NullSemanticMemory("unavailable", "Moss initialization failed.")


__all__ = ["SemanticMemory", "get_semantic_memory"]
