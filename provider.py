from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from agent.memory_provider import MemoryProvider

try:
    from .config import load_memorose_config
    from .formatters import format_prefetch_context, format_status_payload
    from .service import MemoroseService
except ImportError:
    from config import load_memorose_config
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
        self._sync_mode = "user_only"

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
        self._sync_mode = cfg.sync_mode
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
        if user_content.strip():
            self._service.store_text(user_content)
        if self._sync_mode == "user_and_assistant" and assistant_content.strip():
            self._service.store_text(assistant_content)

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


__all__ = [
    "DELETE_TOOL",
    "MemoroseMemoryProvider",
    "SEARCH_TOOL",
    "STATUS_TOOL",
    "STORE_TOOL",
    "TASKS_TOOL",
    "register",
]
