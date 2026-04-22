# Hermes Memorose Plugin Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a standalone Hermes memory provider plugin named `memorose` that reuses the Python Memorose SDK, requires Hermes runtime `user_id`, and maps Hermes `session_id` directly to Memorose `stream_id`.

**Architecture:** The plugin uses a Provider + Service split. `__init__.py` implements the Hermes `MemoryProvider` surface and delegates all Memorose SDK interaction to `service.py`, while `config.py` owns config/env resolution and `formatters.py` keeps prompt/tool output small and deterministic.

**Tech Stack:** Python 3, Hermes `MemoryProvider` plugin API, `memorose` Python SDK, standard library JSON/threading/path handling, pytest.

---

## File Structure

### Files to create

- `README.md`
- `requirements.txt`
- `plugin.yaml`
- `__init__.py`
- `service.py`
- `config.py`
- `formatters.py`
- `cli.py`
- `tests/test_config.py`
- `tests/test_service.py`
- `tests/test_provider.py`
- `tests/test_cli.py`

### File responsibilities

- `README.md`
  - install/setup/use documentation for Hermes users
- `requirements.txt`
  - runtime and test dependencies for the plugin project
- `plugin.yaml`
  - Hermes plugin metadata and dependency declaration
- `config.py`
  - load `memorose.json`, require `MEMOROSE_API_KEY`, validate runtime config
- `service.py`
  - adapt the `memorose` SDK into provider-friendly methods
- `formatters.py`
  - render compact prefetch context and JSON tool results
- `__init__.py`
  - implement `MemoryProvider`, define tool schemas, register the provider
- `cli.py`
  - expose `hermes memorose status`
- `tests/test_config.py`
  - validate config resolution, especially `user_id` hard requirements
- `tests/test_service.py`
  - validate SDK adapter request construction and error behavior
- `tests/test_provider.py`
  - validate provider lifecycle, tools, sync, and prefetch behavior
- `tests/test_cli.py`
  - validate CLI registration and status command output

## Task 1: Create project metadata and dependency skeleton

**Files:**
- Create: `README.md`
- Create: `requirements.txt`
- Create: `plugin.yaml`

- [ ] **Step 1: Write the failing metadata test**

```python
# tests/test_provider.py
from pathlib import Path


def test_plugin_metadata_files_exist():
    root = Path(__file__).resolve().parents[1]
    assert (root / "plugin.yaml").exists()
    assert (root / "requirements.txt").exists()
    assert (root / "README.md").exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/dylan/future/akashic/hermes-memorose-plugin && pytest tests/test_provider.py::test_plugin_metadata_files_exist -v`
Expected: FAIL with missing file assertions.

- [ ] **Step 3: Write minimal metadata files**

```yaml
# plugin.yaml
name: memorose
version: 1.0.0
description: "Memorose memory provider for Hermes Agent using the Python Memorose SDK."
pip_dependencies:
  - memorose
hooks:
  - on_session_end
```

```text
# requirements.txt
memorose
pytest
```

```markdown
# Hermes Memorose Plugin

Hermes memory provider plugin backed by Memorose.

## Status

Work in progress.
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/dylan/future/akashic/hermes-memorose-plugin && pytest tests/test_provider.py::test_plugin_metadata_files_exist -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd /Users/dylan/future/akashic/hermes-memorose-plugin
git add README.md requirements.txt plugin.yaml tests/test_provider.py
git commit -m "chore: add plugin metadata skeleton"
```

## Task 2: Implement config loading and validation

**Files:**
- Create: `config.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: Write the failing config tests**

```python
import json
from pathlib import Path

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
    (tmp_path / "memorose.json").write_text(
        json.dumps({"sync": {"mode": "bad-mode"}})
    )

    with pytest.raises(MemoroseConfigError, match="sync.mode"):
        load_memorose_config(str(tmp_path))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/dylan/future/akashic/hermes-memorose-plugin && pytest tests/test_config.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'config'`.

- [ ] **Step 3: Write minimal config implementation**

```python
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class MemoroseConfigError(RuntimeError):
    pass


@dataclass(frozen=True)
class MemoroseConfig:
    base_url: str
    api_key: str
    org_id: str | None
    retrieve_limit: int
    retrieve_min_score: float
    retrieve_graph_depth: int
    sync_mode: str


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def load_memorose_config(hermes_home: str) -> MemoroseConfig:
    config_path = Path(hermes_home) / "memorose.json"
    raw: dict[str, Any] = {}
    if config_path.exists():
        raw = json.loads(config_path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise MemoroseConfigError("memorose.json must contain an object")

    api_key = os.environ.get("MEMOROSE_API_KEY", "").strip()
    if not api_key:
        raise MemoroseConfigError("MEMOROSE_API_KEY is required")

    retrieve = _as_dict(raw.get("retrieve"))
    sync = _as_dict(raw.get("sync"))
    sync_mode = str(sync.get("mode", "user_only")).strip() or "user_only"
    if sync_mode not in {"user_only", "user_and_assistant"}:
        raise MemoroseConfigError("sync.mode must be user_only or user_and_assistant")

    return MemoroseConfig(
        base_url=str(raw.get("base_url", "http://127.0.0.1:3000")).rstrip("/"),
        api_key=api_key,
        org_id=str(raw["org_id"]).strip() if raw.get("org_id") else None,
        retrieve_limit=int(retrieve.get("limit", 8)),
        retrieve_min_score=float(retrieve.get("min_score", 0.0)),
        retrieve_graph_depth=int(retrieve.get("graph_depth", 1)),
        sync_mode=sync_mode,
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/dylan/future/akashic/hermes-memorose-plugin && pytest tests/test_config.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd /Users/dylan/future/akashic/hermes-memorose-plugin
git add config.py tests/test_config.py
git commit -m "feat: add memorose config loader"
```

## Task 3: Implement formatter helpers

**Files:**
- Create: `formatters.py`
- Modify: `tests/test_provider.py`

- [ ] **Step 1: Write the failing formatter tests**

```python
from formatters import format_prefetch_context, format_status_payload


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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/dylan/future/akashic/hermes-memorose-plugin && pytest tests/test_provider.py::test_format_prefetch_context_uses_compact_bullets tests/test_provider.py::test_format_status_payload_returns_jsonable_dict -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'formatters'`.

- [ ] **Step 3: Write minimal formatter implementation**

```python
from __future__ import annotations

from typing import Any


def format_prefetch_context(results: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for item in results:
        content = str(item.get("content", "")).strip()
        if content:
            lines.append(f"- {content}")
    if not lines:
        return ""
    return "<memorose-context>\n" + "\n".join(lines) + "\n</memorose-context>"


def format_status_payload(
    *,
    base_url: str,
    user_id: str,
    stream_id: str,
    pending: dict[str, Any],
) -> dict[str, Any]:
    return {
        "base_url": base_url,
        "user_id": user_id,
        "stream_id": stream_id,
        "pending": pending,
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/dylan/future/akashic/hermes-memorose-plugin && pytest tests/test_provider.py::test_format_prefetch_context_uses_compact_bullets tests/test_provider.py::test_format_status_payload_returns_jsonable_dict -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd /Users/dylan/future/akashic/hermes-memorose-plugin
git add formatters.py tests/test_provider.py
git commit -m "feat: add memorose formatter helpers"
```

## Task 4: Implement the Memorose service adapter

**Files:**
- Create: `service.py`
- Create: `tests/test_service.py`

- [ ] **Step 1: Write the failing service tests**

```python
from types import SimpleNamespace

from config import MemoroseConfig
from service import MemoroseService


class FakeClient:
    def __init__(self):
        self.calls = []

    def retrieve_memory(self, user_id, stream_id, request):
        self.calls.append(("retrieve", user_id, stream_id, request))
        return SimpleNamespace(
            results=[
                {
                    "unit": {
                        "id": "m1",
                        "content": "User prefers Rust over Python.",
                    },
                    "score": 0.91,
                }
            ],
            query_time_ms=12,
        )

    def ingest_event(self, user_id, stream_id, request):
        self.calls.append(("ingest", user_id, stream_id, request))
        return SimpleNamespace(status="accepted", event_id="evt-1")

    def delete_memory(self, user_id, memory_id):
        self.calls.append(("delete", user_id, memory_id))
        return True

    def get_pending_count(self):
        self.calls.append(("pending",))
        return {"pending": 0, "ready": True}

    def get_all_task_trees(self, user_id):
        self.calls.append(("tasks", user_id))
        return []


def make_service():
    cfg = MemoroseConfig(
        base_url="http://127.0.0.1:3000",
        api_key="key",
        org_id="org-1",
        retrieve_limit=8,
        retrieve_min_score=0.2,
        retrieve_graph_depth=1,
        sync_mode="user_only",
    )
    return MemoroseService(cfg, "user-1", "session-1", client=FakeClient())


def test_search_memories_uses_runtime_user_and_stream():
    service = make_service()
    results = service.search_memories("rust")
    assert results[0]["memory_id"] == "m1"
    assert results[0]["content"] == "User prefers Rust over Python."
    assert service._client.calls[0][0] == "retrieve"
    assert service._client.calls[0][1:3] == ("user-1", "session-1")


def test_store_text_ingests_current_stream():
    service = make_service()
    result = service.store_text("remember this")
    assert result["status"] == "accepted"
    assert result["event_id"] == "evt-1"
    assert service._client.calls[0][0] == "ingest"


def test_delete_memory_uses_runtime_user():
    service = make_service()
    result = service.delete_memory("m1")
    assert result["deleted"] is True
    assert service._client.calls[0] == ("delete", "user-1", "m1")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/dylan/future/akashic/hermes-memorose-plugin && pytest tests/test_service.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'service'`.

- [ ] **Step 3: Write minimal service implementation**

```python
from __future__ import annotations

from typing import Any

from memorose import MemoroseClient
from memorose.types import IngestRequest, RetrieveRequest

from config import MemoroseConfig


class MemoroseService:
    def __init__(
        self,
        config: MemoroseConfig,
        user_id: str,
        stream_id: str,
        *,
        client: Any | None = None,
    ) -> None:
        self._config = config
        self._user_id = user_id
        self._stream_id = stream_id
        self._client = client or MemoroseClient(config.base_url, config.api_key, timeout=30)

    def search_memories(self, query: str) -> list[dict[str, Any]]:
        response = self._client.retrieve_memory(
            self._user_id,
            self._stream_id,
            RetrieveRequest(
                query=query,
                limit=self._config.retrieve_limit,
                min_score=self._config.retrieve_min_score,
                graph_depth=self._config.retrieve_graph_depth,
                org_id=self._config.org_id,
            ),
        )
        results: list[dict[str, Any]] = []
        for item in list(response.results or []):
            unit = item.get("unit", {}) if isinstance(item, dict) else {}
            results.append(
                {
                    "memory_id": unit.get("id"),
                    "content": unit.get("content", ""),
                    "score": item.get("score", 0.0) if isinstance(item, dict) else 0.0,
                }
            )
        return results

    def store_text(self, content: str) -> dict[str, Any]:
        response = self._client.ingest_event(
            self._user_id,
            self._stream_id,
            IngestRequest(content=content, org_id=self._config.org_id),
        )
        return {"status": response.status, "event_id": response.event_id}

    def delete_memory(self, memory_id: str) -> dict[str, Any]:
        deleted = self._client.delete_memory(self._user_id, memory_id)
        return {"deleted": bool(deleted), "memory_id": memory_id}

    def get_status(self) -> dict[str, Any]:
        return self._client.get_pending_count()

    def get_tasks(self) -> dict[str, Any]:
        trees = self._client.get_all_task_trees(self._user_id)
        ready = self._client.get_ready_tasks(self._user_id)
        return {"trees": trees, "ready": ready}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/dylan/future/akashic/hermes-memorose-plugin && pytest tests/test_service.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd /Users/dylan/future/akashic/hermes-memorose-plugin
git add service.py tests/test_service.py
git commit -m "feat: add memorose sdk service adapter"
```

## Task 5: Implement the Hermes provider

**Files:**
- Create: `__init__.py`
- Modify: `tests/test_provider.py`

- [ ] **Step 1: Write the failing provider tests**

```python
import json

import pytest

from config import MemoroseConfig
from service import MemoroseService
from __init__ import MemoroseMemoryProvider


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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/dylan/future/akashic/hermes-memorose-plugin && pytest tests/test_provider.py::test_initialize_requires_runtime_user_id tests/test_provider.py::test_initialize_binds_stream_id_to_session_id tests/test_provider.py::test_prefetch_returns_formatted_context tests/test_provider.py::test_handle_tool_call_routes_supported_tools -v`
Expected: FAIL with `ModuleNotFoundError: No module named '__init__'` or missing implementation.

- [ ] **Step 3: Write minimal provider implementation**

```python
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from agent.memory_provider import MemoryProvider

from config import MemoroseConfigError, load_memorose_config
from formatters import format_prefetch_context, format_status_payload
from service import MemoroseService


SEARCH_TOOL = {
    "name": "memorose_search",
    "description": "Search long-term memory stored in Memorose.",
    "parameters": {
        "type": "object",
        "properties": {"query": {"type": "string"}},
        "required": ["query"],
    },
}

STORE_TOOL = {
    "name": "memorose_store",
    "description": "Store a new long-term memory in Memorose.",
    "parameters": {
        "type": "object",
        "properties": {"content": {"type": "string"}},
        "required": ["content"],
    },
}

DELETE_TOOL = {
    "name": "memorose_delete",
    "description": "Delete a memory from Memorose by id.",
    "parameters": {
        "type": "object",
        "properties": {"memory_id": {"type": "string"}},
        "required": ["memory_id"],
    },
}

STATUS_TOOL = {
    "name": "memorose_status",
    "description": "Show current Memorose connectivity and routing status.",
    "parameters": {"type": "object", "properties": {}},
}

TASKS_TOOL = {
    "name": "memorose_tasks",
    "description": "Show user-level Memorose tasks.",
    "parameters": {"type": "object", "properties": {}},
}


class MemoroseMemoryProvider(MemoryProvider):
    def __init__(
        self,
        *,
        service_factory: Callable[..., MemoroseService] | None = None,
    ) -> None:
        self._service_factory = service_factory or MemoroseService
        self._service: MemoroseService | Any | None = None
        self._hermes_home = ""
        self._user_id = ""
        self._stream_id = ""
        self._base_url = ""

    @property
    def name(self) -> str:
        return "memorose"

    def is_available(self) -> bool:
        return True

    def initialize(self, session_id: str, **kwargs) -> None:
        user_id = str(kwargs.get("user_id", "")).strip()
        if not user_id:
            raise RuntimeError("Memorose provider requires Hermes runtime user_id")
        hermes_home = str(kwargs.get("hermes_home", "")).strip()
        cfg = load_memorose_config(hermes_home)
        self._hermes_home = hermes_home
        self._user_id = user_id
        self._stream_id = session_id
        self._base_url = cfg.base_url
        self._service = self._service_factory(cfg, user_id, session_id)

    def system_prompt_block(self) -> str:
        return (
            "Memorose long-term memory is available. "
            "Use memorose_search for explicit recall when prior facts or preferences matter."
        )

    def prefetch(self, query: str, *, session_id: str = "") -> str:
        if not self._service:
            return ""
        return format_prefetch_context(self._service.search_memories(query))

    def sync_turn(self, user_content: str, assistant_content: str, *, session_id: str = "") -> None:
        if not self._service:
            return
        self._service.store_text(user_content)

    def get_tool_schemas(self):
        return [SEARCH_TOOL, STORE_TOOL, DELETE_TOOL, STATUS_TOOL, TASKS_TOOL]

    def handle_tool_call(self, tool_name, args, **kwargs):
        if not self._service:
            return json.dumps({"error": "provider not initialized"})
        if tool_name == "memorose_search":
            return json.dumps({"results": self._service.search_memories(str(args.get("query", "")))})
        if tool_name == "memorose_store":
            return json.dumps(self._service.store_text(str(args.get("content", ""))))
        if tool_name == "memorose_delete":
            return json.dumps(self._service.delete_memory(str(args.get("memory_id", ""))))
        if tool_name == "memorose_status":
            return json.dumps(
                format_status_payload(
                    base_url=self._base_url,
                    user_id=self._user_id,
                    stream_id=self._stream_id,
                    pending=self._service.get_status(),
                )
            )
        if tool_name == "memorose_tasks":
            return json.dumps(self._service.get_tasks())
        return json.dumps({"error": f"unknown tool: {tool_name}"})

    def get_config_schema(self):
        return [
            {
                "key": "api_key",
                "description": "Memorose API key",
                "secret": True,
                "required": True,
                "env_var": "MEMOROSE_API_KEY",
            },
            {
                "key": "base_url",
                "description": "Memorose server base URL",
                "default": "http://127.0.0.1:3000",
            },
        ]

    def save_config(self, values, hermes_home):
        path = Path(hermes_home) / "memorose.json"
        path.write_text(json.dumps(values, indent=2) + "\n", encoding="utf-8")


def register(ctx) -> None:
    ctx.register_memory_provider(MemoroseMemoryProvider())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/dylan/future/akashic/hermes-memorose-plugin && pytest tests/test_provider.py::test_initialize_requires_runtime_user_id tests/test_provider.py::test_initialize_binds_stream_id_to_session_id tests/test_provider.py::test_prefetch_returns_formatted_context tests/test_provider.py::test_handle_tool_call_routes_supported_tools -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd /Users/dylan/future/akashic/hermes-memorose-plugin
git add __init__.py tests/test_provider.py
git commit -m "feat: add hermes memorose memory provider"
```

## Task 6: Respect sync mode and add tasks/status service tests

**Files:**
- Modify: `service.py`
- Modify: `__init__.py`
- Modify: `tests/test_service.py`
- Modify: `tests/test_provider.py`

- [ ] **Step 1: Write the failing sync-mode and status/task tests**

```python
def test_get_status_returns_pending_payload():
    service = make_service()
    payload = service.get_status()
    assert payload["ready"] is True


def test_get_tasks_returns_tree_and_ready_lists():
    service = make_service()
    payload = service.get_tasks()
    assert payload == {"trees": [], "ready": []}


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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/dylan/future/akashic/hermes-memorose-plugin && pytest tests/test_service.py::test_get_status_returns_pending_payload tests/test_service.py::test_get_tasks_returns_tree_and_ready_lists tests/test_provider.py::test_sync_turn_skips_assistant_when_user_only -v`
Expected: FAIL if provider/service behavior is incomplete or inconsistent.

- [ ] **Step 3: Update implementation to satisfy sync-mode expectations**

```python
# In __init__.py inside initialize():
self._sync_mode = cfg.sync_mode

# In __init__.py inside sync_turn():
if not self._service:
    return
if user_content.strip():
    self._service.store_text(user_content)
if self._sync_mode == "user_and_assistant" and assistant_content.strip():
    self._service.store_text(assistant_content)
```

```python
# In __init__.py __init__():
self._sync_mode = "user_only"
```

```python
# In service.py get_tasks():
trees = self._client.get_all_task_trees(self._user_id)
ready = self._client.get_ready_tasks(self._user_id)
return {"trees": trees, "ready": ready}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/dylan/future/akashic/hermes-memorose-plugin && pytest tests/test_service.py::test_get_status_returns_pending_payload tests/test_service.py::test_get_tasks_returns_tree_and_ready_lists tests/test_provider.py::test_sync_turn_skips_assistant_when_user_only -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd /Users/dylan/future/akashic/hermes-memorose-plugin
git add __init__.py service.py tests/test_service.py tests/test_provider.py
git commit -m "feat: respect sync mode and expose status tasks"
```

## Task 7: Implement provider CLI registration

**Files:**
- Create: `cli.py`
- Create: `tests/test_cli.py`

- [ ] **Step 1: Write the failing CLI tests**

```python
import argparse

from cli import register_cli


def test_register_cli_sets_memorose_subcommands():
    parser = argparse.ArgumentParser()
    register_cli(parser)
    assert parser.get_default("func") is not None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/dylan/future/akashic/hermes-memorose-plugin && pytest tests/test_cli.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'cli'`.

- [ ] **Step 3: Write minimal CLI implementation**

```python
from __future__ import annotations

import argparse
import json

from config import load_memorose_config
from service import MemoroseService


def memorose_command(args) -> None:
    if getattr(args, "memorose_command", None) != "status":
        print("Usage: hermes memorose status")
        return
    cfg = load_memorose_config(args.hermes_home)
    service = MemoroseService(cfg, args.user_id, args.session_id)
    print(json.dumps(service.get_status(), indent=2))


def register_cli(subparser) -> None:
    subs = subparser.add_subparsers(dest="memorose_command")
    status = subs.add_parser("status", help="Show Memorose status")
    status.add_argument("--hermes-home", required=True)
    status.add_argument("--user-id", required=True)
    status.add_argument("--session-id", required=True)
    subparser.set_defaults(func=memorose_command)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/dylan/future/akashic/hermes-memorose-plugin && pytest tests/test_cli.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd /Users/dylan/future/akashic/hermes-memorose-plugin
git add cli.py tests/test_cli.py
git commit -m "feat: add memorose provider cli"
```

## Task 8: Expand README with real install/setup/use instructions

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Write the failing README smoke test**

```python
from pathlib import Path


def test_readme_mentions_required_user_id_and_session_mapping():
    readme = Path("README.md").read_text(encoding="utf-8")
    assert "user_id" in readme
    assert "session_id" in readme
    assert "MEMOROSE_API_KEY" in readme
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/dylan/future/akashic/hermes-memorose-plugin && pytest tests/test_provider.py::test_readme_mentions_required_user_id_and_session_mapping -v`
Expected: FAIL because the placeholder README is too thin.

- [ ] **Step 3: Replace README with a usable first-version guide**

```markdown
# Hermes Memorose Plugin

Hermes memory provider plugin backed by Memorose.

## What it does

- requires Hermes runtime `user_id`
- maps Hermes `session_id` directly to Memorose `stream_id`
- uses the Python `memorose` SDK
- exposes `memorose_search`, `memorose_store`, `memorose_delete`, `memorose_status`, and `memorose_tasks`

## Install

Copy this directory into your Hermes user plugins directory as `memorose`.

## Configure

Set the secret in your Hermes `.env`:

```bash
MEMOROSE_API_KEY=your-key
```

Create `$HERMES_HOME/memorose.json`:

```json
{
  "base_url": "http://127.0.0.1:3000",
  "retrieve": {
    "limit": 8,
    "min_score": 0.0,
    "graph_depth": 1
  },
  "sync": {
    "mode": "user_only"
  }
}
```

## Runtime rules

- `user_id` must be supplied by Hermes runtime
- missing `user_id` is a hard error
- Hermes `session_id` becomes Memorose `stream_id`

## Development

```bash
pytest tests -v
```
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/dylan/future/akashic/hermes-memorose-plugin && pytest tests/test_provider.py::test_readme_mentions_required_user_id_and_session_mapping -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd /Users/dylan/future/akashic/hermes-memorose-plugin
git add README.md tests/test_provider.py
git commit -m "docs: expand plugin readme"
```

## Task 9: Run the full local test suite for the plugin project

**Files:**
- Modify: no source changes expected unless tests reveal gaps

- [ ] **Step 1: Run the full plugin test suite**

Run: `cd /Users/dylan/future/akashic/hermes-memorose-plugin && pytest tests -v`
Expected: PASS

- [ ] **Step 2: If failures occur, fix the smallest root cause**

```python
# Fix only the failing implementation or test assumptions.
# Do not widen scope beyond the plugin project.
```

- [ ] **Step 3: Re-run the full plugin test suite**

Run: `cd /Users/dylan/future/akashic/hermes-memorose-plugin && pytest tests -v`
Expected: PASS

- [ ] **Step 4: Commit the stabilized plugin project**

```bash
cd /Users/dylan/future/akashic/hermes-memorose-plugin
git add .
git commit -m "test: stabilize hermes memorose plugin"
```

## Self-Review

### Spec coverage

- standalone Python project: covered by Tasks 1 and 9
- Provider + Service split: covered by Tasks 2, 3, 4, and 5
- reuse `memorose-sdk/python`: covered by Task 4
- require runtime `user_id`: covered by Tasks 2 and 5
- `session_id -> stream_id`: covered by Tasks 4 and 5
- prompt recall and turn sync: covered by Tasks 3, 4, 5, and 6
- explicit tools: covered by Task 5
- optional CLI: covered by Task 7
- docs/setup: covered by Task 8

### Placeholder scan

- No `TODO`, `TBD`, or deferred “handle appropriately” language remains
- Every code step has explicit snippets
- Every verification step has an exact command

### Type consistency

- provider name is consistently `memorose`
- runtime identifiers are consistently `user_id` and `session_id`
- `stream_id` always maps from `session_id`
- sync mode values are consistently `user_only` and `user_and_assistant`
