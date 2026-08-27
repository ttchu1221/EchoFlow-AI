"""平台适配器基类"""

from __future__ import annotations

from abc import ABC, abstractmethod

from .models import (
    BindAccountRequest,
    ContentMetrics,
    PlatformAccount,
    PublishRequest,
    PublishResult,
)


class PlatformAdapter(ABC):
    """所有平台适配器的抽象基类"""

    platform_id: str = ""

    @abstractmethod
    async def publish(self, req: PublishRequest) -> PublishResult:
        """发布内容到平台"""

    @abstractmethod
    async def fetch_metrics(self, post_id: str) -> ContentMetrics:
        """获取已发布内容的指标数据"""

    @abstractmethod
    async def check_login(self) -> bool:
        """检查登录状态是否有效"""

    @abstractmethod
    async def bind_account(self, req: BindAccountRequest) -> PlatformAccount:
        """绑定平台账号（通过 Cookie）"""

    @abstractmethod
    async def unbind_account(self) -> bool:
        """解绑平台账号"""

    @abstractmethod
    async def get_account_info(self) -> PlatformAccount | None:
        """获取当前绑定的账号信息"""
