from src.config.settings import get_settings


def test_moss_defaults_disabled_and_handles_invalid_top_k(monkeypatch):
    monkeypatch.delenv("MOSS_ENABLED", raising=False)
    monkeypatch.setenv("MOSS_TOP_K", "not-a-number")
    get_settings.cache_clear()
    try:
        settings = get_settings()
        assert settings.moss_enabled is False
        assert settings.moss_top_k == 4
    finally:
        get_settings.cache_clear()


def test_moss_secret_is_not_in_settings_repr():
    from src.config.settings import Settings

    settings = Settings(moss_project_key="sensitive-value")
    assert "sensitive-value" not in repr(settings)
