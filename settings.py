"""Tiny JSON-backed settings store. Failures are silently ignored (best effort)."""
from __future__ import annotations

import json
from typing import Any

from paths import user_config_dir

_FILE = user_config_dir() / "settings.json"
_cache: dict[str, Any] | None = None


def _load() -> dict[str, Any]:
    global _cache
    if _cache is None:
        try:
            _cache = json.loads(_FILE.read_text(encoding="utf-8"))
            if not isinstance(_cache, dict):
                _cache = {}
        except (OSError, ValueError):
            _cache = {}
    return _cache


def get(key: str, default: Any = None) -> Any:
    return _load().get(key, default)


def put(key: str, value: Any) -> None:
    data = _load()
    data[key] = value
    try:
        _FILE.parent.mkdir(parents=True, exist_ok=True)
        _FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except OSError:
        pass
