"""记忆层 — MongoDB 持久存储 + Redis 缓存"""

from __future__ import annotations

import logging
import os

import motor.motor_asyncio
import redis.asyncio as aioredis

logger = logging.getLogger(__name__)

# ── MongoDB ───────────────────────────────────────────────

_mongo_client: motor.motor_asyncio.AsyncIOMotorClient | None = None
db: motor.motor_asyncio.AsyncIOMotorDatabase | None = None


async def init_mongo(uri: str | None = None, db_name: str | None = None):
    """初始化 MongoDB 连接"""
    global _mongo_client, db
    uri = uri or os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    db_name = db_name or os.getenv("MONGODB_DB", "echoflow")
    _mongo_client = motor.motor_asyncio.AsyncIOMotorClient(uri)
    db = _mongo_client[db_name]
    # 验证连接
    await _mongo_client.admin.command("ping")
    logger.info(f"MongoDB 已连接: {db_name}")


async def close_mongo():
    """关闭 MongoDB 连接"""
    global _mongo_client, db
    if _mongo_client:
        _mongo_client.close()
        _mongo_client = None
        db = None
        logger.info("MongoDB 已断开")


# ── Redis ─────────────────────────────────────────────────

redis_client: aioredis.Redis | None = None


async def init_redis(url: str | None = None):
    """初始化 Redis 连接"""
    global redis_client
    url = url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
    redis_client = aioredis.from_url(url, decode_responses=True)
    # 验证连接
    await redis_client.ping()
    logger.info(f"Redis 已连接: {url}")


async def close_redis():
    """关闭 Redis 连接"""
    global redis_client
    if redis_client:
        await redis_client.aclose()
        redis_client = None
        logger.info("Redis 已断开")
