"""抖音适配器 — Cookie 登录 + 网页数据采集"""

from __future__ import annotations

import json
import logging
import re
import uuid
from datetime import datetime
from urllib.parse import unquote

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
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}


class DouyinAdapter(PlatformAdapter):
    """抖音平台适配器"""

    platform_id = "douyin"

    def __init__(self, store_collection=None):
        self._cookies_raw: str | None = None
        self._cookies_encrypted: str | None = None
        self._account: PlatformAccount | None = None
        self._col = store_collection

    def _parse_cookies(self) -> dict[str, str]:
        cookies = {}
        if self._cookies_raw:
            for item in self._cookies_raw.split(";"):
                item = item.strip()
                if "=" in item:
                    k, v = item.split("=", 1)
                    cookies[k.strip()] = v.strip()
        return cookies

    async def _get_client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            headers=_HEADERS,
            cookies=self._parse_cookies(),
            timeout=20.0,
            follow_redirects=True,
        )

    # ── Cookie 验证 ──────────────────────────────────────────────────

    async def _validate_cookie(self) -> tuple[bool, str, str]:
        """
        验证 Cookie 是否有效。
        抖音有 JS 反爬保护，纯 httpx 请求会被拦截。
        验证策略：
        1. 尝试 API 端点（可能被反爬拦截）
        2. 检查 Cookie 中的关键登录标识
        """
        if not self._cookies_raw:
            return False, "", ""

        # 检查关键登录 Cookie 是否存在
        cookies = self._parse_cookies()
        has_session = bool(cookies.get("sessionid") or cookies.get("sid_tt"))
        has_uid = bool(cookies.get("uid_tt"))
        has_passport = bool(cookies.get("passport_csrf_token"))

        if not (has_session and has_uid):
            return False, "", ""

        # 尝试 API 验证（可能被反爬拦截，不作为唯一判断）
        try:
            async with httpx.AsyncClient(
                headers={**_HEADERS, "Accept": "application/json, text/plain, */*"},
                cookies=cookies,
                timeout=15.0,
                follow_redirects=True,
            ) as client:
                resp = await client.get(f"{_DY_BASE}/aweme/v1/web/user/profile/self/")
                if resp.status_code == 200:
                    try:
                        data = resp.json()
                        if data.get("status_code") == 0:
                            user = data.get("user", {})
                            if isinstance(user, dict):
                                nickname = user.get("nickname", "")
                                avatar_obj = user.get("avatar_larger", {})
                                avatar = ""
                                if isinstance(avatar_obj, dict):
                                    urls = avatar_obj.get("url_list", [])
                                    avatar = urls[0] if urls else ""
                                return True, nickname, avatar
                    except Exception:
                        pass
        except Exception as e:
            logger.warning(f"[Douyin] API 验证异常: {e}")

        # API 被反爬拦截时，根据 Cookie 标识判断
        # 有 sessionid + uid_tt + passport_csrf_token + passport_auth_status = 已登录
        if has_session and has_uid and has_passport:
            logger.info("[Douyin] API 被反爬拦截，Cookie 标识判断为已登录")
            return True, "抖音用户", ""

        return False, "", ""

    # ── 网页数据采集 ─────────────────────────────────────────────────

    async def fetch_metrics(self, post_id: str) -> ContentMetrics:
        """
        获取视频数据 — Playwright 拦截 /aweme/v1/web/aweme/detail/ API 响应。
        """
        url = f"{_DY_BASE}/video/{post_id}"
        try:
            from playwright.async_api import async_playwright

            aweme_data = {}

            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent=_HEADERS["User-Agent"],
                    locale="zh-CN",
                )
                page = await context.new_page()

                # 注入用户 Cookie
                if self._cookies_raw:
                    cookies = self._parse_cookies()
                    for name, value in cookies.items():
                        await context.add_cookies([{
                            "name": name,
                            "value": value,
                            "domain": ".douyin.com",
                            "path": "/",
                        }])

                # 拦截 aweme/detail API 响应
                async def on_response(response):
                    if "aweme/detail" in response.url:
                        try:
                            data = await response.json()
                            if data.get("aweme_detail"):
                                aweme_data.update(data["aweme_detail"])
                        except Exception:
                            pass

                page.on("response", on_response)
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                # 等待 API 请求完成
                await page.wait_for_timeout(5000)
                await browser.close()

            if aweme_data:
                stats = aweme_data.get("statistics", {})
                logger.info(f"[Douyin] 视频统计: {json.dumps(stats, ensure_ascii=False)[:200]}")
                return self._stats_to_metrics(post_id, stats)

            logger.warning(f"[Douyin] 未拦截到视频数据 (id={post_id})")

        except ImportError:
            logger.warning("[Douyin] playwright 未安装")
        except Exception as e:
            logger.warning(f"[Douyin] 数据采集异常: {e}")

        return ContentMetrics(post_id=post_id, platform="douyin")

    def _extract_stats_from_html(self, html: str) -> dict | None:
        """从 HTML 中提取视频统计数据"""
        # 尝试 RENDER_DATA
        match = re.search(r'<script\s+id="RENDER_DATA"[^>]*>(.+?)</script>', html, re.DOTALL)
        if match:
            try:
                raw = unquote(match.group(1))
                data = json.loads(raw)
                stats = self._deep_find_statistics(data)
                if stats:
                    return stats
            except Exception as e:
                logger.warning(f"[Douyin] RENDER_DATA 解析失败: {e}")

        # 尝试 _SSR_HYDRATED_DATA
        match2 = re.search(r'window\._SSR_HYDRATED_DATA\s*=\s*(\{.+?\})\s*</script>', html, re.DOTALL)
        if match2:
            try:
                data = json.loads(match2.group(1))
                stats = self._deep_find_statistics(data)
                if stats:
                    return stats
            except Exception as e:
                logger.warning(f"[Douyin] SSR_HYDRATED_DATA 解析失败: {e}")

        return None

    def _deep_find_statistics(self, data, depth: int = 0) -> dict | None:
        """递归查找视频统计数据（兼容多种字段命名）"""
        if depth > 20:
            return None
        if isinstance(data, dict):
            # 检查 statistics 字段
            if "statistics" in data and isinstance(data["statistics"], dict):
                stats = data["statistics"]
                if any(k in stats for k in ("digg_count", "comment_count", "play_count", "diggCount", "commentCount", "playCount")):
                    return stats
            # 检查 stats 字段
            if "stats" in data and isinstance(data["stats"], dict):
                stats = data["stats"]
                if any(k in stats for k in ("diggCount", "commentCount", "playCount", "digg_count", "comment_count", "play_count")):
                    return stats
            # 检查 aweme_id + 统计字段直接在当前层
            if "aweme_id" in data or "awemeId" in data:
                stat_keys = [k for k in data if any(s in k.lower() for s in ("count", "digg", "comment", "play", "share", "collect"))]
                if len(stat_keys) >= 2:
                    return {k: data[k] for k in stat_keys}
            # 检查 video + statistics 组合
            if "video" in data and isinstance(data["video"], dict):
                video = data["video"]
                if "statistics" in video and isinstance(video["statistics"], dict):
                    return video["statistics"]
            for v in data.values():
                result = self._deep_find_statistics(v, depth + 1)
                if result:
                    return result
        elif isinstance(data, list):
            for item in data:
                result = self._deep_find_statistics(item, depth + 1)
                if result:
                    return result
        return None

    def _stats_to_metrics(self, aweme_id: str, stats: dict) -> ContentMetrics:
        """将抖音 statistics 转为 ContentMetrics"""
        return ContentMetrics(
            post_id=aweme_id,
            platform="douyin",
            views=int(stats.get("play_count", stats.get("playCount", 0))),
            likes=int(stats.get("digg_count", stats.get("diggCount", 0))),
            comments=int(stats.get("comment_count", stats.get("commentCount", 0))),
            shares=int(stats.get("share_count", stats.get("shareCount", 0))),
            saves=int(stats.get("collect_count", stats.get("collectCount", 0))),
        )

    # ── 发布 ─────────────────────────────────────────────────────────

    async def publish(self, req: PublishRequest) -> PublishResult:
        post_id = str(uuid.uuid4())[:8]
        return PublishResult(
            id=post_id,
            platform="douyin",
            status=PublishStatus.FAILED,
            title=req.title,
            content=req.content,
            error_message="抖音发布需要视频文件，请使用抖音创作者中心手动发布",
        )

    # ── 账号管理 ─────────────────────────────────────────────────────

    async def check_login(self) -> bool:
        valid, _, _ = await self._validate_cookie()
        return valid

    async def bind_account(self, req: BindAccountRequest) -> PlatformAccount:
        """绑定账号 — 必须先验证 Cookie 有效性"""
        self._cookies_raw = req.cookies

        valid, nickname, avatar = await self._validate_cookie()
        if not valid:
            raise ValueError("Cookie 无效或已过期，请重新获取")

        self._cookies_encrypted = encrypt_cookie(req.cookies)
        nickname = req.nickname or nickname or "抖音用户"

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
