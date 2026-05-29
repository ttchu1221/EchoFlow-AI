"""抖音爬虫 — 热搜抓取（反爬重点处理）"""

from __future__ import annotations

import logging
import re
from typing import Any

from crawlers.base import CrawlerClient, build_headers

logger = logging.getLogger(__name__)

# 抖音热搜 API（移动端接口，相对稳定）
_DOUYIN_HOT_API = "https://www.douyin.com/aweme/v1/web/hot/search/list/"
# 备用：通过页面解析
_DOUYIN_HOT_PAGE = "https://www.douyin.com/hot"
# 聚合平台备用
_TOPHUB_API = "https://tophub.today/api/nodes/2"


async def fetch_hot_search(limit: int = 30) -> list[dict]:
    """获取抖音热搜榜

    策略：
    1. 优先尝试抖音官方 API
    2. 失败则从页面 HTML 解析
    3. 最后 fallback 到聚合平台
    """
    # 方式1: 抖音热搜 API
    results = await _fetch_from_api(limit)
    if results:
        return results

    # 方式2: 页面解析
    results = await _fetch_from_page(limit)
    if results:
        return results

    # 方式3: 聚合平台 fallback
    results = await _fetch_from_tophub(limit)
    if results:
        return results

    logger.warning("[抖音] 所有热搜获取方式均失败")
    return []


async def _fetch_from_api(limit: int) -> list[dict]:
    """通过抖音官方 API 获取热搜（先获取临时 Cookie）"""
    try:
        async with CrawlerClient(base_delay=2.0, max_retries=2) as client:
            # 先访问抖音主页获取 __ac_nonce Cookie
            home_resp = await client.get_html(
                "https://www.douyin.com/",
                referer="https://www.douyin.com/",
            )
            # 从 client session 中获取 Cookie
            cookies = {}
            if hasattr(client, "_client") and hasattr(client._client, "cookies"):
                cookies = dict(client._client.cookies)

            # 调用热搜 API
            data = await client.get(
                _DOUYIN_HOT_API,
                headers={
                    "Referer": "https://www.douyin.com/",
                    "Origin": "https://www.douyin.com",
                },
                params={
                    "device_platform": "webapp",
                    "aid": "6383",
                    "channel": "channel_pc_web",
                    "detail_list": "1",
                },
                referer="https://www.douyin.com/",
            )
            if data and data.get("data", {}).get("word_list"):
                results = []
                for item in data["data"]["word_list"][:limit]:
                    results.append({
                        "keyword": item.get("word", ""),
                        "heat_score": item.get("hot_value", 0),
                        "position": item.get("position", 0),
                        "label": item.get("label", ""),
                        "event_time": item.get("event_time", ""),
                        "url": f"https://www.douyin.com/search/{item.get('word', '')}",
                    })
                logger.info(f"[抖音] API 获取到 {len(results)} 条热搜")
                return results
    except Exception as e:
        logger.warning(f"[抖音] API 获取失败: {e}")
    return []


async def _fetch_from_page(limit: int) -> list[dict]:
    """从抖音热搜页面解析数据（反爬严格，可能失败）"""
    try:
        async with CrawlerClient(base_delay=3.0, max_retries=2) as client:
            html = await client.get_html(
                _DOUYIN_HOT_PAGE,
                referer="https://www.douyin.com",
            )
            if not html:
                return []

            # 尝试从 SSR 数据中提取 JSON
            match = re.search(r'<script id="RENDER_DATA"[^>]*>([^<]+)</script>', html)
            if match:
                import urllib.parse
                decoded = urllib.parse.unquote(match.group(1))
                import json
                data = json.loads(decoded)
                # 递归查找热搜列表
                hot_list = _extract_hot_list(data)
                if hot_list:
                    results = []
                    for item in hot_list[:limit]:
                        results.append({
                            "keyword": item.get("word", ""),
                            "heat_score": item.get("hotValue", item.get("hot_value", 0)),
                            "position": item.get("position", 0),
                            "label": item.get("label", ""),
                            "url": f"https://www.douyin.com/search/{item.get('word', '')}",
                        })
                    logger.info(f"[抖音] 页面解析获取到 {len(results)} 条热搜")
                    return results
    except Exception as e:
        logger.warning(f"[抖音] 页面解析失败: {e}")
    return []


async def _fetch_from_tophub(limit: int) -> list[dict]:
    """从 tophub.today 聚合平台获取抖音热搜（兜底方案）"""
    try:
        async with CrawlerClient(base_delay=1.0, max_retries=2) as client:
            # tophub.today 的抖音热搜节点
            data = await client.get(
                "https://tophub.today/api/nodes/2",
                referer="https://tophub.today",
            )
            if data and isinstance(data, dict) and data.get("data"):
                items = data["data"] if isinstance(data["data"], list) else data["data"].get("items", [])
                results = []
                for item in items[:limit]:
                    if isinstance(item, dict):
                        results.append({
                            "keyword": item.get("title", item.get("name", "")),
                            "heat_score": item.get("extra", {}).get("hot_value", 0) if isinstance(item.get("extra"), dict) else 0,
                            "url": item.get("url", ""),
                        })
                if results:
                    logger.info(f"[抖音] tophub 获取到 {len(results)} 条热搜")
                    return results

            # 备用：直接抓 tophub 页面
            html = await client.get_html("https://tophub.today/n/DpQvNABoNE", referer="https://tophub.today")
            if html:
                # 简单正则提取
                items = re.findall(r'class="al[^"]*"[^>]*>.*?<a[^>]*>([^<]+)</a>', html, re.DOTALL)
                if items:
                    results = [{"keyword": t.strip(), "heat_score": 0, "url": ""} for t in items[:limit] if t.strip()]
                    logger.info(f"[抖音] tophub HTML 获取到 {len(results)} 条热搜")
                    return results
    except Exception as e:
        logger.warning(f"[抖音] tophub 获取失败: {e}")
    return []


def _extract_hot_list(obj: Any) -> list[dict]:
    """递归搜索 JSON 中的热搜列表"""
    if isinstance(obj, dict):
        # 直接匹配已知 key
        for key in ("wordList", "word_list", "hotList", "hot_list", "data"):
            if key in obj and isinstance(obj[key], list) and len(obj[key]) > 0:
                first = obj[key][0]
                if isinstance(first, dict) and ("word" in first or "title" in first):
                    return obj[key]
        # 递归
        for v in obj.values():
            result = _extract_hot_list(v)
            if result:
                return result
    elif isinstance(obj, list):
        for item in obj:
            result = _extract_hot_list(item)
            if result:
                return result
    return []
