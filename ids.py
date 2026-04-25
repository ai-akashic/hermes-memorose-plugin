from __future__ import annotations

import uuid


def ensure_memorose_uuid(raw_id: str, *, kind: str = "user") -> str:
    """Convert external platform ids into deterministic UUIDs for Memorose."""
    if not raw_id:
        return ""
    try:
        parsed = uuid.UUID(str(raw_id))
        return str(parsed)
    except ValueError:
        return str(uuid.uuid5(uuid.NAMESPACE_URL, f"memorose://{kind}/{raw_id}"))
