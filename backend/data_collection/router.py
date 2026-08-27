from __future__ import annotations

import logging
from datetime import datetime

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query

from auth.dependencies import get_current_user
from crawlers.data_source import fetch_hot_search

from .models import CollectionJobCreate, ManualCollectRequest, SmartCollectQuestion
from .service import _clean_id, _db, create_job, overview, record_many, update_job_run
from .smart_query import answer_with_auto_collection

logger = logging.getLogger("echoflow.data_collection.router")

router = APIRouter(prefix="/api/data-collection", tags=["data-collection"])


@router.get("/overview")
async def get_overview(days: int = Query(7, ge=1, le=365), current_user: dict = Depends(get_current_user)):
    return {"code": 200, "data": await overview(days)}


@router.post("/jobs")
async def create_collection_job(req: CollectionJobCreate, current_user: dict = Depends(get_current_user)):
    job = await create_job(req.model_dump(), current_user)
    return {"code": 200, "data": job}


@router.get("/jobs")
async def list_jobs(
    status: str = "",
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    db = _db()
    query = {"status": status} if status else {}
    total = await db["collection_jobs"].count_documents(query)
    cursor = db["collection_jobs"].find(query).sort("created_at", -1).skip((page - 1) * size).limit(size)
    items = [_clean_id(doc) async for doc in cursor]
    return {"code": 200, "data": {"total": total, "items": items, "page": page, "size": size}}


@router.post("/jobs/{job_id}/run")
async def run_job(job_id: str, current_user: dict = Depends(get_current_user)):
    db = _db()
    try:
        job = await db["collection_jobs"].find_one({"_id": ObjectId(job_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="无效的任务 ID")
    if not job:
        raise HTTPException(status_code=404, detail="采集任务不存在")
    target = job.get("target", {})
    try:
        result = await _run_collect(
            platform=target.get("platform", "douyin"),
            source_type=target.get("source_type", "hot_search"),
            keyword=target.get("keyword", ""),
            account_id=target.get("account_id", ""),
            account_name=target.get("account_name", ""),
            limit=int(target.get("limit", 20)),
            job_id=job_id,
        )
        await update_job_run(job_id, "success", result)
        return {"code": 200, "data": result}
    except Exception as e:
        logger.exception("[采集任务] 执行失败")
        await update_job_run(job_id, "failed", None, str(e))
        raise HTTPException(status_code=500, detail=f"采集失败: {e}")


@router.post("/collect")
async def manual_collect(req: ManualCollectRequest, current_user: dict = Depends(get_current_user)):
    result = await _run_collect(
        platform=req.platform,
        source_type=req.source_type,
        keyword=req.keyword,
        account_id=req.account_id,
        account_name=req.account_name,
        limit=req.limit,
    )
    return {"code": 200, "data": result}


@router.post("/ask")
async def ask_with_auto_collection(req: SmartCollectQuestion, current_user: dict = Depends(get_current_user)):
    """自然语言提问 -> 自动判断数据源 -> 采集 -> 标准化入库 -> 基于数据回答"""
    try:
        result = await answer_with_auto_collection(req.question)
        return {"code": 200, "data": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("[智能采集问答] 失败")
        raise HTTPException(status_code=500, detail=f"智能采集失败: {e}")


@router.get("/contents")
async def list_contents(
    platform: str = "",
    source_type: str = "",
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    db = _db()
    query = {}
    if platform:
        query["platform"] = platform
    if source_type:
        query["source_type"] = source_type
    total = await db["standard_contents"].count_documents(query)
    cursor = db["standard_contents"].find(query).sort("collected_at", -1).skip((page - 1) * size).limit(size)
    items = [_clean_id(doc) async for doc in cursor]
    return {"code": 200, "data": {"total": total, "items": items, "page": page, "size": size}}


@router.get("/quality")
async def quality_report(current_user: dict = Depends(get_current_user)):
    db = _db()
    docs = await db["standard_contents"].find({}, {"quality": 1, "platform": 1, "source_type": 1}).sort("collected_at", -1).limit(500).to_list(length=500)
    low_quality = [d for d in docs if d.get("quality", {}).get("score", 1) < 0.75]
    duplicate_count = sum(1 for d in docs if d.get("quality", {}).get("is_duplicate"))
    return {
        "code": 200,
        "data": {
            "sample_size": len(docs),
            "low_quality_count": len(low_quality),
            "duplicate_count": duplicate_count,
            "issues": [_clean_id(d) for d in low_quality[:20]],
        },
    }


async def _run_collect(
    platform: str,
    source_type: str,
    keyword: str = "",
    account_id: str = "",
    account_name: str = "",
    limit: int = 20,
    job_id: str | None = None,
) -> dict:
    started_at = datetime.utcnow()
    if source_type == "hot_search":
        items = await fetch_hot_search(platform, limit)
        normalized_items = [{**item, "platform": platform} for item in items]
    elif source_type == "keyword_content":
        from crawlers.content_search import fetch_keyword_content
        if not keyword:
            raise HTTPException(status_code=400, detail="关键词内容采集需要填写 keyword")
        items = await fetch_keyword_content(platform, keyword, limit)
        normalized_items = [{**item, "platform": platform, "keyword": keyword} for item in items]
    elif source_type == "competitor_content":
        from competitor.crawler import fetch_competitor_content
        items = await fetch_competitor_content(platform, account_id, account_name or keyword, limit)
        normalized_items = [{**item, "platform": platform, "account_name": account_name or keyword} for item in items]
    else:
        raise HTTPException(status_code=400, detail=f"暂不支持采集类型: {source_type}")

    stats = await record_many(platform, source_type, normalized_items, job_id)
    fallback_used = any(item.get("source_note") for item in normalized_items)
    source_status = "success" if normalized_items else "empty"
    stats.update({
        "platform": platform,
        "source_type": source_type,
        "started_at": started_at.isoformat(),
        "completed_at": datetime.utcnow().isoformat(),
        "source_status": source_status,
        "fallback_used": fallback_used,
        "failure_reason": "" if normalized_items else "未从目标平台或兜底源获取到有效内容",
    })
    return stats
