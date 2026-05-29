"""MCP 数据源封装 — 将各平台 MCP 工具结果转换为统一格式

优先级：MCP Server → 爬虫降级
每个平台的 MCP 工具映射到统一的热搜/内容数据结构
"""

from __future__ import annotations

import logging
import re
from typing import Any

from mcp_clients.manager import get_mcp_manager

logger = logging.getLogger(__name__)


# ── B站 MCP 数据源 (mr-house/bilibili-mcp-server, general_search) ──

def _parse_bilibili_search(result: dict, limit: int = 30) -> list[dict]:
    """解析 bilibili_api web_search 返回结构
    result 结构: {"result": [{"result_type": "video", "data": [video_dict, ...]}, ...]}
    """
    if not isinstance(result, dict):
        return []
    items = []
    for group in result.get("result", []):
        if group.get("result_type") != "video":
            continue
        for v in group.get("data", []):
            if not isinstance(v, dict):
                continue
            title = re.sub(r"<[^>]+>", "", str(v.get("title", "")))
            if not title:
                continue
            items.append({
                "keyword": title,
                "heat_score": v.get("play", 0) or 0,
                "author": v.get("author", v.get("uname", "")),
                "url": v.get("arcurl", v.get("url", "")),
                "bvid": v.get("bvid", ""),
                "duration": v.get("duration", ""),
                "description": v.get("description", ""),
                "source": "mcp",
            })
            if len(items) >= limit:
                return items
    return items


async def bilibili_hot_via_mcp(limit: int = 30) -> list[dict]:
    """通过 B站 MCP general_search 获取热门内容"""
    mcp = get_mcp_manager()
    result = await mcp.call("bilibili", "general_search", {"keyword": "B站每日热门"})
    if not result:
        return []

    results = _parse_bilibili_search(result, limit)
    if results:
        logger.info(f"[B站MCP] 获取到 {len(results)} 条热门")
    return results


async def bilibili_search_via_mcp(keyword: str, limit: int = 20) -> list[dict]:
    """通过 B站 MCP general_search 搜索视频"""
    mcp = get_mcp_manager()
    result = await mcp.call("bilibili", "general_search", {"keyword": keyword})
    if not result:
        return []

    return _parse_bilibili_search(result, limit)


# ── 抖音 MCP 数据源 ───────────────────────────────────────

async def douyin_video_info_via_mcp(share_url: str) -> dict | None:
    """通过抖音 MCP 解析视频信息"""
    mcp = get_mcp_manager()
    result = await mcp.call("douyin", "parse_douyin_video_info", {"url": share_url})
    if result:
        return {**result, "source": "mcp"}
    return None


async def douyin_extract_text_via_mcp(share_url: str) -> str | None:
    """通过抖音 MCP 提取视频文案"""
    mcp = get_mcp_manager()
    result = await mcp.call("douyin", "extract_douyin_text", {"url": share_url})
    if isinstance(result, str):
        return result
    if isinstance(result, dict):
        return result.get("text", result.get("content", str(result)))
    return str(result) if result else None


# ── 小红书 MCP 数据源 ─────────────────────────────────────

async def xiaohongshu_search_via_mcp(keyword: str, limit: int = 20) -> list[dict]:
    """通过小红书 MCP 搜索内容"""
    mcp = get_mcp_manager()
    result = await mcp.call("xiaohongshu", "search_feeds", {"keyword": keyword})
    if not result:
        return []

    feeds = _extract_list(result)
    results = []
    for f in feeds[:limit]:
        results.append({
            "keyword": f.get("title", f.get("desc", "")),
            "heat_score": f.get("liked_count", f.get("likes", 0)),
            "author": f.get("nickname", f.get("author", "")),
            "url": f.get("url", ""),
            "feed_id": f.get("feed_id", f.get("id", "")),
            "source": "mcp",
        })
    if results:
        logger.info(f"[小红书MCP] 搜索「{keyword}」得到 {len(results)} 条")
    return results


async def xiaohongshu_recommend_via_mcp(limit: int = 30) -> list[dict]:
    """通过小红书 MCP 获取推荐列表"""
    mcp = get_mcp_manager()
    result = await mcp.call("xiaohongshu", "list_feeds", {})
    if not result:
        return []

    feeds = _extract_list(result)
    results = []
    for f in feeds[:limit]:
        results.append({
            "keyword": f.get("title", f.get("desc", "")),
            "heat_score": f.get("liked_count", f.get("likes", 0)),
            "author": f.get("nickname", f.get("author", "")),
            "url": f.get("url", ""),
            "source": "mcp",
        })
    if results:
        logger.info(f"[小红书MCP] 获取到 {len(results)} 条推荐")
    return results


# ── 微博 MCP 数据源 ───────────────────────────────────────

async def weibo_hot_via_mcp(limit: int = 30) -> list[dict]:
    """通过微博 MCP get_trendings 获取热搜"""
    mcp = get_mcp_manager()

    # 优先用 get_trendings（热搜榜）
    result = await mcp.call("weibo", "get_trendings", {"limit": limit})
    if result:
        items = _extract_list(result)
        if not items and isinstance(result, dict):
            # 可能结果在某个 key 下
            for key in ("trendings", "data", "result", "items"):
                if key in result:
                    items = _extract_list(result[key])
                    if items:
                        break
        if items:
            results = []
            for item in items[:limit]:
                if isinstance(item, dict):
                    # 微博 MCP 返回结构: {description, trending, url}
                    keyword = item.get("description", item.get("title", item.get("word", item.get("keyword", item.get("name", "")))))
                    heat_score = item.get("trending", item.get("num", item.get("hot_value", item.get("heat", item.get("count", 0)))))
                    if keyword:
                        results.append({
                            "keyword": keyword,
                            "heat_score": heat_score,
                            "url": item.get("url", item.get("link", "")),
                            "source": "mcp",
                        })
                elif isinstance(item, str):
                    results.append({"keyword": item, "heat_score": 0, "source": "mcp"})
            if results:
                logger.info(f"[微博MCP] 获取到 {len(results)} 条热搜")
                return results

    # 降级: get_hot_feeds
    result = await mcp.call("weibo", "get_hot_feeds", {})
    if result:
        items = _extract_list(result)
        if items:
            results = []
            for item in items[:limit]:
                if isinstance(item, dict):
                    results.append({
                        "keyword": item.get("text", item.get("title", ""))[:50],
                        "heat_score": item.get("reposts_count", item.get("attitudes_count", 0)),
                        "url": item.get("url", ""),
                        "source": "mcp",
                    })
            if results:
                logger.info(f"[微博MCP] 通过 hot_feeds 获取到 {len(results)} 条")
                return results

    logger.warning("[微博MCP] 热搜获取失败")
    return []


# ── 工具函数 ──────────────────────────────────────────────

def _extract_list(data: Any) -> list:
    """从 MCP 返回结果中提取列表数据"""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        # 常见的嵌套 key
        for key in ("data", "items", "list", "results", "videos", "feeds", "hot_search",
                     "realtime", "result", "content"):
            val = data.get(key)
            if isinstance(val, list):
                return val
            if isinstance(val, dict):
                # 再嵌套一层
                for key2 in ("items", "list", "data", "results"):
                    v2 = val.get(key2)
                    if isinstance(v2, list):
                        return v2
    return []
