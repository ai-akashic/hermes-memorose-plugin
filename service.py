from __future__ import annotations

from typing import Any

try:
    from .config import MemoroseConfig
except ImportError:
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
        if client is not None:
            self._client = client
        else:
            from memorose import MemoroseClient

            self._client = MemoroseClient(config.base_url, config.api_key, timeout=30)

    def search_memories(self, query: str) -> list[dict[str, Any]]:
        from memorose.types import RetrieveRequest

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
        from memorose.types import IngestRequest

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
