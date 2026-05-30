# -*- coding: utf-8 -*-
"""认证 API 路由"""

import time
import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from passlib.context import CryptContext

from .models import (
    UserCreate, UserLogin, UserResponse, TokenResponse,
    PasswordChange, UserRole, user_to_response,
)
from .jwt_handler import create_access_token, create_refresh_token, decode_token
from .dependencies import get_current_user, require_role

logger = logging.getLogger("echowflow.auth")

router = APIRouter(prefix="/api/auth", tags=["认证"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _get_users_collection():
    """延迟获取 MongoDB users 集合"""
    from memory import db
    if db is None:
        raise RuntimeError("MongoDB 未初始化")
    return db["users"]


@router.post("/register", response_model=dict, status_code=201)
async def register(body: UserCreate):
    """注册新用户"""
    users = _get_users_collection()

    # 检查用户名是否已存在
    existing = await users.find_one({"username": body.username})
    if existing:
        raise HTTPException(400, detail={"code": 400, "error": "用户名已存在"})

    # 第一个用户自动成为管理员
    user_count = await users.count_documents({})
    role = UserRole.ADMIN if user_count == 0 else (body.role or UserRole.EDITOR)

    hashed = pwd_context.hash(body.password)
    now = datetime.utcnow()
    doc = {
        "username": body.username,
        "password": hashed,
        "display_name": body.display_name or body.username,
        "role": role.value if isinstance(role, UserRole) else role,
        "created_at": now,
        "last_login": None,
        "is_active": True,
    }
    result = await users.insert_one(doc)
    doc["_id"] = result.inserted_id

    logger.info(f"用户注册: {body.username}, 角色: {role}")

    # 自动登录返回 token
    token_data = create_access_token(str(result.inserted_id), body.username, role.value if isinstance(role, UserRole) else role)
    user_resp = user_to_response(doc)

    return {
        "code": 200,
        "message": "注册成功",
        "data": {
            **token_data,
            "user": user_resp.model_dump(),
        },
    }


@router.post("/login", response_model=dict)
async def login(body: UserLogin):
    """用户登录"""
    users = _get_users_collection()
    user = await users.find_one({"username": body.username})

    if not user or not pwd_context.verify(body.password, user["password"]):
        raise HTTPException(401, detail={"code": 401, "error": "用户名或密码错误"})

    if not user.get("is_active", True):
        raise HTTPException(403, detail={"code": 403, "error": "账号已被禁用"})

    # 更新最后登录时间
    await users.update_one({"_id": user["_id"]}, {"$set": {"last_login": datetime.utcnow()}})

    role = user.get("role", UserRole.VIEWER)
    token_data = create_access_token(str(user["_id"]), user["username"], role)
    user_resp = user_to_response(user)

    logger.info(f"用户登录: {body.username}")

    return {
        "code": 200,
        "message": "登录成功",
        "data": {
            **token_data,
            "user": user_resp.model_dump(),
        },
    }


@router.post("/refresh", response_model=dict)
async def refresh_token(refresh_token: str):
    """刷新 access token"""
    try:
        payload = decode_token(refresh_token)
    except ValueError as e:
        raise HTTPException(401, detail={"code": 401, "error": str(e)})

    if payload.get("type") != "refresh":
        raise HTTPException(401, detail={"code": 401, "error": "无效的 refresh token"})

    users = _get_users_collection()
    from bson import ObjectId
    user = await users.find_one({"_id": ObjectId(payload["sub"])})
    if not user:
        raise HTTPException(401, detail={"code": 401, "error": "用户不存在"})

    role = user.get("role", UserRole.VIEWER)
    token_data = create_access_token(str(user["_id"]), user["username"], role)

    return {"code": 200, "message": "刷新成功", "data": token_data}


@router.get("/me", response_model=dict)
async def get_me(current_user: dict = Depends(get_current_user)):
    """获取当前用户信息"""
    users = _get_users_collection()
    from bson import ObjectId
    user = await users.find_one({"_id": ObjectId(current_user["user_id"])})
    if not user:
        raise HTTPException(404, detail={"code": 404, "error": "用户不存在"})
    return {"code": 200, "data": user_to_response(user).model_dump()}


@router.put("/password", response_model=dict)
async def change_password(
    body: PasswordChange,
    current_user: dict = Depends(get_current_user),
):
    """修改密码"""
    users = _get_users_collection()
    from bson import ObjectId
    user = await users.find_one({"_id": ObjectId(current_user["user_id"])})
    if not user or not pwd_context.verify(body.old_password, user["password"]):
        raise HTTPException(400, detail={"code": 400, "error": "原密码错误"})

    hashed = pwd_context.hash(body.new_password)
    await users.update_one({"_id": user["_id"]}, {"$set": {"password": hashed}})
    logger.info(f"用户修改密码: {current_user['username']}")

    return {"code": 200, "message": "密码修改成功"}


@router.get("/users", response_model=dict)
async def list_users(current_user: dict = Depends(require_role(UserRole.ADMIN))):
    """获取用户列表（仅管理员）"""
    users = _get_users_collection()
    result = []
    async for u in users.find().sort("created_at", -1):
        result.append(user_to_response(u).model_dump())
    return {"code": 200, "data": result}


@router.put("/users/{user_id}/role", response_model=dict)
async def update_user_role(
    user_id: str,
    role: UserRole,
    current_user: dict = Depends(require_role(UserRole.ADMIN)),
):
    """修改用户角色（仅管理员）"""
    users = _get_users_collection()
    from bson import ObjectId
    result = await users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"role": role.value}},
    )
    if result.matched_count == 0:
        raise HTTPException(404, detail={"code": 404, "error": "用户不存在"})

    logger.info(f"管理员 {current_user['username']} 修改用户 {user_id} 角色为 {role.value}")
    return {"code": 200, "message": f"角色已更新为 {role.value}"}


@router.put("/users/{user_id}/status", response_model=dict)
async def toggle_user_status(
    user_id: str,
    active: bool,
    current_user: dict = Depends(require_role(UserRole.ADMIN)),
):
    """启用/禁用用户（仅管理员）"""
    users = _get_users_collection()
    from bson import ObjectId
    result = await users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"is_active": active}},
    )
    if result.matched_count == 0:
        raise HTTPException(404, detail={"code": 404, "error": "用户不存在"})

    status_text = "启用" if active else "禁用"
    logger.info(f"管理员 {current_user['username']} {status_text}用户 {user_id}")
    return {"code": 200, "message": f"用户已{status_text}"}
