from kicli_code_assist.ui.config import BackendConfig
from kicli_code_assist.web import server_config
from kicli_code_assist.web.server_config import get_web_settings


def test_web_settings_default_to_assigned_development_port():
    assert get_web_settings({}) == ("127.0.0.1", 8100)


def test_web_settings_follow_stage_service_port():
    config = {
        "stack": {
            "services": {
                "web": {"host": "127.0.0.1", "port": 8000},
            },
        },
    }

    assert get_web_settings(config) == ("127.0.0.1", 8000)


def test_web_settings_prefer_unified_production_service():
    config = {
        "stack": {
            "services": {
                "api": {"host": "127.0.0.1", "port": 8100},
                "web": {"host": "127.0.0.1", "port": 8000},
            },
        },
    }

    assert get_web_settings(config) == ("127.0.0.1", 8000)


def test_web_setting_overrides_stage_service_port():
    config = {
        "web": {"host": "localhost", "port": 8201},
        "stack": {"services": {"api": {"host": "127.0.0.1", "port": 8100}}},
    }

    assert get_web_settings(config) == ("localhost", 8201)


def test_tui_backend_defaults_to_assigned_development_port():
    assert BackendConfig().url == "http://localhost:8100"


def test_config_fallback_preserves_production_port(monkeypatch):
    class FailedConfigManager:
        def load(self, **kwargs):
            raise RuntimeError("configuration unavailable")

    monkeypatch.setattr(server_config, "ConfigManager", FailedConfigManager)
    monkeypatch.setenv("KI_STAGE", "production")

    assert server_config.get_config()["web"]["port"] == 8000
