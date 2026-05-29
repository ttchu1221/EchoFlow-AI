"""爬虫基础模块 — 反爬策略、HTTP会话管理、重试机制"""

from __future__ import annotations

import asyncio
import logging
import random
import time
from typing import Any

import httpx
from fake_useragent import UserAgent

logger = logging.getLogger(__name__)

# ── User-Agent 池 ─────────────────────────────────────────
_ua = UserAgent(browsers=["chrome", "edge", "firefox"], os=["windows", "macos"])


def random_ua() -> str:
    return _ua.random


# ── 常用浏览器指纹 Headers 模板 ────────────────────────────
_CHROME_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0",
    "sec-ch-ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
}


def build_headers(referer: str = "", extra: dict | None = None) -> dict[str, str]:
    """构建带随机 UA 的请求头"""
    headers = {**_CHROME_HEADERS, "User-Agent": random_ua()}
    if referer:
        headers["Referer"] = referer
    if extra:
        headers.update(extra)
    return headers


# ── 随机延迟 ──────────────────────────────────────────────

async def random_delay(min_s: float = 1.0, max_s: float = 3.0):
    """随机延迟，模拟人类行为"""
    delay = random.uniform(min_s, max_s)
    await asyncio.sleep(delay)


# ── 带重试的 HTTP 客户端 ──────────────────────────────────

class CrawlerClient:
    """封装 httpx.AsyncClient，自带反爬策略"""

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        timeout: float = 15.0,
        proxy: str | None = None,
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.timeout = timeout
        self.proxy = proxy
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self):
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout),
            follow_redirects=True,
            http2=True,
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
        )
        return self

    async def __aexit__(self, *args):
        if self._client:
            await self._client.aclose()

    async def get(
        self,
        url: str,
        headers: dict | None = None,
        params: dict | None = None,
        referer: str = "",
    ) -> dict[str, Any] | None:
        """带重试和随机延迟的 GET 请求"""
        if not self._client:
            raise RuntimeError("CrawlerClient 未初始化，请使用 async with")

        req_headers = build_headers(referer=referer)
        if headers:
            req_headers.update(headers)

        last_err = None
        for attempt in range(self.max_retries):
            try:
                await random_delay(
                    self.base_delay * (attempt + 1),
                    self.base_delay * (attempt + 1) + 1.0,
                )

                resp = await self._client.get(
                    url,
                    headers=req_headers,
                    params=params,
                )

                if resp.status_code == 200:
                    return resp.json()
                elif resp.status_code == 404:
                    # 资源不存在，重试无意义
                    logger.warning(f"HTTP 404: {url}")
                    return None
                elif resp.status_code == 403:
                    logger.warning(f"[反爬] 403 Forbidden: {url} (尝试 {attempt + 1})")
                    await random_delay(3.0, 6.0)
                elif resp.status_code == 429:
                    logger.warning(f"[反爬] 429 限流: {url} (尝试 {attempt + 1})")
                    await random_delay(5.0, 10.0)
                else:
                    logger.warning(f"HTTP {resp.status_code}: {url}")

            except httpx.TimeoutException:
                logger.warning(f"请求超时: {url} (尝试 {attempt + 1})")
            except httpx.HTTPError as e:
                logger.warning(f"HTTP 错误: {e} (尝试 {attempt + 1})")
                last_err = e

        logger.error(f"请求失败（已重试 {self.max_retries} 次）: {url}")
        return None

    async def get_html(
        self,
        url: str,
        headers: dict | None = None,
        params: dict | None = None,
        referer: str = "",
    ) -> str | None:
        """带重试的 GET 请求，返回 HTML 文本"""
        if not self._client:
            raise RuntimeError("CrawlerClient 未初始化，请使用 async with")

        req_headers = build_headers(referer=referer)
        if headers:
            req_headers.update(headers)
        # HTML 请求不需要 JSON Accept
        req_headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"

        for attempt in range(self.max_retries):
            try:
                await random_delay(
                    self.base_delay * (attempt + 1),
                    self.base_delay * (attempt + 1) + 1.0,
                )
                resp = await self._client.get(
                    url, headers=req_headers, params=params,
                )
                if resp.status_code == 200:
                    return resp.text
                elif resp.status_code == 404:
                    logger.warning(f"HTTP 404: {url}")
                    return None
                elif resp.status_code in (403, 429):
                    logger.warning(f"[反爬] {resp.status_code}: {url}")
                    await random_delay(3.0, 8.0)
            except Exception as e:
                logger.warning(f"请求错误: {e}")
        return None
