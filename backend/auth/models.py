# -*- coding: utf-8 -*-
"""用户模型和角色定义"""

import enum
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class UserRole(str, enum.Enum):
    """用户角色"""
    ADMIN = "admin"          # 管理员：全部权限
    EDITOR = "editor"        # 编辑：创建/编辑内容，提交审核
    REVIEWER = "reviewer"    # 审核员：审核/驳回内容
    VIEWER = "viewer"        # 只读：查看数据


# 角色权限映射
ROLE_PERMISSIONS = {
    UserRole.ADMIN: [
        "content:create", "content:edit", "content:delete",
        "content:review", "content:publish",
        "account:manage", "account:bind",
        "user:manage", "user:invite",
        "schedule:manage", "abtest:manage",
        "competitor:manage", "alert:manage",
        "cost:view", "cost:manage",
        "data:export", "data:archive",
    ],
    UserRole.EDITOR: [
        "content:create", "content:edit",
        "content:review",  # 可以提交审核
        "account:bind",
        "schedule:manage",
        "abtest:manage",
        "cost:view",
    ],
    UserRole.REVIEWER: [
        "content:review", "content:publish",
        "cost:view",
    ],
    UserRole.VIEWER: [
        "cost:view",
    ],
}


# --- Pydantic Schemas ---

class UserCreate(BaseModel):
    """注册请求"""
    username: str = Field(..., min_length=3, max_length=32, pattern=r'^[a-zA-Z0-9_]+$')
    password: str = Field(..., min_length=6, max_length=128)
    display_name: Optional[str] = Field(None, max_length=64)
    role: Optional[UserRole] = Field(None, description="仅管理员可指定角色")


class UserLogin(BaseModel):
    """登录请求"""
    username: str
    password: str


class UserResponse(BaseModel):
    """用户信息响应"""
    id: str
    username: str
    display_name: str
    role: UserRole
    permissions: list[str]
    created_at: str
    last_login: Optional[str] = None


class TokenResponse(BaseModel):
    """Token 响应"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class PasswordChange(BaseModel):
    """修改密码"""
    old_password: str
    new_password: str = Field(..., min_length=6, max_length=128)


def user_to_response(user_doc: dict) -> UserResponse:
    """MongoDB 文档 → 响应模型"""
    role = user_doc.get("role", UserRole.VIEWER)
    return UserResponse(
        id=str(user_doc["_id"]),
        username=user_doc["username"],
        display_name=user_doc.get("display_name", user_doc["username"]),
        role=role,
        permissions=ROLE_PERMISSIONS.get(role, []),
        created_at=user_doc.get("created_at", datetime.utcnow()).isoformat(),
        last_login=user_doc.get("last_login", datetime.utcnow()).isoformat() if user_doc.get("last_login") else None,
    )
