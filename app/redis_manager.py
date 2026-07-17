import json
import os
from typing import Optional, List
from app.watermark import Watermark

REDIS_KEY = "oct_watermarker"
CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.toml")


def _read_config() -> Optional[dict]:
    """Read Redis connection info from config.toml. Returns None if missing."""
    if not os.path.isfile(CONFIG_FILE):
        return None
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
        conf = {}
        for line in lines:
            line = line.strip()
            if line.startswith("#") or not line:
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                conf[k.strip()] = v.strip().strip("\"'")
        if "redis_host" not in conf:
            return None
        return conf
    except Exception:
        return None


def _write_config(host: str, port: int, password: str) -> bool:
    """Write Redis connection info to config.toml."""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            f.write("# Redis \u8fde\u63a5\u914d\u7f6e\n")
            f.write(f'redis_host = "{host}"\n')
            f.write(f'redis_port = {port}\n')
            f.write(f'redis_password = "{password}"\n')
        return True
    except Exception:
        return False


def _get_connection() -> Optional[object]:
    """Try to connect to Redis using config. Returns None if unavailable."""
    conf = _read_config()
    if conf is None:
        return None
    try:
        import redis
        r = redis.Redis(
            host=conf.get("redis_host", "127.0.0.1"),
            port=int(conf.get("redis_port", 6379)),
            password=conf.get("redis_password", ""),
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=3,
        )
        r.ping()
        return r
    except Exception:
        return None


def is_redis_available() -> bool:
    return _get_connection() is not None


def load_favorites() -> List[Watermark]:
    """Load favorited watermarks from Redis. Returns empty list on failure."""
    conn = _get_connection()
    if conn is None:
        return []
    try:
        raw_list = conn.lrange(REDIS_KEY, 0, -1)
        result = []
        for item in raw_list:
            try:
                data = json.loads(item)
                wm = Watermark.from_dict(data)
                result.append(wm)
            except Exception:
                continue
        return result
    except Exception:
        return []


def save_favorite(wm: Watermark) -> bool:
    """Save a single watermark to the Redis list (append if not exists)."""
    conn = _get_connection()
    if conn is None:
        return False
    try:
        serialized = json.dumps(wm.to_dict(), ensure_ascii=False)
        # Remove existing entry with same id first, then push
        conn.lrem(REDIS_KEY, 0, serialized)
        conn.rpush(REDIS_KEY, serialized)
        return True
    except Exception:
        return False


def remove_favorite(wm: Watermark) -> bool:
    """Remove a watermark from the Redis list by matching its full dict."""
    conn = _get_connection()
    if conn is None:
        return False
    try:
        serialized = json.dumps(wm.to_dict(), ensure_ascii=False)
        conn.lrem(REDIS_KEY, 0, serialized)
        return True
    except Exception:
        return False


def is_favorited(wm: Watermark) -> bool:
    """Check if a watermark is already in the Redis favorites list."""
    conn = _get_connection()
    if conn is None:
        return False
    try:
        serialized = json.dumps(wm.to_dict(), ensure_ascii=False)
        for item in conn.lrange(REDIS_KEY, 0, -1):
            if item == serialized:
                return True
        return False
    except Exception:
        return False
