"""小红书适配器 — Cookie 登录 + 发布 + 数据采集"""

from __future__ import annotations

import logging
import re
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

# 小红书 Web API
_XHS_BASE = "https://edith.xiaohongshu.com"
_XHS_WEB = "https://www.xiaohongshu.com"

# 请求头模拟浏览器
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.xiaohongshu.com/",
    "Origin": "https://www.xiaohongshu.com",
}


class XiaohongshuAdapter(PlatformAdapter):
    """小红书平台适配器"""

    platform_id = "xiaohongshu"

    def __init__(self, store_collection=None):
        self._cookies_raw: str | None = None
        self._cookies_encrypted: str | None = None
        self._account: PlatformAccount | None = None
        self._col = store_collection  # MongoDB collection for persistence

    async def _get_client(self) -> httpx.AsyncClient:
        """创建带 Cookie 的 HTTP 客户端"""
        cookies = {}
        if self._cookies_raw:
            for item in self._cookies_raw.split(";"):
                item = item.strip()
                if "=" in item:
                    k, v = item.split("=", 1)
                    cookies[k.strip()] = v.strip()
        return httpx.AsyncClient(
            headers=_HEADERS,
            cookies=cookies,
            timeout=15.0,
            follow_redirects=True,
        )

    async def publish(self, req: PublishRequest) -> PublishResult:
        """发布笔记到小红书（通过 Web API）"""
        if not self._cookies_raw:
            return PublishResult(
                id=str(uuid.uuid4())[:8],
                platform="xiaohongshu",
                status=PublishStatus.FAILED,
                title=req.title,
                content=req.content,
                error_message="未登录，请先绑定小红书账号",
            )

        post_id = str(uuid.uuid4())[:8]
        try:
            async with await self._get_client() as client:
                # 小红书发布笔记 API
                payload = {
                    "title": req.title,
                    "desc": req.content,
                    "tags": ",".join(req.tags) if req.tags else "",
                    "post_type": "normal",
                }

                # 如果有图片，先上传
                if req.images:
                    payload["image_list"] = req.images

                resp = await client.post(
                    f"{_XHS_BASE}/api/sns/web/v1/feed",
                    json=payload,
                )

                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("success"):
                        note_id = data.get("data", {}).get("note_id", post_id)
                        return PublishResult(
                            id=post_id,
                            platform="xiaohongshu",
                            status=PublishStatus.SUCCESS,
                            title=req.title,
                            content=req.content,
                            tags=req.tags,
                            platform_post_id=note_id,
                            platform_post_url=f"https://www.xiaohongshu.com/explore/{note_id}",
                            published_at=datetime.now().isoformat(),
                        )
                    else:
                        error_msg = data.get("msg", "发布失败")
                        logger.warning(f"[XHS] 发布失败: {error_msg}")
                        return PublishResult(
                            id=post_id,
                            platform="xiaohongshu",
                            status=PublishStatus.FAILED,
                            title=req.title,
                            content=req.content,
                            error_message=error_msg,
                        )
                else:
                    logger.warning(f"[XHS] HTTP {resp.status_code}")
                    return PublishResult(
                        id=post_id,
                        platform="xiaohongshu",
                        status=PublishStatus.FAILED,
                        title=req.title,
                        content=req.content,
                        error_message=f"HTTP {resp.status_code}",
                    )

        except Exception as e:
            logger.exception(f"[XHS] 发布异常: {e}")
            return PublishResult(
                id=post_id,
                platform="xiaohongshu",
                status=PublishStatus.FAILED,
                title=req.title,
                content=req.content,
                error_message=str(e),
            )

    async def fetch_metrics(self, post_id: str) -> ContentMetrics:
        """获取笔记数据指标"""
        if not self._cookies_raw:
            return ContentMetrics(post_id=post_id, platform="xiaohongshu")

        try:
            async with await self._get_client() as client:
                resp = await client.get(
                    f"{_XHS_BASE}/api/sns/web/v1/feed",
                    params={"source_note_id": post_id},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    note = data.get("data", {}).get("items", [{}])[0].get("note_card", {})
                    interact = note.get("interact_info", {})
                    return ContentMetrics(
                        post_id=post_id,
                        platform="xiaohongshu",
                        views=int(interact.get("view_count", 0)),
                        likes=int(interact.get("liked_count", 0)),
                        comments=int(interact.get("comment_count", 0)),
                        shares=int(interact.get("share_count", 0)),
                        saves=int(interact.get("collected_count", 0)),
                    )
        except Exception as e:
            logger.warning(f"[XHS] 获取指标失败: {e}")

        return ContentMetrics(post_id=post_id, platform="xiaohongshu")

    async def check_login(self) -> bool:
        if not self._cookies_raw:
            return False
        try:
            async with await self._get_client() as client:
                resp = await client.get(f"{_XHS_BASE}/api/sns/web/v1/user/selfinfo")
                return resp.status_code == 200 and resp.json().get("success")
        except Exception:
            return False

    async def bind_account(self, req: BindAccountRequest) -> PlatformAccount:
        """通过 Cookie 绑定小红书账号"""
        self._cookies_raw = req.cookies
        self._cookies_encrypted = encrypt_cookie(req.cookies)

        # 验证 Cookie 有效性并获取用户信息
        nickname = req.nickname
        avatar = ""
        try:
            async with await self._get_client() as client:
                resp = await client.get(f"{_XHS_BASE}/api/sns/web/v1/user/selfinfo")
                if resp.status_code == 200:
                    data = resp.json().get("data", {})
                    nickname = nickname or data.get("nickname", "小红书用户")
                    avatar = data.get("image", "")
        except Exception as e:
            logger.warning(f"[XHS] 获取用户信息失败: {e}")

        self._account = PlatformAccount(
            id=f"xhs_{uuid.uuid4().hex[:6]}",
            platform=PlatformType.XIAOHONGSHU,
            nickname=nickname,
            avatar_url=avatar,
            status=AccountStatus.ACTIVE,
        )

        # 持久化到 MongoDB
        if self._col is not None:
            await self._col.update_one(
                {"platform": "xiaohongshu"},
                {"$set": {
                    "platform": "xiaohongshu",
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
            await self._col.delete_one({"platform": "xiaohongshu"})
        return True

    async def get_account_info(self) -> PlatformAccount | None:
        if self._account:
            return self._account
        # 从 MongoDB 恢复
        if self._col is not None:
            doc = await self._col.find_one({"platform": "xiaohongshu"}, {"_id": 0})
            if doc and doc.get("cookies_encrypted"):
                self._cookies_encrypted = doc["cookies_encrypted"]
                try:
                    self._cookies_raw = decrypt_cookie(self._cookies_encrypted)
                except Exception:
                    return None
                self._account = PlatformAccount(
                    id=doc.get("id", f"xhs_{uuid.uuid4().hex[:6]}"),
                    platform=PlatformType.XIAOHONGSHU,
                    nickname=doc.get("nickname", ""),
                    avatar_url=doc.get("avatar_url", ""),
                    status=AccountStatus(doc.get("status", "active")),
                    bound_at=doc.get("bound_at", ""),
                )
                return self._account
        return None
