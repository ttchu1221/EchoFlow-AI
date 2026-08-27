from __future__ import annotations

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
    try:
        async with httpx.AsyncClient(
            timeout=20,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0"},
        ) as client:
            resp = await client.get("https://duckduckgo.com/html/", params={"q": query})
            if resp.status_code >= 400:
                logger.warning(f"[关键词采集-抖音] 搜索兜底失败 HTTP {resp.status_code}")
                return []
    except Exception as e:
        logger.warning(f"[关键词采集-抖音] 搜索兜底请求失败: {e}")
        return []

    results = []
    seen = set()
    for match in re.finditer(r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>', resp.text, re.S):
        raw_url, raw_title = match.groups()
        url = _unwrap_duckduckgo_url(html.unescape(raw_url))
        title = _clean_html(raw_title)
        if "douyin.com/video" not in url or url in seen:
            continue
        if keyword not in title and keyword not in url:
            continue
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
        if len(results) >= limit:
            break

    if results:
        logger.info(f"[关键词采集-抖音] 搜索兜底「{keyword}」获取到 {len(results)} 条")
    return results


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
