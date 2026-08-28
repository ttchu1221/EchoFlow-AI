from __future__ import annotations

import asyncio
import html
import logging
import re
from urllib.parse import parse_qs, unquote, urlparse

logger = logging.getLogger(__name__)


async def fetch_keyword_content(platform: str, keyword: str, limit: int = 20) -> list[dict]:
    """按关键词搜索平台内容。

    用于品牌、产品、话题等非账号类问题，例如“找珀莱雅在抖音相关内容”。
    """
    keyword = (keyword or "").strip()
    if not keyword:
        return []

    if platform == "douyin":
        from competitor.crawler import fetch_competitor_content

        items = await fetch_competitor_content(platform, keyword, keyword, limit)
        if not items:
            items = await _fetch_douyin_via_web_search(keyword, limit)
    elif platform == "xiaohongshu":
        from crawlers.xiaohongshu import fetch_trending_notes

        items = await fetch_trending_notes(keyword, limit)
    elif platform == "bilibili":
        from crawlers.bilibili import search_videos

        items = await search_videos(keyword, page=1, page_size=limit)
    else:
        logger.warning(f"[关键词采集] 暂不支持平台: {platform}")
        return []

    normalized = []
    for item in items[:limit]:
        normalized.append({
            **item,
            "platform": platform,
            "keyword": keyword,
            "search_keyword": keyword,
            "entity_type": "content",
        })
    return normalized


async def _fetch_douyin_via_web_search(keyword: str, limit: int = 20) -> list[dict]:
    """抖音搜索 API 无结果时，通过搜索引擎抓取公开结果页兜底。"""
    import httpx

    query = f"site:douyin.com/video {keyword} 抖音"
    resp = None
    search_urls = (
        "https://duckduckgo.com/html/",
        "https://html.duckduckgo.com/html/",
        "https://lite.duckduckgo.com/lite/",
    )
    try:
        async with httpx.AsyncClient(
            timeout=12,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0"},
        ) as client:
            for attempt in range(1):
                for search_url in search_urls:
                    resp = await client.get(search_url, params={"q": query})
                    if resp.status_code == 202:
                        logger.info(f"[关键词采集-抖音] 搜索兜底返回 202，准备重试: {search_url}")
                        continue
                    if resp.status_code >= 400:
                        logger.warning(f"[关键词采集-抖音] 搜索兜底失败 HTTP {resp.status_code}: {search_url}")
                        continue
                    if "result__a" in resp.text or "douyin.com/video" in resp.text:
                        break
                if resp is not None and resp.status_code < 400 and resp.status_code != 202:
                    break
                await asyncio.sleep(1 + attempt)
    except Exception as e:
        logger.warning(f"[关键词采集-抖音] 搜索兜底请求失败: {e}")
        return []

    if resp is None or resp.status_code >= 400 or resp.status_code == 202:
        logger.warning("[关键词采集-抖音] 搜索兜底未返回可解析页面")
        return []

    results = []
    seen = set()
    for match in re.finditer(r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>', resp.text, re.S):
        raw_url, raw_title = match.groups()
        url = _unwrap_duckduckgo_url(html.unescape(raw_url))
        title = _clean_html(raw_title)
        _append_douyin_result(results, seen, keyword, url, title, limit)
        if len(results) >= limit:
            break

    if not results:
        text = html.unescape(resp.text)
        for url in re.findall(r"https?://(?:www\.)?douyin\.com/video/[0-9A-Za-z_-]+", text):
            _append_douyin_result(results, seen, keyword, url, f"{keyword} - 抖音", limit)
            if len(results) >= limit:
                break

    if results:
        logger.info(f"[关键词采集-抖音] 搜索兜底「{keyword}」获取到 {len(results)} 条")
    return results


def _append_douyin_result(results: list[dict], seen: set[str], keyword: str, url: str, title: str, limit: int):
    if "douyin.com/video" not in url or url in seen:
        return
    if keyword not in title and keyword not in url:
        return
    seen.add(url)
    video_id = url.rstrip("/").split("/")[-1]
    results.append({
        "platform_content_id": video_id,
        "title": title[:120],
        "description": title,
        "url": url,
        "content_url": url,
        "source_note": "web_search_fallback",
    })


def _unwrap_duckduckgo_url(url: str) -> str:
    if url.startswith("//"):
        url = "https:" + url
    parsed = urlparse(url)
    if "duckduckgo.com" in parsed.netloc:
        target = parse_qs(parsed.query).get("uddg", [""])[0]
        if target:
            return unquote(target)
    return url


def _clean_html(text: str) -> str:
    text = re.sub(r"<.*?>", "", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()
