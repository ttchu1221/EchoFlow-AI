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


@router.post("/collect")
async def trigger_data_collection(
    current_user: dict = Depends(require_permission("abtest:manage")),
):
    """手动触发 A/B 测试数据采集
    
    立即从平台拉取所有运行中测试的变体指标，并自动判定到期测试的优胜者。
    """
    from abtest.collector import collect_abtest_metrics
    result = await collect_abtest_metrics()
    return {"code": 200, "data": result}


@router.post("/{test_id}/update-results")
async def update_test_results(
    test_id: str,
    body: dict,
    current_user: dict = Depends(require_permission("abtest:manage")),
):
    """手动录入变体表现数据
    
    请求体:
    {
        "variant_id": "xxx",
        "views": 1000,
        "likes": 50,
        "comments": 10,
        "shares": 5
    }
    """
    coll = _get_abtest_collection()
    from bson import ObjectId
    doc = await coll.find_one({"_id": ObjectId(test_id)})
    if not doc:
        raise HTTPException(404, detail={"code": 404, "error": "测试不存在"})

    variant_id = body.get("variant_id", "")
    if not variant_id:
        raise HTTPException(400, detail={"code": 400, "error": "variant_id 不能为空"})

    views = int(body.get("views", 0))
    likes = int(body.get("likes", 0))
    comments = int(body.get("comments", 0))
    shares = int(body.get("shares", 0))
    engagement_rate = round((likes + comments + shares) / max(views, 1), 4)

    # 更新 results 数组
    results = doc.get("results", [])
    # 移除旧的同 variant_id 结果
    results = [r for r in results if r.get("variant_id") != variant_id]
    results.append({
        "variant_id": variant_id,
        "views": views,
        "likes": likes,
        "comments": comments,
        "shares": shares,
        "engagement_rate": engagement_rate,
        "collected_at": datetime.utcnow().isoformat(),
        "source": "manual",
    })

    await coll.update_one(
        {"_id": ObjectId(test_id)},
        {"$set": {"results": results, "updated_at": datetime.utcnow()}},
    )

    return {"code": 200, "data": {"variant_id": variant_id, "engagement_rate": engagement_rate}}
