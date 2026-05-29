"""Mock 适配器 — 用于本地开发和演示"""

from __future__ import annotations

import logging
import random
import uuid
from datetime import datetime

from .base import PlatformAdapter
from .models import (
    AccountStatus,
    BindAccountRequest,
    ContentMetrics,
    PlatformAccount,
    PlatformType,
    PublishRequest,
    PublishResult,
    PublishStatus,
)

logger = logging.getLogger(__name__)


class MockAdapter(PlatformAdapter):
    """模拟适配器，所有操作返回模拟数据"""

    platform_id = "mock"

    def __init__(self, platform_type: PlatformType = PlatformType.XIAOHONGSHU):
        self.platform_type = platform_type
        self._bound = False
        self._posts: dict[str, PublishResult] = {}

    async def publish(self, req: PublishRequest) -> PublishResult:
        post_id = f"mock_{uuid.uuid4().hex[:8]}"
        result = PublishResult(
            id=post_id,
            platform=req.platform.value,
            status=PublishStatus.SUCCESS,
            title=req.title,
            content=req.content,
            tags=req.tags,
            platform_post_id=post_id,
            platform_post_url=f"https://mock.{req.platform.value}.com/post/{post_id}",
            published_at=datetime.now().isoformat(),
        )
        self._posts[post_id] = result
        logger.info(f"[Mock] 已发布: {req.title} → {req.platform.value}")
        return result

    async def fetch_metrics(self, post_id: str) -> ContentMetrics:
        return ContentMetrics(
            post_id=post_id,
            platform=self.platform_type.value,
            views=random.randint(100, 50000),
            likes=random.randint(10, 5000),
            comments=random.randint(0, 500),
            shares=random.randint(0, 200),
            saves=random.randint(0, 1000),
            engagement_rate=round(random.uniform(0.01, 0.15), 4),
        )

    async def check_login(self) -> bool:
        return self._bound

    async def bind_account(self, req: BindAccountRequest) -> PlatformAccount:
        self._bound = True
        return PlatformAccount(
            id=f"mock_acc_{uuid.uuid4().hex[:6]}",
            platform=req.platform,
            nickname=req.nickname or f"Mock_{req.platform.value}_User",
            avatar_url="",
            status=AccountStatus.ACTIVE,
        )

    async def unbind_account(self) -> bool:
        self._bound = False
        return True

    async def get_account_info(self) -> PlatformAccount | None:
        if not self._bound:
            return None
        return PlatformAccount(
            id=f"mock_acc_{self.platform_type.value}",
            platform=self.platform_type,
            nickname=f"Mock_{self.platform_type.value}_User",
            status=AccountStatus.ACTIVE,
        )
