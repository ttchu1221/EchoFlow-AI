# -*- coding: utf-8 -*-
"""JWT Token 管理"""

import os
import time
import jwt
import logging

logger = logging.getLogger("echowflow.auth")

# 配置
JWT_SECRET = os.getenv("JWT_SECRET", "echowflow-default-secret-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRE_HOURS", "24"))
JWT_REFRESH_DAYS = int(os.getenv("JWT_REFRESH_DAYS", "7"))


def create_access_token(user_id: str, username: str, role: str) -> dict:
    """创建 access token"""
    now = time.time()
    payload = {
        "sub": user_id,
        "username": username,
        "role": role,
        "type": "access",
        "iat": now,
        "exp": now + JWT_EXPIRE_HOURS * 3600,
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": JWT_EXPIRE_HOURS * 3600,
    }


def create_refresh_token(user_id: str) -> str:
    """创建 refresh token"""
    now = time.time()
    payload = {
        "sub": user_id,
        "type": "refresh",
        "iat": now,
        "exp": now + JWT_REFRESH_DAYS * 86400,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """解码并验证 token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("token 已过期")
    except jwt.InvalidTokenError:
        raise ValueError("无效的 token")
