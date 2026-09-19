"""Offline Streamlit workflows verify real page rendering and human review."""

from pathlib import Path

import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

from src.config.settings import get_settings

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def offline_ui(monkeypatch):
    monkeypatch.setenv("DATA_BACKEND", "memory")
    monkeypatch.setenv("MOSS_ENABLED", "false")
    get_settings.cache_clear()
    st.cache_resource.clear()
    st.cache_data.clear()
    yield
    st.cache_resource.clear()
    st.cache_data.clear()
    get_settings.cache_clear()


@pytest.mark.parametrize(
    "page",
    ["app.py"]
    + [str(p.relative_to(ROOT)) for p in sorted((ROOT / "pages").glob("*.py"))],
)
def test_pages_render_with_simulation_disclosures(page):
    app = AppTest.from_file(str(ROOT / page), default_timeout=20).run()
    assert not app.exception
    assert any("simulated prototype data" in item.value for item in app.caption)
    assert any("Persistence: MEMORY" in item.value for item in app.caption)
    assert len(app.markdown) > 0


def button(app, label):
    return next(item for item in app.button if item.label == label)


def test_storm_and_human_review_workflow():
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=20).run()
    button(app, "SIMULATE CHENNAI STORM").click().run()
    assert not app.exception
    assert app.session_state["storm_complete"] is True
    assert len(app.session_state["storm_steps"]) == 48
    button(app, "RUN COLLABORATIVE ANALYSIS").click().run()
    assert not app.exception
    result = app.session_state["ai_orchestration_result"]
    assert result.moss_status == "disabled"
    assert result.semantic_context == ()
    assert app.session_state["ai_human_review"] == "pending"
    for label, expected in [
        ("Accept advisory", "accepted"),
        ("Reject advisory", "rejected"),
        ("Request more evidence", "more_evidence_requested"),
    ]:
        button(app, label).click().run()
        assert not app.exception
        assert app.session_state["ai_human_review"] == expected
        assert (
            app.session_state["ai_orchestration_result"].live_facts == result.live_facts
        )
    button(app, "Reset simulation").click().run()
    assert not app.exception
    assert app.session_state["storm_complete"] is False


def test_impact_displays_calculated_retention_and_discharge():
    app = AppTest.from_file(
        str(ROOT / "pages/05_impact_analytics.py"), default_timeout=20
    ).run()
    assert not app.exception
    text = " ".join(item.value for item in app.markdown)
    assert "Safety diversion:" in text
    assert "Controlled discharge:" in text
    assert "of simulated immediate runoff was locally retained" in text
    assert "not a hydraulic flood-depth or damage model" in text


def test_sidebar_exposes_degraded_persistence(monkeypatch):
    from src.persistence.memory_repository import MemoryRepository

    repo = MemoryRepository.from_demo_data()
    repo.degraded_reason = "Firestore retry limit reached."
    monkeypatch.setattr("src.ui.runtime.repository", lambda: repo)
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=20).run()
    assert not app.exception
    assert any("Persistence: MEMORY FALLBACK" in item.value for item in app.caption)
    assert any(item.value == repo.degraded_reason for item in app.warning)
