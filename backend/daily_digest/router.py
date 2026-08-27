"""每日热点总结 API

端点：
- POST /api/daily-digest/generate    — 生成今日热点总结（自动存 MongoDB + 导出 Obsidian）
- GET  /api/daily-digest/today       — 获取今日热点总结（未生成则自动生成）
- GET  /api/daily-digest/{date}      — 获取指定日期的热点总结
- GET  /api/daily-digest/list        — 获取历史热点总结列表
- GET  /api/daily-digest/obsidian/{date} — 获取 Obsidian Markdown 内容
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse

from daily_digest.agent import generate_daily_digest
from daily_digest.obsidian_export import OBSIDIAN_VAULT, DIGEST_FOLDER

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/daily-digest", tags=["每日热点总结"])


def _get_db():
    """延迟获取 MongoDB 数据库实例"""
    from memory import db
    if db is None:
        raise RuntimeError("MongoDB 未初始化")
    return db


@router.post("/generate")
async def generate_digest(body: dict | None = None):
    """生成今日热点总结

    请求体（可选）：
    - llm_provider: 已废弃，统一使用用户配置的模型
    - focus_topic: 关注领域（如 "美妆"、"科技"）
    - track: 赛道筛选（如 "美妆"、"科技"、"游戏"），只分析该赛道热点
    """
    body = body or {}
    llm_provider = body.get("llm_provider")  # None = 使用统一模型配置
    focus_topic = body.get("focus_topic", "")
    track = body.get("track", "")

    try:
        database = _get_db()
        result = await generate_daily_digest(
            llm_provider=llm_provider,
            focus_topic=focus_topic,
            track=track,
            db=database,
        )
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"[每日热点] 生成失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"生成失败: {str(e)}")


@router.get("/today")
async def get_today_digest():
    """获取今日热点总结（如未生成则自动生成）"""
    today = datetime.now().strftime("%Y-%m-%d")

    try:
        database = _get_db()
        coll = database["daily_digests"]
        doc = await coll.find_one({"date": today})
        if doc:
            doc.pop("_id", None)
            return {"success": True, "data": doc, "cached": True}
    except Exception as e:
        logger.warning(f"[每日热点] MongoDB 查询失败: {e}")

    # 今日未生成，自动触发生成
    try:
        database = _get_db()
        result = await generate_daily_digest(db=database)
        return {"success": True, "data": result, "cached": False}
    except Exception as e:
        logger.error(f"[每日热点] 自动生成失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"生成失败: {str(e)}")


@router.get("/list")
async def list_digests(days: int = 30):
    """获取历史热点总结列表

    参数：
    - days: 查询最近多少天（默认 30）
    """
    try:
        database = _get_db()
        coll = database["daily_digests"]
        cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        cursor = coll.find(
            {"date": {"$gte": cutoff}},
            {"date": 1, "total_hot_items": 1, "platform_stats": 1, "overview": 1, "focus_topic": 1, "generated_at": 1},
        ).sort("date", -1)

        items = []
        async for doc in cursor:
            doc.pop("_id", None)
            items.append(doc)

        return {"success": True, "items": items, "total": len(items)}
    except Exception as e:
        logger.error(f"[每日热点] 查询列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/obsidian/{date}")
async def get_obsidian_content(date: str):
    """获取指定日期的 Obsidian Markdown 内容"""
    filepath = os.path.join(OBSIDIAN_VAULT, DIGEST_FOLDER, f"{date} 每日热点.md")
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail=f"Obsidian 文件不存在: {date}")
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    return PlainTextResponse(content, media_type="text/plain; charset=utf-8")


@router.get("/{date}")
async def get_digest_by_date(date: str):
    """获取指定日期的热点总结

    路径参数：
    - date: 日期，格式 YYYY-MM-DD
    """
    try:
        database = _get_db()
        coll = database["daily_digests"]
        doc = await coll.find_one({"date": date})
        if not doc:
            raise HTTPException(status_code=404, detail=f"{date} 的热点总结不存在")
        doc.pop("_id", None)
        return {"success": True, "data": doc}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[每日热点] 查询失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
