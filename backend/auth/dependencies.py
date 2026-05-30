# -*- coding: utf-8 -*-
"""FastAPI 认证依赖"""

import logging
from datetime import datetime
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .jwt_handler import decode_token
from .models import UserRole, ROLE_PERMISSIONS

logger = logging.getLogger("echowflow.auth")

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> dict:
    """获取当前认证用户（必须登录）"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": 401, "error": "未登录，请先登录"},
        )

    try:
        payload = decode_token(credentials.credentials)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": 401, "error": str(e)},
        )

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": 401, "error": "无效的 token 类型"},
        )

    return {
        "user_id": payload["sub"],
        "username": payload["username"],
        "role": payload.get("role", UserRole.VIEWER),
    }


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[dict]:
    """获取当前用户（可选，未登录返回 None）"""
    if not credentials:
        return None
    try:
        payload = decode_token(credentials.credentials)
        if payload.get("type") != "access":
            return None
        return {
            "user_id": payload["sub"],
            "username": payload["username"],
            "role": payload.get("role", UserRole.VIEWER),
        }
    except (ValueError, Exception):
        return None


def require_role(*roles: UserRole):
    """角色检查依赖工厂"""
    async def _check(current_user: dict = Depends(get_current_user)) -> dict:
        user_role = current_user.get("role", UserRole.VIEWER)
        if user_role not in [r.value for r in roles]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": 403, "error": f"权限不足，需要角色: {[r.value for r in roles]}"},
            )
        return current_user
    return _check


def require_permission(permission: str):
    """权限检查依赖工厂"""
    async def _check(current_user: dict = Depends(get_current_user)) -> dict:
        user_role = current_user.get("role", UserRole.VIEWER)
        try:
            role_enum = UserRole(user_role)
        except ValueError:
            role_enum = UserRole.VIEWER
        perms = ROLE_PERMISSIONS.get(role_enum, [])
        if permission not in perms:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": 403, "error": f"权限不足，需要: {permission}"},
            )
        return current_user
    return _check
