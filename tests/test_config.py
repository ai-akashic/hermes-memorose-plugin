import json

import pytest

from config import MemoroseConfig, MemoroseConfigError, load_memorose_config


def test_load_memorose_config_reads_json_and_env(monkeypatch, tmp_path):
    monkeypatch.setenv("MEMOROSE_API_KEY", "test-key")
    config_path = tmp_path / "memorose.json"
    config_path.write_text(
        json.dumps(
            {
                "base_url": "http://127.0.0.1:3000",
                "org_id": "org-1",
                "retrieve": {"limit": 5, "min_score": 0.2, "graph_depth": 2},
                "sync": {"mode": "user_only"},
            }
        )
    )

    cfg = load_memorose_config(str(tmp_path))

    assert cfg == MemoroseConfig(
        base_url="http://127.0.0.1:3000",
        api_key="test-key",
        org_id="org-1",
        retrieve_limit=5,
        retrieve_min_score=0.2,
        retrieve_graph_depth=2,
        sync_mode="user_only",
    )


def test_load_memorose_config_requires_api_key(monkeypatch, tmp_path):
    monkeypatch.delenv("MEMOROSE_API_KEY", raising=False)
    (tmp_path / "memorose.json").write_text(json.dumps({"base_url": "http://127.0.0.1:3000"}))

    with pytest.raises(MemoroseConfigError, match="MEMOROSE_API_KEY"):
        load_memorose_config(str(tmp_path))


def test_load_memorose_config_rejects_invalid_sync_mode(monkeypatch, tmp_path):
    monkeypatch.setenv("MEMOROSE_API_KEY", "test-key")
    (tmp_path / "memorose.json").write_text(json.dumps({"sync": {"mode": "bad-mode"}}))

    with pytest.raises(MemoroseConfigError, match="sync.mode"):
        load_memorose_config(str(tmp_path))
