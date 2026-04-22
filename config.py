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
