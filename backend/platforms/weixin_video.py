"""微信视频号适配器 — Cookie 登录 + 数据采集"""

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

_CHANNELS_BASE = "https://channels.weixin.qq.com"
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://channels.weixin.qq.com/",
}


class WeixinVideoAdapter(PlatformAdapter):
    """微信视频号适配器"""

    platform_id = "weixin_video"

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
        # 视频号发布需要视频，暂不支持
        return PublishResult(
            id=post_id,
            platform="weixin_video",
            status=PublishStatus.FAILED,
            title=req.title,
            content=req.content,
            error_message="视频号发布需要视频文件，请使用视频号助手手动发布",
        )

    async def fetch_metrics(self, post_id: str) -> ContentMetrics:
        if not self._cookies_raw:
            return ContentMetrics(post_id=post_id, platform="weixin_video")
        try:
            async with await self._get_client() as client:
                resp = await client.get(
                    f"{_CHANNELS_BASE}/cgi-bin/mmfinderassistant-bin/feed/get_finder_feed",
                    params={"feed_id": post_id},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    feed = data.get("finder_feed", {})
                    stats = feed.get("stats", {})
                    return ContentMetrics(
                        post_id=post_id,
                        platform="weixin_video",
                        views=int(stats.get("view_count", 0)),
                        likes=int(stats.get("like_count", 0)),
                        comments=int(stats.get("comment_count", 0)),
                        shares=int(stats.get("forward_count", 0)),
                        saves=int(stats.get("fav_count", 0)),
                    )
        except Exception as e:
            logger.warning(f"[WeixinVideo] 获取指标失败: {e}")
        return ContentMetrics(post_id=post_id, platform="weixin_video")

    async def check_login(self) -> bool:
        if not self._cookies_raw:
            return False
        try:
            async with await self._get_client() as client:
                resp = await client.get(f"{_CHANNELS_BASE}/cgi-bin/mmfinderassistant-bin/auth/auth_check")
                return resp.status_code == 200 and resp.json().get("base_resp", {}).get("ret") == 0
        except Exception:
            return False

    async def bind_account(self, req: BindAccountRequest) -> PlatformAccount:
        self._cookies_raw = req.cookies
        self._cookies_encrypted = encrypt_cookie(req.cookies)
        nickname = req.nickname or "视频号用户"
        avatar = ""

        self._account = PlatformAccount(
            id=f"wxv_{uuid.uuid4().hex[:6]}",
            platform=PlatformType.WEIXIN_VIDEO,
            nickname=nickname,
            avatar_url=avatar,
            status=AccountStatus.ACTIVE,
        )
        if self._col is not None:
            await self._col.update_one(
                {"platform": "weixin_video"},
                {"$set": {
                    "platform": "weixin_video",
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
            await self._col.delete_one({"platform": "weixin_video"})
        return True

    async def get_account_info(self) -> PlatformAccount | None:
        if self._account:
            return self._account
        if self._col is not None:
            doc = await self._col.find_one({"platform": "weixin_video"}, {"_id": 0})
            if doc and doc.get("cookies_encrypted"):
                self._cookies_encrypted = doc["cookies_encrypted"]
                try:
                    self._cookies_raw = decrypt_cookie(self._cookies_encrypted)
                except Exception:
                    return None
                self._account = PlatformAccount(
                    id=doc.get("id", f"wxv_{uuid.uuid4().hex[:6]}"),
                    platform=PlatformType.WEIXIN_VIDEO,
                    nickname=doc.get("nickname", ""),
                    avatar_url=doc.get("avatar_url", ""),
                    status=AccountStatus(doc.get("status", "active")),
                    bound_at=doc.get("bound_at", ""),
                )
                return self._account
        return None
