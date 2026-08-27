"""平台对接数据模型"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class PlatformType(str, Enum):
    XIAOHONGSHU = "xiaohongshu"
    DOUYIN = "douyin"
    WEIXIN_VIDEO = "weixin_video"


class PublishStatus(str, Enum):
    PENDING = "pending"
    PUBLISHING = "publishing"
    SUCCESS = "success"
    FAILED = "failed"


class AccountStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    LOGGED_OUT = "logged_out"


class PublishRequest(BaseModel):
    """发布请求"""
    platform: PlatformType
    title: str
    content: str
    tags: list[str] = Field(default_factory=list)
    images: list[str] = Field(default_factory=list, description="图片路径/URL 列表")
    video_url: str | None = None
    scheduled_at: str | None = None  # ISO format, None = 立即发布


class PublishResult(BaseModel):
    """发布结果"""
    id: str
    platform: str
    status: PublishStatus = PublishStatus.PENDING
    title: str
    content: str
    tags: list[str] = Field(default_factory=list)
    platform_post_id: str | None = None
    platform_post_url: str | None = None
    error_message: str | None = None
    published_at: str | None = None
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class ContentMetrics(BaseModel):
    """内容指标"""
    post_id: str
    platform: str
    views: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    saves: int = 0
    engagement_rate: float = 0.0
    fetched_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class PlatformAccount(BaseModel):
    """平台账号信息"""
    id: str
    platform: PlatformType
    nickname: str = ""
    avatar_url: str = ""
    status: AccountStatus = AccountStatus.ACTIVE
    bound_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    last_sync_at: str | None = None
    extra: dict = Field(default_factory=dict)


class BindAccountRequest(BaseModel):
    """绑定账号请求"""
    platform: PlatformType
    cookies: str = Field(description="从浏览器复制的 Cookie 字符串", alias="cookie")
    nickname: str = ""

    model_config = {"populate_by_name": True}


class LoginQRRequest(BaseModel):
    """扫码登录请求"""
    platform: PlatformType
