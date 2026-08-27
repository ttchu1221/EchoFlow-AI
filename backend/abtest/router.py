# -*- coding: utf-8 -*-
"""A/B 测试框架 — 同一话题多版本内容对比"""

import logging
import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException

from auth.dependencies import get_current_user, require_permission

logger = logging.getLogger("echowflow.abtest")

router = APIRouter(prefix="/api/abtest", tags=["A/B 测试"])


class ABVariant(BaseModel):
    """A/B 变体"""
    variant_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = Field(..., max_length=50)
    content: dict
    platform: str = ""
    content_id: Optional[str] = None


class ABTestCreate(BaseModel):
    """创建 A/B 测试"""
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    topic: str = ""
    variants: list[ABVariant] = Field(..., min_length=2, max_length=5)
    metric: str = "engagement_rate"
    auto_select: bool = True
    auto_select_hours: int = 24


def _get_abtest_collection():
    from memory import db
    if db is None:
        raise RuntimeError("MongoDB 未初始化")
    return db["ab_tests"]


@router.post("", status_code=201)
async def create_ab_test(
    body: ABTestCreate,
    current_user: dict = Depends(require_permission("abtest:manage")),
):
    """创建 A/B 测试"""
    coll = _get_abtest_collection()
    now = datetime.utcnow()

    doc = {
        "name": body.name,
        "description": body.description,
        "topic": body.topic,
        "variants": [v.model_dump() for v in body.variants],
        "metric": body.metric,
        "auto_select": body.auto_select,
        "auto_select_hours": body.auto_select_hours,
        "status": "created",
        "winner_variant_id": None,
        "created_by": current_user["username"],
        "created_at": now,
        "updated_at": now,
        "started_at": None,
        "completed_at": None,
        "results": [],
    }
    result = await coll.insert_one(doc)
    doc["id"] = str(result.inserted_id)
    del doc["_id"]

    logger.info(f"A/B 测试创建: {body.name} ({len(body.variants)} 个变体)")
    return {"code": 200, "data": doc}


@router.get("")
async def list_ab_tests(
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    """获取 A/B 测试列表"""
    coll = _get_abtest_collection()
    query = {}
    if status:
        query["status"] = status

    items = []
    async for doc in coll.find(query).sort("created_at", -1):
        doc["id"] = str(doc.pop("_id"))
        items.append(doc)
    return {"code": 200, "data": items}


@router.get("/{test_id}")
async def get_ab_test(test_id: str, current_user: dict = Depends(get_current_user)):
    """获取 A/B 测试详情"""
    coll = _get_abtest_collection()
    from bson import ObjectId
    try:
        doc = await coll.find_one({"_id": ObjectId(test_id)})
    except Exception:
        raise HTTPException(400, detail={"code": 400, "error": "无效的测试 ID"})
    if not doc:
        raise HTTPException(404, detail={"code": 404, "error": "测试不存在"})
    doc["id"] = str(doc.pop("_id"))
    return {"code": 200, "data": doc}


@router.post("/{test_id}/start")
async def start_ab_test(
    test_id: str,
    current_user: dict = Depends(require_permission("abtest:manage")),
):
    """启动 A/B 测试"""
    coll = _get_abtest_collection()
    from bson import ObjectId
    doc = await coll.find_one({"_id": ObjectId(test_id)})
    if not doc:
        raise HTTPException(404, detail={"code": 404, "error": "测试不存在"})
    if doc.get("status") != "created":
        raise HTTPException(400, detail={"code": 400, "error": f"当前状态 {doc['status']} 不允许启动"})

    await coll.update_one(
        {"_id": ObjectId(test_id)},
        {"$set": {"status": "running", "started_at": datetime.utcnow(), "updated_at": datetime.utcnow()}},
    )

    logger.info(f"A/B 测试启动: {test_id}")
    return {"code": 200, "message": "测试已启动"}


@router.post("/{test_id}/complete")
async def complete_ab_test(
    test_id: str,
    winner_variant_id: Optional[str] = None,
    current_user: dict = Depends(require_permission("abtest:manage")),
):
    """完成 A/B 测试"""
    coll = _get_abtest_collection()
    from bson import ObjectId
    doc = await coll.find_one({"_id": ObjectId(test_id)})
    if not doc:
        raise HTTPException(404, detail={"code": 404, "error": "测试不存在"})

    results = doc.get("results", [])
    metric = doc.get("metric", "engagement_rate")

    if not winner_variant_id and results:
        best = max(results, key=lambda r: r.get(metric, 0))
        winner_variant_id = best.get("variant_id")

    await coll.update_one(
        {"_id": ObjectId(test_id)},
        {"$set": {
            "status": "completed",
            "winner_variant_id": winner_variant_id,
            "completed_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }},
    )

    logger.info(f"A/B 测试完成: {test_id}, 优胜: {winner_variant_id}")
    return {"code": 200, "data": {"winner_variant_id": winner_variant_id}}


@router.get("/{test_id}/analysis")
async def analyze_ab_test(test_id: str, current_user: dict = Depends(get_current_user)):
    """分析 A/B 测试结果"""
    coll = _get_abtest_collection()
    from bson import ObjectId
    doc = await coll.find_one({"_id": ObjectId(test_id)})
    if not doc:
        raise HTTPException(404, detail={"code": 404, "error": "测试不存在"})

    results = doc.get("results", [])
    metric = doc.get("metric", "engagement_rate")

    if not results:
        return {"code": 200, "data": {"message": "暂无结果数据"}}

    ranked = sorted(results, key=lambda r: r.get(metric, 0), reverse=True)

    analysis = {
        "test_name": doc.get("name"),
        "metric": metric,
        "ranking": [],
        "improvement": None,
    }

    for i, r in enumerate(ranked):
        analysis["ranking"].append({
            "rank": i + 1,
            "variant_id": r["variant_id"],
            "metric_value": r.get(metric, 0),
            "views": r.get("views", 0),
            "likes": r.get("likes", 0),
        })

    if len(ranked) >= 2:
        best_val = ranked[0].get(metric, 0)
        worst_val = ranked[-1].get(metric, 0)
        if worst_val > 0:
            analysis["improvement"] = round((best_val - worst_val) / worst_val * 100, 1)

    return {"code": 200, "data": analysis}
