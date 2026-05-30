# -*- coding: utf-8 -*-
"""内容审核 API 路由"""

import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from .states import (
    ContentStatus, ReviewAction, ContentItem, ReviewRequest,
    BulkReviewRequest, can_transition, transition,
)
from auth.dependencies import get_current_user, require_permission

logger = logging.getLogger("echowflow.workflow")

router = APIRouter(prefix="/api/content", tags=["内容审核"])


def _get_content_collection():
    from memory import db
    if db is None:
        raise RuntimeError("MongoDB 未初始化")
    return db["content"]


def _doc_to_item(doc: dict) -> dict:
    """MongoDB 文档 → 响应"""
    doc["id"] = str(doc.pop("_id"))
    doc.setdefault("history", [])
    return doc


@router.post("", status_code=201)
async def create_content(
    item: ContentItem,
    current_user: dict = Depends(require_permission("content:create")),
):
    """创建内容（草稿）"""
    coll = _get_content_collection()
    now = datetime.utcnow()
    doc = item.model_dump()
    doc["status"] = ContentStatus.DRAFT.value
    doc["author_id"] = current_user["user_id"]
    doc["author_name"] = current_user["username"]
    doc["created_at"] = now
    doc["updated_at"] = now
    doc["history"] = [{
        "action": "create",
        "from_status": None,
        "to_status": ContentStatus.DRAFT.value,
        "user": current_user["username"],
        "at": now.isoformat(),
    }]
    result = await coll.insert_one(doc)
    doc["_id"] = result.inserted_id

    logger.info(f"内容创建: {item.title} by {current_user['username']}")
    return {"code": 200, "data": _doc_to_item(doc)}


@router.get("")
async def list_content(
    status: Optional[str] = Query(None, description="按状态过滤"),
    platform: Optional[str] = Query(None, description="按平台过滤"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    """获取内容列表"""
    coll = _get_content_collection()
    query = {}
    if status:
        query["status"] = status
    if platform:
        query["platform"] = platform

    total = await coll.count_documents(query)
    skip = (page - 1) * page_size
    items = []
    async for doc in coll.find(query).sort("updated_at", -1).skip(skip).limit(page_size):
        items.append(_doc_to_item(doc))

    return {
        "code": 200,
        "data": {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        },
    }


@router.get("/{content_id}")
async def get_content(content_id: str, current_user: dict = Depends(get_current_user)):
    """获取单条内容"""
    coll = _get_content_collection()
    from bson import ObjectId
    try:
        doc = await coll.find_one({"_id": ObjectId(content_id)})
    except Exception:
        raise HTTPException(400, detail={"code": 400, "error": "无效的内容 ID"})
    if not doc:
        raise HTTPException(404, detail={"code": 404, "error": "内容不存在"})
    return {"code": 200, "data": _doc_to_item(doc)}


@router.put("/{content_id}")
async def update_content(
    content_id: str,
    item: ContentItem,
    current_user: dict = Depends(require_permission("content:edit")),
):
    """编辑内容（仅草稿/驳回状态可编辑）"""
    coll = _get_content_collection()
    from bson import ObjectId
    try:
        doc = await coll.find_one({"_id": ObjectId(content_id)})
    except Exception:
        raise HTTPException(400, detail={"code": 400, "error": "无效的内容 ID"})
    if not doc:
        raise HTTPException(404, detail={"code": 404, "error": "内容不存在"})

    current_status = ContentStatus(doc.get("status", ContentStatus.DRAFT.value))
    if current_status not in [ContentStatus.DRAFT, ContentStatus.REJECTED]:
        raise HTTPException(400, detail={"code": 400, "error": f"状态 {current_status.value} 不可编辑"})

    now = datetime.utcnow()
    update_doc = {
        "title": item.title,
        "content": item.content,
        "platform": item.platform,
        "status": ContentStatus.DRAFT.value,
        "updated_at": now,
    }
    await coll.update_one({"_id": ObjectId(content_id)}, {"$set": update_doc})
    doc.update(update_doc)

    # 记录历史
    history_entry = {
        "action": "edit",
        "from_status": current_status.value,
        "to_status": ContentStatus.DRAFT.value,
        "user": current_user["username"],
        "at": now.isoformat(),
    }
    await coll.update_one({"_id": ObjectId(content_id)}, {"$push": {"history": history_entry}})

    logger.info(f"内容编辑: {content_id} by {current_user['username']}")
    return {"code": 200, "data": _doc_to_item(doc)}


@router.post("/{content_id}/review")
async def review_content(
    content_id: str,
    req: ReviewRequest,
    current_user: dict = Depends(get_current_user),
):
    """审核内容（提交/通过/驳回/发布）"""
    coll = _get_content_collection()
    from bson import ObjectId
    try:
        doc = await coll.find_one({"_id": ObjectId(content_id)})
    except Exception:
        raise HTTPException(400, detail={"code": 400, "error": "无效的内容 ID"})
    if not doc:
        raise HTTPException(404, detail={"code": 404, "error": "内容不存在"})

    current_status = ContentStatus(doc.get("status", ContentStatus.DRAFT.value))

    # 权限检查
    action = req.action
    if action in [ReviewAction.APPROVE, ReviewAction.REJECT]:
        if "content:review" not in _get_user_permissions(current_user):
            raise HTTPException(403, detail={"code": 403, "error": "无审核权限"})
    if action == ReviewAction.PUBLISH:
        if "content:publish" not in _get_user_permissions(current_user):
            raise HTTPException(403, detail={"code": 403, "error": "无发布权限"})

    # 状态转换
    if not can_transition(current_status, action):
        raise HTTPException(400, detail={
            "code": 400,
            "error": f"非法操作: {current_status.value} 不允许 {action.value}",
        })

    new_status = transition(current_status, action)
    now = datetime.utcnow()

    update_fields = {
        "status": new_status.value,
        "updated_at": now,
    }
    if action in [ReviewAction.APPROVE, ReviewAction.REJECT]:
        update_fields["reviewer_id"] = current_user["user_id"]
        update_fields["reviewer_name"] = current_user["username"]
        update_fields["review_comment"] = req.comment
    if new_status == ContentStatus.PUBLISHED:
        update_fields["published_at"] = now

    await coll.update_one({"_id": ObjectId(content_id)}, {"$set": update_fields})

    # 编辑时附带内容修改
    if action == ReviewAction.EDIT and req.content:
        await coll.update_one({"_id": ObjectId(content_id)}, {"$set": {"content": req.content}})

    history_entry = {
        "action": action.value,
        "from_status": current_status.value,
        "to_status": new_status.value,
        "user": current_user["username"],
        "comment": req.comment,
        "at": now.isoformat(),
    }
    await coll.update_one({"_id": ObjectId(content_id)}, {"$push": {"history": history_entry}})

    logger.info(f"内容审核: {content_id} {action.value} by {current_user['username']}")
    return {"code": 200, "message": f"操作成功: {new_status.value}"}


@router.post("/batch/review")
async def batch_review(
    req: BulkReviewRequest,
    current_user: dict = Depends(get_current_user),
):
    """批量审核"""
    coll = _get_content_collection()
    from bson import ObjectId

    success, failed = 0, 0
    errors = []
    for cid in req.content_ids:
        try:
            doc = await coll.find_one({"_id": ObjectId(cid)})
            if not doc:
                errors.append({"id": cid, "error": "不存在"})
                failed += 1
                continue

            current_status = ContentStatus(doc.get("status", ContentStatus.DRAFT.value))
            if not can_transition(current_status, req.action):
                errors.append({"id": cid, "error": f"状态 {current_status.value} 不允许 {req.action.value}"})
                failed += 1
                continue

            new_status = transition(current_status, req.action)
            now = datetime.utcnow()
            update_fields = {"status": new_status.value, "updated_at": now}
            if req.action in [ReviewAction.APPROVE, ReviewAction.REJECT]:
                update_fields["reviewer_id"] = current_user["user_id"]
                update_fields["reviewer_name"] = current_user["username"]
                update_fields["review_comment"] = req.comment

            await coll.update_one({"_id": ObjectId(cid)}, {"$set": update_fields})
            await coll.update_one({"_id": ObjectId(cid)}, {"$push": {"history": {
                "action": req.action.value,
                "from_status": current_status.value,
                "to_status": new_status.value,
                "user": current_user["username"],
                "comment": req.comment,
                "at": now.isoformat(),
            }}})
            success += 1
        except Exception as e:
            errors.append({"id": cid, "error": str(e)})
            failed += 1

    return {"code": 200, "data": {"success": success, "failed": failed, "errors": errors}}


@router.get("/stats/overview")
async def content_stats(current_user: dict = Depends(get_current_user)):
    """内容统计概览"""
    coll = _get_content_collection()
    pipeline = [
        {"$group": {"_id": "$status", "count": {"$sum": 1}}},
    ]
    stats = {}
    async for doc in coll.aggregate(pipeline):
        stats[doc["_id"]] = doc["count"]

    return {
        "code": 200,
        "data": {
            "total": sum(stats.values()),
            "by_status": stats,
        },
    }


def _get_user_permissions(user: dict) -> list:
    """获取用户权限列表"""
    from auth.models import ROLE_PERMISSIONS, UserRole
    try:
        role = UserRole(user.get("role", "viewer"))
    except ValueError:
        role = UserRole.VIEWER
    return ROLE_PERMISSIONS.get(role, [])
