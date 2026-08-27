"""平台管理器 — 统一管理所有平台适配器"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime

import memory as _mem

from .base import PlatformAdapter
from .mock_adapter import MockAdapter
from .xiaohongshu import XiaohongshuAdapter
from .douyin import DouyinAdapter
from .weixin_video import WeixinVideoAdapter
from .models import (
    BindAccountRequest,
    ContentMetrics,
    PlatformAccount,
    PlatformType,
    PublishRequest,
    PublishResult,
    PublishStatus,
)

logger = logging.getLogger(__name__)


def _col(name: str):
    return _mem.db[name]


class PlatformManager:
    """平台管理器 — 管理所有平台适配器的生命周期"""

    def __init__(self, use_mock: bool = False):
        self._use_mock = use_mock
        self._adapters: dict[str, PlatformAdapter] = {}
        self._init_adapters()

    def _init_adapters(self):
        if self._use_mock:
            for pt in PlatformType:
                self._adapters[pt.value] = MockAdapter(pt)
        else:
            self._adapters["xiaohongshu"] = XiaohongshuAdapter(
                store_collection=_col("platform_accounts")
            )
            self._adapters["douyin"] = DouyinAdapter(
                store_collection=_col("platform_accounts")
            )
            self._adapters["weixin_video"] = WeixinVideoAdapter(
                store_collection=_col("platform_accounts")
            )

    def get_adapter(self, platform: str) -> PlatformAdapter:
        adapter = self._adapters.get(platform)
        if not adapter:
            raise ValueError(f"不支持的平台: {platform}")
        return adapter

    async def publish(self, req: PublishRequest) -> PublishResult:
        """发布内容到指定平台"""
        adapter = self.get_adapter(req.platform.value)
        result = await adapter.publish(req)

        # 保存发布记录到 MongoDB
        record = {
            "id": result.id,
            "platform": result.platform,
            "status": result.status.value,
            "title": result.title,
            "content": result.content,
            "tags": result.tags,
            "platform_post_id": result.platform_post_id,
            "platform_post_url": result.platform_post_url,
            "error_message": result.error_message,
            "published_at": result.published_at,
            "created_at": datetime.now().isoformat(),
        }
        await _col("publish_records").insert_one(record)
        return result

    async def fetch_metrics(self, platform: str, post_id: str) -> ContentMetrics:
        """获取已发布内容的指标"""
        adapter = self.get_adapter(platform)
        metrics = await adapter.fetch_metrics(post_id)

        # 更新 MongoDB 中的指标
        await _col("content_metrics").update_one(
            {"post_id": post_id, "platform": platform},
            {"$set": metrics.model_dump()},
            upsert=True,
        )
        return metrics

    async def sync_all_metrics(self) -> list[ContentMetrics]:
        """同步所有已发布内容的指标（Phase 3 数据回流）"""
        results = []
        cursor = _col("publish_records").find(
            {"status": "success", "platform_post_id": {"$ne": None}},
            {"_id": 0},
        )
        records = await cursor.to_list(length=200)

        for record in records:
            platform = record.get("platform", "")
            post_id = record.get("platform_post_id", "")
            if not post_id:
                continue
            try:
                metrics = await self.fetch_metrics(platform, post_id)
                results.append(metrics)
            except Exception as e:
                logger.warning(f"同步指标失败: {platform}/{post_id} — {e}")

        return results

    async def get_publish_history(
        self, platform: str | None = None, limit: int = 20
    ) -> list[dict]:
        """获取发布历史"""
        query = {}
        if platform:
            query["platform"] = platform
        cursor = (
            _col("publish_records")
            .find(query, {"_id": 0})
            .sort("created_at", -1)
            .limit(limit)
        )
        return await cursor.to_list(length=limit)

    async def get_all_accounts(self) -> list[PlatformAccount]:
        """获取所有已绑定的账号"""
        accounts = []
        for platform, adapter in self._adapters.items():
            info = await adapter.get_account_info()
            if info:
                accounts.append(info)
        return accounts

    async def bind_account(self, req: BindAccountRequest) -> PlatformAccount:
        """绑定平台账号"""
        adapter = self.get_adapter(req.platform.value)
        return await adapter.bind_account(req)

    async def unbind_account(self, platform: str) -> bool:
        """解绑平台账号"""
        adapter = self.get_adapter(platform)
        return await adapter.unbind_account()

    async def check_login(self, platform: str) -> bool:
        """检查平台登录状态"""
        adapter = self.get_adapter(platform)
        return await adapter.check_login()
