# -*- coding: utf-8 -*-
"""团队协作 — 操作日志 + 评论批注"""

import logging
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, Query

from auth.dependencies import get_current_user, require_permission

logger = logging.getLogger("echowflow.team")

router = APIRouter(prefix="/api/team", tags=["团队协作"])


class CommentCreate(BaseModel):
    """评论/批注"""
    target_type: str = Field(..., description="content | abtest | competitor")
    target_id: str
    content: str = Field(..., max_length=2000)
    parent_id: Optional[str] = None


def _get_comments_collection():
    from memory import db
    if db is None:
        raise RuntimeError("MongoDB 未初始化")
    return db["comments"]


def _get_activity_collection():
    from memory import db
    if db is None:
        raise RuntimeError("MongoDB 未初始化")
    return db["activity_logs"]


async def log_activity(
    user_id: str,
    username: str,
    action: str,
    target_type: str,
    target_id: str,
    target_name: str = "",
    details: Optional[dict] = None,
):
    """记录操作日志"""
    coll = _get_activity_collection()
    doc = {
        "user_id": user_id,
        "username": username,
        "action": action,
        "target_type": target_type,
        "target_id": target_id,
        "target_name": target_name,
        "details": details or {},
        "timestamp": datetime.utcnow().isoformat(),
    }
    await coll.insert_one(doc)


@router.post("/comments", status_code=201)
async def add_comment(
    body: CommentCreate,
    current_user: dict = Depends(get_current_user),
):
    """添加评论"""
    coll = _get_comments_collection()
    now = datetime.utcnow()

    doc = {
        "target_type": body.target_type,
        "target_id": body.target_id,
        "content": body.content,
        "parent_id": body.parent_id,
        "user_id": current_user["user_id"],
        "username": current_user["username"],
        "created_at": now,
        "updated_at": now,
        "is_deleted": False,
    }
    result = await coll.insert_one(doc)
    doc["id"] = str(result.inserted_id)
    del doc["_id"]

    await log_activity(
        current_user["user_id"], current_user["username"],
        "comment", body.target_type, body.target_id,
        body.content[:50],
    )

    return {"code": 200, "data": doc}


@router.get("/comments")
async def list_comments(
    target_type: str = Query(...),
    target_id: str = Query(...),
    current_user: dict = Depends(get_current_user),
):
    """获取评论列表"""
    coll = _get_comments_collection()
    items = []
    async for doc in coll.find({
        "target_type": target_type,
        "target_id": target_id,
        "is_deleted": False,
    }).sort("created_at", 1):
        doc["id"] = str(doc.pop("_id"))
        items.append(doc)

    return {"code": 200, "data": items}


@router.delete("/comments/{comment_id}")
async def delete_comment(
    comment_id: str,
    current_user: dict = Depends(get_current_user),
):
    """删除评论（软删除）"""
    coll = _get_comments_collection()
    from bson import ObjectId
    doc = await coll.find_one({"_id": ObjectId(comment_id)})
    if not doc:
        raise HTTPException(404, detail={"code": 404, "error": "评论不存在"})

    if doc["user_id"] != current_user["user_id"] and current_user.get("role") != "admin":
        raise HTTPException(403, detail={"code": 403, "error": "无权删除他人评论"})

    await coll.update_one({"_id": ObjectId(comment_id)}, {"$set": {"is_deleted": True}})
    return {"code": 200, "message": "评论已删除"}


@router.get("/activity")
async def list_activity(
    limit: int = 50,
    target_type: Optional[str] = None,
    target_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    """获取操作日志"""
    coll = _get_activity_collection()
    query = {}
    if target_type:
        query["target_type"] = target_type
    if target_id:
        query["target_id"] = target_id

    items = []
    async for doc in coll.find(query).sort("timestamp", -1).limit(limit):
        doc["id"] = str(doc.pop("_id"))
        items.append(doc)

    return {"code": 200, "data": items}


@router.get("/activity/user/{user_id}")
async def user_activity(
    user_id: str,
    limit: int = 50,
    current_user: dict = Depends(get_current_user),
):
    """获取用户操作日志"""
    coll = _get_activity_collection()
    items = []
    async for doc in coll.find({"user_id": user_id}).sort("timestamp", -1).limit(limit):
        doc["id"] = str(doc.pop("_id"))
        items.append(doc)
    return {"code": 200, "data": items}
