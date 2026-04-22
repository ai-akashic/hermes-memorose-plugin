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
