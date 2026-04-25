import uuid

from ids import ensure_memorose_uuid


def test_ensure_memorose_uuid_preserves_existing_uuid_strings():
    value = "8862fd89-8b31-4d8f-930a-9d3b6be4d5fd"
    assert ensure_memorose_uuid(value) == value


def test_ensure_memorose_uuid_uses_role_specific_namespace():
    raw_id = "o9cq1234567890@im.wechat"
    assert ensure_memorose_uuid(raw_id, kind="user") == str(
        uuid.uuid5(uuid.NAMESPACE_URL, f"memorose://user/{raw_id}")
    )
    assert ensure_memorose_uuid(raw_id, kind="stream") == str(
        uuid.uuid5(uuid.NAMESPACE_URL, f"memorose://stream/{raw_id}")
    )
