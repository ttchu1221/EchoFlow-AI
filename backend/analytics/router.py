# -*- coding: utf-8 -*-
"""内容效果对比看板 — 发布前 vs 发布后数据对比"""

import logging
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Query

from auth.dependencies import get_current_user

logger = logging.getLogger("echowflow.analytics")

router = APIRouter(prefix="/api/analytics", tags=["效果分析"])


def _get_content_collection():
    from db import get_db
    return get_db()["content"]


def _get_growth_feedback_collection():
    from db import get_db
    return get_db()["growth_feedback"]


@router.get("/performance/overview")
async def performance_overview(
    days: int = Query(30, ge=1, le=365),
    platform: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    """内容效果总览"""
    content_coll = _get_content_collection()
    feedback_coll = _get_growth_feedback_collection()

    cutoff = datetime.utcnow() - timedelta(days=days)
    query = {"published_at": {"$gte": cutoff}}
    if platform:
        query["platform"] = platform

    # 统计已发布内容
    published = list(content_coll.find(query))
    total_published = len(published)

    # 统计各状态数量
    status_counts = {}
    for doc in content_coll.aggregate([{"$group": {"_id": "$status", "count": {"$sum": 1}}}]):
        status_counts[doc["_id"]] = doc["count"]

    # 统计平台分布
    platform_dist = {}
    for doc in published:
        p = doc.get("platform", "unknown")
        platform_dist[p] = platform_dist.get(p, 0) + 1

    # 获取反馈数据
    feedback_query = {"created_at": {"$gte": cutoff.isoformat()}}
    feedbacks = list(feedback_coll.find(feedback_query))

    avg_views = sum(f.get("view_count", 0) for f in feedbacks) / max(len(feedbacks), 1)
    avg_likes = sum(f.get("like_count", 0) for f in feedbacks) / max(len(feedbacks), 1)
    avg_engagement = sum(f.get("engagement_rate", 0) for f in feedbacks) / max(len(feedbacks), 1)

    return {
        "code": 200,
        "data": {
            "period_days": days,
            "total_published": total_published,
            "status_counts": status_counts,
            "platform_distribution": platform_dist,
            "avg_views": round(avg_views, 0),
            "avg_likes": round(avg_likes, 0),
            "avg_engagement_rate": round(avg_engagement, 4),
            "total_feedbacks": len(feedbacks),
        },
    }


@router.get("/performance/trend")
async def performance_trend(
    days: int = Query(30, ge=1, le=365),
    metric: str = Query("views", description="views | likes | engagement_rate"),
    platform: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    """效果趋势（按天）"""
    feedback_coll = _get_growth_feedback_collection()
    cutoff = datetime.utcnow() - timedelta(days=days)

    pipeline = [
        {"$match": {"created_at": {"$gte": cutoff.isoformat()}}},
        {"$group": {
            "_id": {"$substr": ["$created_at", 0, 10]},
            "avg_value": {"$avg": f"${metric}"},
            "count": {"$sum": 1},
        }},
        {"$sort": {"_id": 1}},
    ]

    trend = []
    for doc in feedback_coll.aggregate(pipeline):
        trend.append({
            "date": doc["_id"],
            "value": round(doc["avg_value"], 2),
            "count": doc["count"],
        })

    return {"code": 200, "data": {"metric": metric, "trend": trend}}


@router.get("/performance/top")
async def top_content(
    metric: str = Query("views", description="views | likes | engagement_rate"),
    limit: int = Query(10, ge=1, le=50),
    days: int = Query(30, ge=1, le=365),
    current_user: dict = Depends(get_current_user),
):
    """Top N 内容排行"""
    feedback_coll = _get_growth_feedback_collection()
    cutoff = datetime.utcnow() - timedelta(days=days)

    sort_order = -1 if metric != "engagement_rate" else -1
    items = []
    for doc in feedback_coll.find(
        {"created_at": {"$gte": cutoff.isoformat()}}
    ).sort(metric, sort_order).limit(limit):
        doc["id"] = str(doc.pop("_id"))
        items.append(doc)

    return {"code": 200, "data": {"metric": metric, "items": items}}


@router.get("/performance/compare")
async def compare_periods(
    metric: str = Query("views"),
    current_days: int = Query(30),
    previous_days: int = Query(30),
    current_user: dict = Depends(get_current_user),
):
    """环比对比：当前周期 vs 上一周期"""
    feedback_coll = _get_growth_feedback_collection()
    now = datetime.utcnow()

    current_start = now - timedelta(days=current_days)
    previous_start = current_start - timedelta(days=previous_days)

    # 当前周期
    current_pipeline = [
        {"$match": {"created_at": {"$gte": current_start.isoformat(), "$lt": now.isoformat()}}},
        {"$group": {"_id": None, "avg": {"$avg": f"${metric}"}, "count": {"$sum": 1}}},
    ]
    current_result = list(feedback_coll.aggregate(current_pipeline))
    current_avg = current_result[0]["avg"] if current_result else 0
    current_count = current_result[0]["count"] if current_result else 0

    # 上一周期
    previous_pipeline = [
        {"$match": {"created_at": {"$gte": previous_start.isoformat(), "$lt": current_start.isoformat()}}},
        {"$group": {"_id": None, "avg": {"$avg": f"${metric}"}, "count": {"$sum": 1}}},
    ]
    previous_result = list(feedback_coll.aggregate(previous_pipeline))
    previous_avg = previous_result[0]["avg"] if previous_result else 0
    previous_count = previous_result[0]["count"] if previous_result else 0

    # 计算变化率
    change_pct = 0
    if previous_avg > 0:
        change_pct = round((current_avg - previous_avg) / previous_avg * 100, 2)

    return {
        "code": 200,
        "data": {
            "metric": metric,
            "current": {"days": current_days, "avg": round(current_avg, 2), "count": current_count},
            "previous": {"days": previous_days, "avg": round(previous_avg, 2), "count": previous_count},
            "change_pct": change_pct,
            "trend": "up" if change_pct > 0 else "down" if change_pct < 0 else "flat",
        },
    }
