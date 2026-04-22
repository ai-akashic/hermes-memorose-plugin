import json
from pathlib import Path

import pytest
import yaml

from plugins.memory import _load_provider_from_dir

from formatters import format_prefetch_context, format_status_payload
from provider import MemoroseMemoryProvider


class StubService:
    def __init__(self):
        self.search_queries = []
        self.stored = []
        self.deleted = []
        self.status_calls = 0
        self.task_calls = 0

    def search_memories(self, query):
        self.search_queries.append(query)
        return [{"memory_id": "m1", "content": "Rust preference", "score": 0.9}]

    def store_text(self, content):
        self.stored.append(content)
        return {"status": "accepted", "event_id": "evt-1"}

    def delete_memory(self, memory_id):
        self.deleted.append(memory_id)
        return {"deleted": True, "memory_id": memory_id}

    def get_status(self):
        self.status_calls += 1
        return {"pending": 0, "ready": True}

    def get_tasks(self):
        self.task_calls += 1
        return {"trees": [], "ready": []}


def test_plugin_metadata_files_exist():
    root = Path(__file__).resolve().parents[1]
    assert (root / "plugin.yaml").exists()
    assert (root / "requirements.txt").exists()
    assert (root / "README.md").exists()
    assert (root / "after-install.md").exists()
    assert (root / ".gitignore").exists()
    assert (root / "LICENSE").exists()


def test_plugin_manifest_exposes_install_metadata():
    root = Path(__file__).resolve().parents[1]
    manifest = yaml.safe_load((root / "plugin.yaml").read_text(encoding="utf-8"))
    assert manifest["manifest_version"] == 1
    assert manifest["name"] == "memorose"
    assert manifest["pip_dependencies"] == ["memorose>=0.1.1"]
    assert manifest["requires_env"][0]["name"] == "MEMOROSE_API_KEY"


def test_format_prefetch_context_uses_compact_bullets():
    text = format_prefetch_context(
        [
            {
                "memory_id": "m1",
                "score": 0.91,
                "content": "User prefers Rust over Python.",
            }
        ]
    )
    assert "<memorose-context>" in text
    assert "Rust over Python" in text
    assert "m1" not in text


def test_format_status_payload_returns_jsonable_dict():
    payload = format_status_payload(
        base_url="http://127.0.0.1:3000",
        user_id="u1",
        stream_id="s1",
        pending={"pending": 0, "ready": True},
    )
    assert payload["base_url"] == "http://127.0.0.1:3000"
    assert payload["user_id"] == "u1"
    assert payload["stream_id"] == "s1"
    assert payload["pending"]["ready"] is True


def test_initialize_requires_runtime_user_id(monkeypatch, tmp_path):
    monkeypatch.setenv("MEMOROSE_API_KEY", "key")
    provider = MemoroseMemoryProvider()
    provider.save_config({"base_url": "http://127.0.0.1:3000"}, str(tmp_path))

    with pytest.raises(RuntimeError, match="user_id"):
        provider.initialize("sess-1", hermes_home=str(tmp_path), platform="telegram")


def test_initialize_binds_stream_id_to_session_id(monkeypatch, tmp_path):
    monkeypatch.setenv("MEMOROSE_API_KEY", "key")
    provider = MemoroseMemoryProvider(service_factory=lambda *args, **kwargs: StubService())
    provider.save_config({"base_url": "http://127.0.0.1:3000"}, str(tmp_path))

    provider.initialize(
        "sess-1",
        hermes_home=str(tmp_path),
        platform="telegram",
        user_id="user-1",
    )

    assert provider._stream_id == "sess-1"
    assert provider._user_id == "user-1"


def test_prefetch_returns_formatted_context(monkeypatch, tmp_path):
    monkeypatch.setenv("MEMOROSE_API_KEY", "key")
    provider = MemoroseMemoryProvider(service_factory=lambda *args, **kwargs: StubService())
    provider.save_config({"base_url": "http://127.0.0.1:3000"}, str(tmp_path))
    provider.initialize("sess-1", hermes_home=str(tmp_path), platform="telegram", user_id="user-1")

    context = provider.prefetch("rust")
    assert "<memorose-context>" in context
    assert "Rust preference" in context


def test_handle_tool_call_routes_supported_tools(monkeypatch, tmp_path):
    monkeypatch.setenv("MEMOROSE_API_KEY", "key")
    provider = MemoroseMemoryProvider(service_factory=lambda *args, **kwargs: StubService())
    provider.save_config({"base_url": "http://127.0.0.1:3000"}, str(tmp_path))
    provider.initialize("sess-1", hermes_home=str(tmp_path), platform="telegram", user_id="user-1")

    search_payload = json.loads(provider.handle_tool_call("memorose_search", {"query": "rust"}))
    store_payload = json.loads(provider.handle_tool_call("memorose_store", {"content": "remember"}))
    status_payload = json.loads(provider.handle_tool_call("memorose_status", {}))

    assert search_payload["results"][0]["memory_id"] == "m1"
    assert store_payload["status"] == "accepted"
    assert status_payload["pending"]["ready"] is True


def test_sync_turn_skips_assistant_when_user_only(monkeypatch, tmp_path):
    monkeypatch.setenv("MEMOROSE_API_KEY", "key")
    stub = StubService()
    provider = MemoroseMemoryProvider(service_factory=lambda *args, **kwargs: stub)
    provider.save_config(
        {"base_url": "http://127.0.0.1:3000", "sync": {"mode": "user_only"}},
        str(tmp_path),
    )
    provider.initialize("sess-1", hermes_home=str(tmp_path), platform="telegram", user_id="user-1")

    provider.sync_turn("user msg", "assistant msg")

    assert stub.stored == ["user msg"]


def test_readme_mentions_required_user_id_and_session_mapping():
    readme = Path("README.md").read_text(encoding="utf-8")
    assert "user_id" in readme
    assert "session_id" in readme
    assert "MEMOROSE_API_KEY" in readme


def test_plugin_loads_via_hermes_provider_loader():
    root = Path(__file__).resolve().parents[1]
    provider = _load_provider_from_dir(root)
    assert provider is not None
    assert provider.name == "memorose"
