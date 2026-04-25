import uuid
from types import SimpleNamespace

from config import MemoroseConfig
from ids import ensure_memorose_uuid
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

    def get_ready_tasks(self, user_id):
        self.calls.append(("ready_tasks", user_id))
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
    assert service._client.calls[0][1:3] == (
        str(uuid.uuid5(uuid.NAMESPACE_URL, "memorose://user/user-1")),
        str(uuid.uuid5(uuid.NAMESPACE_URL, "memorose://stream/session-1")),
    )


def test_store_text_ingests_current_stream():
    service = make_service()
    result = service.store_text("remember this")
    assert result["status"] == "accepted"
    assert result["event_id"] == "evt-1"
    assert service._client.calls[0][0] == "ingest"


def test_non_uuid_ids_are_deterministically_normalized_before_sdk_calls():
    raw_user_id = "o9cq1234567890@im.wechat"
    raw_stream_id = "chat-room-42@im.wechat"
    cfg = MemoroseConfig(
        base_url="http://127.0.0.1:3000",
        api_key="key",
        org_id="org-1",
        retrieve_limit=8,
        retrieve_min_score=0.2,
        retrieve_graph_depth=1,
        sync_mode="user_only",
    )
    service = MemoroseService(cfg, raw_user_id, raw_stream_id, client=FakeClient())

    service.store_text("remember this")

    call = service._client.calls[0]
    assert call[0] == "ingest"
    assert call[1] == str(uuid.uuid5(uuid.NAMESPACE_URL, f"memorose://user/{raw_user_id}"))
    assert call[2] == str(uuid.uuid5(uuid.NAMESPACE_URL, f"memorose://stream/{raw_stream_id}"))


def test_ensure_uuid_preserves_existing_uuid_strings():
    value = "8862fd89-8b31-4d8f-930a-9d3b6be4d5fd"
    assert ensure_memorose_uuid(value) == value


def test_delete_memory_uses_runtime_user():
    service = make_service()
    result = service.delete_memory("m1")
    assert result["deleted"] is True
    assert service._client.calls[0] == (
        "delete",
        str(uuid.uuid5(uuid.NAMESPACE_URL, "memorose://user/user-1")),
        "m1",
    )


def test_get_status_returns_pending_payload():
    service = make_service()
    payload = service.get_status()
    assert payload["ready"] is True


def test_get_tasks_returns_tree_and_ready_lists():
    service = make_service()
    payload = service.get_tasks()
    assert payload == {"trees": [], "ready": []}
    assert service._client.calls[0] == (
        "tasks",
        str(uuid.uuid5(uuid.NAMESPACE_URL, "memorose://user/user-1")),
    )
    assert service._client.calls[1] == (
        "ready_tasks",
        str(uuid.uuid5(uuid.NAMESPACE_URL, "memorose://user/user-1")),
    )
