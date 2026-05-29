"""B站爬虫 — 基于公开API获取热搜、排行榜、视频详情"""

from __future__ import annotations

import logging
from typing import Any

from crawlers.base import CrawlerClient

logger = logging.getLogger(__name__)

# B站公开 API（无需登录）
_BASE = "https://api.bilibili.com"
_SEARCH_BASE = "https://s.search.bilibili.com"


async def fetch_hot_search(limit: int = 30) -> list[dict]:
    """获取B站热搜词"""
    async with CrawlerClient(base_delay=0.5) as client:
        # 方式1: 搜索热词接口
        data = await client.get(
            f"{_SEARCH_BASE}/main/hotword",
            referer="https://www.bilibili.com",
        )
        if data and "list" in data:
            results = []
            for item in data["list"][:limit]:
                results.append({
                    "keyword": item.get("keyword", item.get("show_name", "")),
                    "heat_score": item.get("heat_score", item.get("hot_id", 0)),
                    "icon": item.get("icon", ""),
                    "url": f"https://search.bilibili.com/all?keyword={item.get('keyword', '')}",
                })
            if results:
                logger.info(f"[B站] 获取到 {len(results)} 条热搜")
                return results

        # 方式2: 搜索推荐接口
        data = await client.get(
            f"{_BASE}/x/web-interface/wbi/search/square",
            params={"limit": str(limit)},
            referer="https://www.bilibili.com",
        )
        if data and data.get("data", {}).get("trending", {}).get("list"):
            results = []
            for item in data["data"]["trending"]["list"][:limit]:
                results.append({
                    "keyword": item.get("keyword", ""),
                    "heat_score": item.get("heat_score", 0),
                    "icon": item.get("icon", ""),
                    "url": f"https://search.bilibili.com/all?keyword={item.get('keyword', '')}",
                })
            logger.info(f"[B站] 获取到 {len(results)} 条热搜(wbi)")
            return results

    logger.warning("[B站] 热搜获取失败")
    return []


async def fetch_popular_videos(page: int = 1, page_size: int = 20) -> list[dict]:
    """获取B站热门视频排行榜"""
    async with CrawlerClient(base_delay=0.5) as client:
        data = await client.get(
            f"{_BASE}/x/web-interface/popular",
            params={"ps": str(page_size), "pn": str(page)},
            referer="https://www.bilibili.com",
        )
        if data and data.get("data", {}).get("list"):
            results = []
            for v in data["data"]["list"]:
                stat = v.get("stat", {})
                results.append({
                    "bvid": v.get("bvid", ""),
                    "title": v.get("title", ""),
                    "author": v.get("owner", {}).get("name", ""),
                    "view": stat.get("view", 0),
                    "like": stat.get("like", 0),
                    "coin": stat.get("coin", 0),
                    "favorite": stat.get("favorite", 0),
                    "share": stat.get("share", 0),
                    "comment": stat.get("reply", 0),
                    "duration": v.get("duration", 0),
                    "desc": v.get("desc", ""),
                    "cover": v.get("pic", ""),
                    "tname": v.get("tname", ""),
                    "pubdate": v.get("pubdate", 0),
                    "url": f"https://www.bilibili.com/video/{v.get('bvid', '')}",
                })
            logger.info(f"[B站] 获取到 {len(results)} 条热门视频")
            return results
    return []


async def fetch_ranking(rid: int = 0, day: int = 3) -> list[dict]:
    """获取B站排行榜 (rid: 0全榜, day: 3三日/7一周)"""
    async with CrawlerClient(base_delay=0.5) as client:
        data = await client.get(
            f"{_BASE}/x/web-interface/ranking/v2",
            params={"rid": str(rid), "type": "all"},
            referer="https://www.bilibili.com",
        )
        if data and data.get("data", {}).get("list"):
            results = []
            for i, v in enumerate(data["data"]["list"][:30]):
                stat = v.get("stat", {})
                results.append({
                    "rank": i + 1,
                    "bvid": v.get("bvid", ""),
                    "title": v.get("title", ""),
                    "author": v.get("owner", {}).get("name", ""),
                    "view": stat.get("view", 0),
                    "like": stat.get("like", 0),
                    "score": v.get("score", 0),
                    "tname": v.get("tname", ""),
                    "url": f"https://www.bilibili.com/video/{v.get('bvid', '')}",
                })
            logger.info(f"[B站] 获取到 {len(results)} 条排行榜")
            return results
    return []


async def fetch_video_detail(bvid: str) -> dict | None:
    """获取B站视频详情"""
    async with CrawlerClient(base_delay=0.5) as client:
        data = await client.get(
            f"{_BASE}/x/web-interface/view",
            params={"bvid": bvid},
            referer=f"https://www.bilibili.com/video/{bvid}",
        )
        if data and data.get("data"):
            v = data["data"]
            stat = v.get("stat", {})
            return {
                "bvid": v.get("bvid", ""),
                "title": v.get("title", ""),
                "author": v.get("owner", {}).get("name", ""),
                "view": stat.get("view", 0),
                "like": stat.get("like", 0),
                "coin": stat.get("coin", 0),
                "favorite": stat.get("favorite", 0),
                "share": stat.get("share", 0),
                "comment": stat.get("reply", 0),
                "danmaku": stat.get("danmaku", 0),
                "duration": v.get("duration", 0),
                "desc": v.get("desc", ""),
                "tags": [t.get("tag_name", "") for t in (v.get("tag", []) or [])],
                "tname": v.get("tname", ""),
                "pubdate": v.get("pubdate", 0),
            }
    return None


async def search_videos(keyword: str, page: int = 1, page_size: int = 20) -> list[dict]:
    """搜索B站视频（通过搜索接口）"""
    async with CrawlerClient(base_delay=1.0) as client:
        data = await client.get(
            f"{_BASE}/x/web-interface/search/all/v2",
            params={
                "keyword": keyword,
                "page": str(page),
                "pagesize": str(page_size),
                "search_type": "video",
            },
            referer=f"https://search.bilibili.com/all?keyword={keyword}",
        )
        if data and data.get("data", {}).get("result"):
            results = []
            for group in data["data"]["result"]:
                for v in group.get("data", []) if isinstance(group, dict) else []:
                    results.append({
                        "bvid": v.get("bvid", ""),
                        "title": v.get("title", "").replace("<em class=\"keyword\">", "").replace("</em>", ""),
                        "author": v.get("author", ""),
                        "play": v.get("play", 0),
                        "danmaku": v.get("video_review", 0),
                        "duration": v.get("duration", ""),
                        "desc": v.get("description", ""),
                        "pubdate": v.get("pubdate", 0),
                    })
            logger.info(f"[B站] 搜索「{keyword}」得到 {len(results)} 条结果")
            return results
    return []
