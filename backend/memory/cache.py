"""Redis 缓存层 — 热点数据 TTL 缓存 (v1.2)

用法:
    from memory.cache import cache_get, cache_set

    # 读缓存，未命中返回 None
    data = await cache_get("trends:ai:7d")

    # 写缓存，默认 TTL 300 秒
    await cache_set("trends:ai:7d", data, ttl=600)
"""

from __future__ import annotations

import json
import logging
from typing import Any

from memory import redis_client

logger = logging.getLogger(__name__)

DEFAULT_TTL = 300  # 5 分钟


async def cache_get(key: str) -> Any | None:
    """从 Redis 读取缓存，未命中返回 None"""
    if redis_client is None:
        return None
    try:
        raw = await redis_client.get(key)
        if raw is None:
            return None
        return json.loads(raw)
    except Exception:
        logger.debug(f"Redis GET 失败: {key}")
        return None


async def cache_set(key: str, value: Any, ttl: int = DEFAULT_TTL):
    """写入 Redis 缓存，带 TTL"""
    if redis_client is None:
        return
    try:
        await redis_client.set(key, json.dumps(value, ensure_ascii=False), ex=ttl)
    except Exception:
        logger.debug(f"Redis SET 失败: {key}")


async def cache_delete(key: str):
    """删除缓存"""
    if redis_client is None:
        return
    try:
        await redis_client.delete(key)
    except Exception:
        logger.debug(f"Redis DEL 失败: {key}")


async def cache_delete_pattern(pattern: str):
    """按模式批量删除缓存"""
    if redis_client is None:
        return
    try:
        cursor = 0
        while True:
            cursor, keys = await redis_client.scan(cursor, match=pattern, count=100)
            if keys:
                await redis_client.delete(*keys)
            if cursor == 0:
                break
    except Exception:
        logger.debug(f"Redis DEL pattern 失败: {pattern}")
