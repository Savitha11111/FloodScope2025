import importlib.util
from pathlib import Path

import pytest


def test_require_sentinel_hub_credentials_missing(monkeypatch, tmp_path):
    for key in (
        "SENTINEL_HUB_CLIENT_ID",
        "SENTINEL_HUB_CLIENT_SECRET",
        "SENTINELHUB_CLIENT_ID",
        "SENTINELHUB_CLIENT_SECRET",
        "SH_CLIENT_ID",
        "SH_CLIENT_SECRET",
    ):
        monkeypatch.delenv(key, raising=False)

    empty_env = tmp_path / ".env"
    empty_env.write_text("")
    monkeypatch.setenv("FLOODSCOPE_ENV_FILE", str(empty_env))

    config_path = Path(__file__).resolve().parents[1] / "llm" / "config.py"
    spec = importlib.util.spec_from_file_location("llm.config_testcase", config_path)
    config = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(config)

    with pytest.raises(config.MissingSentinelHubCredentialsError) as excinfo:
        config.require_sentinel_hub_credentials()

    message = str(excinfo.value)
    assert "SENTINEL_HUB_CLIENT_ID" in message
    assert "SENTINEL_HUB_CLIENT_SECRET" in message
