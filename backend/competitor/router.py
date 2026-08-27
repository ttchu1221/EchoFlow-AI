# -*- coding: utf-8 -*-
"""竞品内容监控 — 跟踪竞品账号动态"""

import logging
import asyncio
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException

from auth.dependencies import get_current_user, require_permission

logger = logging.getLogger("echowflow.competitor")

router = APIRouter(prefix="/api/competitor", tags=["竞品监控"])


class CompetitorAccount(BaseModel):
    """竞品账号"""
    id: Optional[str] = None
    name: str = Field(..., max_length=100)
    platform: str
    account_id: str
    account_name: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    notes: Optional[str] = None


def _get_competitor_collection():
    from memory import db
    if db is None:
        raise RuntimeError("MongoDB 未初始化")
    return db["competitors"]


def _get_competitor_content_collection():
    from memory import db
    if db is None:
        raise RuntimeError("MongoDB 未初始化")
    return db["competitor_content"]


@router.post("/accounts", status_code=201)
async def add_competitor(
    body: CompetitorAccount,
    current_user: dict = Depends(require_permission("competitor:manage")),
):
    """添加竞品账号"""
    coll = _get_competitor_collection()

    existing = await coll.find_one({"platform": body.platform, "account_id": body.account_id})
    if existing:
        raise HTTPException(400, detail={"code": 400, "error": "该竞品账号已存在"})

    doc = body.model_dump()
    doc["created_at"] = datetime.utcnow()
    doc["updated_at"] = datetime.utcnow()
    doc["created_by"] = current_user["username"]
    doc["content_count"] = 0
    doc["last_checked_at"] = None

    result = await coll.insert_one(doc)
    doc["id"] = str(result.inserted_id)
    del doc["_id"]

    logger.info(f"竞品添加: {body.name} ({body.platform})")
    return {"code": 200, "data": doc}


@router.get("/accounts")
async def list_competitors(
    platform: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    """获取竞品列表"""
    coll = _get_competitor_collection()
    query = {}
    if platform:
        query["platform"] = platform

    items = []
    async for doc in coll.find(query).sort("created_at", -1):
        doc["id"] = str(doc.pop("_id"))
        items.append(doc)
    return {"code": 200, "data": items}


@router.delete("/accounts/{competitor_id}")
async def remove_competitor(
    competitor_id: str,
    current_user: dict = Depends(require_permission("competitor:manage")),
):
    """删除竞品"""
    coll = _get_competitor_collection()
    from bson import ObjectId
    result = await coll.delete_one({"_id": ObjectId(competitor_id)})
    if result.deleted_count == 0:
        raise HTTPException(404, detail={"code": 404, "error": "竞品不存在"})

    content_coll = _get_competitor_content_collection()
    await content_coll.delete_many({"competitor_id": competitor_id})

    return {"code": 200, "message": "竞品已删除"}


@router.get("/content/{competitor_id}")
async def list_competitor_content(
    competitor_id: str,
    page: int = 1,
    page_size: int = 20,
    sort_by: str = "fetched_at",
    current_user: dict = Depends(get_current_user),
):
    """获取竞品内容列表"""
    content_coll = _get_competitor_content_collection()
    total = await content_coll.count_documents({"competitor_id": competitor_id})
    skip = (page - 1) * page_size

    items = []
    async for doc in content_coll.find({"competitor_id": competitor_id}).sort(sort_by, -1).skip(skip).limit(page_size):
        doc["id"] = str(doc.pop("_id"))
        items.append(doc)

    return {
        "code": 200,
        "data": {"items": items, "total": total, "page": page, "page_size": page_size},
    }


@router.get("/insights")
async def competitor_insights(
    platform: Optional[str] = None,
    days: int = 7,
    current_user: dict = Depends(get_current_user),
):
    """竞品洞察分析"""
    content_coll = _get_competitor_content_collection()
    competitor_coll = _get_competitor_collection()

    cutoff = datetime.utcnow().replace(hour=0, minute=0, second=0) - __import__("datetime").timedelta(days=days)

    pipeline = [
        {"$match": {"fetched_at": {"$gte": cutoff}}},
        {"$group": {
            "_id": "$competitor_id",
            "total_content": {"$sum": 1},
            "avg_views": {"$avg": "$views"},
            "avg_likes": {"$avg": "$likes"},
            "top_content": {"$max": "$views"},
        }},
        {"$sort": {"avg_views": -1}},
    ]

    insights = []
    async for doc in content_coll.aggregate(pipeline):
        comp = None
        if doc["_id"]:
            try:
                from bson import ObjectId
                comp = await competitor_coll.find_one({"_id": ObjectId(doc["_id"])})
            except Exception:
                pass
        insights.append({
            "competitor_id": doc["_id"],
            "competitor_name": comp.get("name", "未知") if comp else "未知",
            "platform": comp.get("platform", "") if comp else "",
            "total_content": doc["total_content"],
            "avg_views": round(doc["avg_views"], 0),
            "avg_likes": round(doc["avg_likes"], 0),
            "top_content_views": doc["top_content"],
        })

    return {"code": 200, "data": {"days": days, "insights": insights}}
