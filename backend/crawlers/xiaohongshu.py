"""小红书爬虫 — 热搜/趋势抓取（反爬最严格，多策略降级）"""

from __future__ import annotations

import logging
import re
from typing import Any

from crawlers.base import CrawlerClient

logger = logging.getLogger(__name__)

# 小红书热搜 API（移动端接口，需 Cookie）
_XHS_HOT_API = "https://edith.xiaohongshu.com/api/sns/v1/search/hot_list"
# 小红书网页版
_XHS_WEB = "https://www.xiaohongshu.com"
# 聚合平台备用
_TOPHUB_DIANPING = "https://tophub.today/n/Y2KeDGQdNP"  # 小红书热榜


async def fetch_hot_search(limit: int = 30) -> list[dict]:
    """获取小红书热搜榜

    策略（小红书反爬最严，需多级降级）：
    1. 尝试移动端 API（需要有效 Cookie）
    2. 解析网页版 SSR 数据
    3. fallback 到聚合平台
    """
    # 方式1: 移动端 API
    results = await _fetch_from_api(limit)
    if results:
        return results

    # 方式2: 网页解析
    results = await _fetch_from_web(limit)
    if results:
        return results

    # 方式3: 聚合平台
    results = await _fetch_from_tophub(limit)
    if results:
        return results

    logger.warning("[小红书] 所有热搜获取方式均失败")
    return []


async def fetch_trending_notes(keyword: str, limit: int = 20) -> list[dict]:
    """搜索小红书热门笔记（通过网页搜索）"""
    try:
        async with CrawlerClient(base_delay=3.0, max_retries=2) as client:
            # 小红书搜索页
            search_url = f"{_XHS_WEB}/search_result?keyword={keyword}&source=web_search_result_notes"
            extra_headers = {
                "Referer": "https://www.xiaohongshu.com",
                "Origin": "https://www.xiaohongshu.com",
            }
            html = await client.get_html(
                search_url,
                headers=extra_headers,
                referer="https://www.xiaohongshu.com",
            )
            if not html:
                return []

            # 尝试从 SSR 数据提取
            notes = _parse_notes_from_html(html, limit)
            if notes:
                logger.info(f"[小红书] 搜索「{keyword}」得到 {len(notes)} 条笔记")
                return notes

    except Exception as e:
        logger.warning(f"[小红书] 搜索失败: {e}")
    return []


async def _fetch_from_api(limit: int) -> list[dict]:
    """通过小红书移动端 API 获取热搜（需要 Cookie，通常会失败）"""
    try:
        async with CrawlerClient(base_delay=2.0, max_retries=1) as client:
            extra_headers = {
                "Referer": "https://www.xiaohongshu.com",
                "Origin": "https://www.xiaohongshu.com",
                "X-Requested-With": "XMLHttpRequest",
            }
            data = await client.get(
                _XHS_HOT_API,
                headers=extra_headers,
                params={"source": "web_explore_feed"},
                referer="https://www.xiaohongshu.com",
            )
            if data and data.get("data"):
                items = data["data"] if isinstance(data["data"], list) else []
                results = []
                for item in items[:limit]:
                    results.append({
                        "keyword": item.get("title", item.get("name", "")),
                        "heat_score": item.get("score", item.get("hot_value", 0)),
                        "icon": item.get("icon", ""),
                        "url": f"https://www.xiaohongshu.com/search_result?keyword={item.get('title', '')}",
                    })
                if results:
                    logger.info(f"[小红书] API 获取到 {len(results)} 条热搜")
                    return results
    except Exception as e:
        logger.debug(f"[小红书] API 获取失败（预期中）: {e}")
    return []


async def _fetch_from_web(limit: int) -> list[dict]:
    """从小红书网页版 SSR 数据解析推荐内容"""
    try:
        async with CrawlerClient(base_delay=2.0, max_retries=2) as client:
            html = await client.get_html(
                f"{_XHS_WEB}/explore",
                referer="https://www.xiaohongshu.com",
            )
            if not html:
                return []

            # 提取 SSR 初始数据
            match = re.search(
                r'window\.__INITIAL_STATE__\s*=\s*({.+?})\s*</script>',
                html, re.DOTALL,
            )
            if not match:
                return []

            import json
            raw = match.group(1).replace('undefined', 'null')
            data = json.loads(raw)

            # 从 feed.feeds 提取推荐笔记（SSR 首屏数据）
            feeds = data.get("feed", {}).get("feeds", [])
            if feeds:
                results = []
                for f in feeds[:limit]:
                    nc = f.get("noteCard", {})
                    title = nc.get("displayTitle", "")
                    if not title:
                        continue
                    user = nc.get("user", {}).get("nickname", "")
                    likes = nc.get("interactInfo", {}).get("likedCount", "0")
                    note_type = nc.get("type", "normal")
                    note_id = f.get("id", "")
                    # 解析点赞数
                    heat = _parse_count(likes)
                    results.append({
                        "keyword": title,
                        "heat_score": heat,
                        "author": user,
                        "note_type": note_type,
                        "note_id": note_id,
                        "url": f"https://www.xiaohongshu.com/explore/{note_id}" if note_id else "",
                    })
                if results:
                    logger.info(f"[小红书] SSR 解析获取到 {len(results)} 条推荐内容")
                    return results

    except Exception as e:
        logger.warning(f"[小红书] 网页解析失败: {e}")
    return []


def _parse_count(text: str) -> int:
    """解析 '6.5万' 这种格式的数字"""
    if not text or not isinstance(text, str):
        return 0
    text = text.strip()
    try:
        if "万" in text:
            return int(float(text.replace("万", "")) * 10000)
        if "亿" in text:
            return int(float(text.replace("亿", "")) * 100000000)
        return int(float(text))
    except (ValueError, TypeError):
        return 0


async def _fetch_from_tophub(limit: int) -> list[dict]:
    """从聚合平台获取小红书热榜（最可靠的兜底方案）"""
    try:
        async with CrawlerClient(base_delay=1.0, max_retries=2) as client:
            # tophub.today 的小红书热榜
            data = await client.get(
                "https://tophub.today/api/nodes/4",
                referer="https://tophub.today",
            )
            if data and isinstance(data, dict):
                items = data.get("data", [])
                if isinstance(items, dict):
                    items = items.get("items", [])
                results = []
                for item in items[:limit]:
                    if isinstance(item, dict):
                        results.append({
                            "keyword": item.get("title", item.get("name", "")),
                            "heat_score": item.get("extra", {}).get("hot_value", 0) if isinstance(item.get("extra"), dict) else 0,
                            "url": item.get("url", ""),
                        })
                if results:
                    logger.info(f"[小红书] tophub 获取到 {len(results)} 条热搜")
                    return results

    except Exception as e:
        logger.warning(f"[小红书] tophub 获取失败: {e}")
    return []


def _parse_notes_from_html(html: str, limit: int) -> list[dict]:
    """从 HTML 中解析笔记数据"""
    results = []
    # 尝试匹配笔记卡片
    note_blocks = re.findall(
        r'<section[^>]*class="note-item[^"]*"[^>]*>(.*?)</section>',
        html, re.DOTALL,
    )
    for block in note_blocks[:limit]:
        title_match = re.search(r'class="title"[^>]*>([^<]+)', block)
        author_match = re.search(r'class="author"[^>]*>([^<]+)', block)
        likes_match = re.search(r'class="like[^"]*"[^>]*>([^<]+)', block)
        if title_match:
            results.append({
                "title": title_match.group(1).strip(),
                "author": author_match.group(1).strip() if author_match else "",
                "likes": likes_match.group(1).strip() if likes_match else "0",
            })
    return results

