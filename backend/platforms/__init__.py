"""平台对接层 — v1.3 多平台发布与数据回流"""

from __future__ import annotations

from .base import PlatformAdapter
from .manager import PlatformManager
from .mock_adapter import MockAdapter
from .xiaohongshu import XiaohongshuAdapter
from .douyin import DouyinAdapter
from .weixin_video import WeixinVideoAdapter

__all__ = [
    "PlatformAdapter",
    "PlatformManager",
    "MockAdapter",
    "XiaohongshuAdapter",
    "DouyinAdapter",
    "WeixinVideoAdapter",
]
