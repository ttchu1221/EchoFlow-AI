"""抖音适配器 — Cookie 登录 + 数据采集（发布需 RPA）"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime

import httpx

from .base import PlatformAdapter
from .crypto import decrypt_cookie, encrypt_cookie
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

_DY_BASE = "https://www.douyin.com"
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.douyin.com/",
}


class DouyinAdapter(PlatformAdapter):
    """抖音平台适配器"""

    platform_id = "douyin"

    def __init__(self, store_collection=None):
        self._cookies_raw: str | None = None
        self._cookies_encrypted: str | None = None
        self._account: PlatformAccount | None = None
        self._col = store_collection

    async def _get_client(self) -> httpx.AsyncClient:
        cookies = {}
        if self._cookies_raw:
            for item in self._cookies_raw.split(";"):
                item = item.strip()
                if "=" in item:
                    k, v = item.split("=", 1)
                    cookies[k.strip()] = v.strip()
        return httpx.AsyncClient(
            headers=_HEADERS, cookies=cookies, timeout=15.0, follow_redirects=True
        )

    async def publish(self, req: PublishRequest) -> PublishResult:
        post_id = str(uuid.uuid4())[:8]
        # 抖音 Web 发布接口需要视频，暂不支持直接发布
        return PublishResult(
            id=post_id,
            platform="douyin",
            status=PublishStatus.FAILED,
            title=req.title,
            content=req.content,
            error_message="抖音发布需要视频文件，请使用抖音创作者中心手动发布",
        )

    async def fetch_metrics(self, post_id: str) -> ContentMetrics:
        if not self._cookies_raw:
            return ContentMetrics(post_id=post_id, platform="douyin")
        try:
            async with await self._get_client() as client:
                resp = await client.get(
                    f"{_DY_BASE}/aweme/v1/web/aweme/detail/",
                    params={"aweme_id": post_id},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    detail = data.get("aweme_detail", {})
                    stats = detail.get("statistics", {})
                    return ContentMetrics(
                        post_id=post_id,
                        platform="douyin",
                        views=int(stats.get("play_count", 0)),
                        likes=int(stats.get("digg_count", 0)),
                        comments=int(stats.get("comment_count", 0)),
                        shares=int(stats.get("share_count", 0)),
                        saves=int(stats.get("collect_count", 0)),
                    )
        except Exception as e:
            logger.warning(f"[Douyin] 获取指标失败: {e}")
        return ContentMetrics(post_id=post_id, platform="douyin")

    async def check_login(self) -> bool:
        if not self._cookies_raw:
            return False
        try:
            async with await self._get_client() as client:
                resp = await client.get(f"{_DY_BASE}/aweme/v1/web/user/profile/self/")
                return resp.status_code == 200 and resp.json().get("status_code") == 0
        except Exception:
            return False

    async def bind_account(self, req: BindAccountRequest) -> PlatformAccount:
        self._cookies_raw = req.cookies
        self._cookies_encrypted = encrypt_cookie(req.cookies)
        nickname = req.nickname or "抖音用户"
        avatar = ""
        try:
            async with await self._get_client() as client:
                resp = await client.get(f"{_DY_BASE}/aweme/v1/web/user/profile/self/")
                if resp.status_code == 200:
                    data = resp.json().get("user", {})
                    nickname = nickname or data.get("nickname", "抖音用户")
                    avatar = data.get("avatar_larger", {}).get("url_list", [""])[0]
        except Exception as e:
            logger.warning(f"[Douyin] 获取用户信息失败: {e}")

        self._account = PlatformAccount(
            id=f"dy_{uuid.uuid4().hex[:6]}",
            platform=PlatformType.DOUYIN,
            nickname=nickname,
            avatar_url=avatar,
            status=AccountStatus.ACTIVE,
        )
        if self._col is not None:
            await self._col.update_one(
                {"platform": "douyin"},
                {"$set": {
                    "platform": "douyin",
                    "nickname": nickname,
                    "avatar_url": avatar,
                    "cookies_encrypted": self._cookies_encrypted,
                    "status": "active",
                    "bound_at": datetime.now().isoformat(),
                }},
                upsert=True,
            )
        return self._account

    async def unbind_account(self) -> bool:
        self._cookies_raw = None
        self._cookies_encrypted = None
        self._account = None
        if self._col is not None:
            await self._col.delete_one({"platform": "douyin"})
        return True

    async def get_account_info(self) -> PlatformAccount | None:
        if self._account:
            return self._account
        if self._col is not None:
            doc = await self._col.find_one({"platform": "douyin"}, {"_id": 0})
            if doc and doc.get("cookies_encrypted"):
                self._cookies_encrypted = doc["cookies_encrypted"]
                try:
                    self._cookies_raw = decrypt_cookie(self._cookies_encrypted)
                except Exception:
                    return None
                self._account = PlatformAccount(
                    id=doc.get("id", f"dy_{uuid.uuid4().hex[:6]}"),
                    platform=PlatformType.DOUYIN,
                    nickname=doc.get("nickname", ""),
                    avatar_url=doc.get("avatar_url", ""),
                    status=AccountStatus(doc.get("status", "active")),
                    bound_at=doc.get("bound_at", ""),
                )
                return self._account
        return None
