"""Job: GODMODE Backend. Purpose: Optional Redis job enqueue with safe no-op fallback."""
import os
import json
import logging

log = logging.getLogger("godmode.queue")
_client = None


def _redis():
    global _client
    url = os.getenv("REDIS_URL")
    if not url:
        return None
    if _client is None:
        import redis
        _client = redis.Redis.from_url(url, socket_connect_timeout=0.5)
    return _client


def enqueue(kind: str, payload: dict) -> bool:
    try:
        client = _redis()
        if client is None:
            return False
        client.rpush("gm:queue:tasks", json.dumps({"kind": kind, **payload}))
        return True
    except Exception as exc:
        log.warning("redis enqueue failed: %s", exc)
        return False


def ping_redis() -> bool:
    try:
        client = _redis()
        if client is None:
            return False
        return bool(client.ping())
    except Exception:
        return False
