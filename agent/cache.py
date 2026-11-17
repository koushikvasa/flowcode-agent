"""Tiny disk cache: one JSON file per key, so reruns skip paid API calls.

Layout: .cache/<namespace>/<sha256 of key>.json
Each file holds {"key": ..., "saved_at": ..., "value": ...}; the key is kept
so a person can open the file and see what it is.
"""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agent.config import CACHE_DIR


def _path(namespace: str, key: str) -> Path:
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
    return CACHE_DIR / namespace / f"{digest}.json"


def get(namespace: str, key: str) -> Any | None:
    """Return the cached value, or None if we have never saved this key."""
    path = _path(namespace, key)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))["value"]


def put(namespace: str, key: str, value: Any) -> None:
    """Save a JSON-serializable value. Write to a temp file, then swap it in."""
    path = _path(namespace, key)
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {"key": key, "saved_at": datetime.now(timezone.utc).isoformat(), "value": value}
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)  # atomic on the same disk: no half-written cache files
