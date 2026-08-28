"""统一数据源 — MCP Server 优先 + 爬虫降级 + 缓存

数据获取优先级：
1. MCP Server（最稳定，结构化数据）
2. 平台原生 API（B站等公开接口）
3. 聚合平台 tophub.today（兜底）
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from crawlers.base import CrawlerClient

logger = logging.getLogger(__name__)

# ── 缓存 ──────────────────────────────────────────────────

class TTLCache:
    def __init__(self, default_ttl: int = 600):
        self._store: dict[str, tuple[float, Any]] = {}
        self._default_ttl = default_ttl

    def get(self, key: str) -> Any | None:
        if key in self._store:
            ts, val = self._store[key]
            if time.time() - ts < self._default_ttl:
                return val
            del self._store[key]
        return None

    def set(self, key: str, value: Any, ttl: int | None = None):
        self._store[key] = (time.time(), value)

    def clear(self):
        self._store.clear()


_cache = TTLCache(default_ttl=600)


# ── 聚合平台: tophub.today ────────────────────────────────

_TOPHUB_NODES = {
    "bilibili": "3",
    "douyin": "2",
    "xiaohongshu": "4",
    "weibo": "1",
}


async def _fetch_tophub_node(node_id: str, platform_name: str, limit: int = 30) -> list[dict]:
    """从 tophub.today 获取指定平台的热榜"""
    cache_key = f"tophub_{platform_name}"
    cached = _cache.get(cache_key)
    if cached:
        return cached[:limit]

    try:
        async with CrawlerClient(base_delay=0.3, max_retries=1, timeout=8.0) as client:
            data = await client.get(
                f"https://tophub.today/api/nodes/{node_id}",
                referer="https://tophub.today",
            )
            if not data:
                return []

            items = []
            if isinstance(data, dict):
                if "data" in data:
                    d = data["data"]
                    if isinstance(d, list):
                        items = d
                    elif isinstance(d, dict):
                        items = d.get("items", d.get("list", []))
            elif isinstance(data, list):
                items = data

            import re
            results = []
            for item in items[:limit]:
                if not isinstance(item, dict):
                    continue
                title = item.get("title", item.get("name", item.get("content", "")))
                if not title:
                    continue
                hot_val = 0
                extra = item.get("extra")
                if isinstance(extra, dict):
                    hot_val = extra.get("hot_value", extra.get("pv", 0))
                elif isinstance(extra, str):
                    m = re.match(r"(\d+)", extra.replace(",", ""))
                    if m:
                        hot_val = int(m.group(1))

                results.append({
                    "keyword": title.strip(),
                    "heat_score": hot_val,
                    "url": item.get("url", ""),
                })

            if results:
                _cache.set(cache_key, results)
                logger.info(f"[tophub] {platform_name} 获取到 {len(results)} 条热搜")
            return results

    except Exception as e:
        logger.warning(f"[tophub] {platform_name} 获取失败: {e}")
    return []


# ── 平台原生数据源 ────────────────────────────────────────

async def _fetch_bilibili_native(limit: int = 30) -> list[dict]:
    """B站原生 API 热搜"""
    cache_key = "bilibili_native"
    cached = _cache.get(cache_key)
    if cached:
        return cached[:limit]

    try:
        async with CrawlerClient(base_delay=0.5) as client:
            data = await client.get(
                "https://s.search.bilibili.com/main/hotword",
                referer="https://www.bilibili.com",
            )
            if data and "list" in data:
                results = []
                for item in data["list"][:limit]:
                    results.append({
                        "keyword": item.get("keyword", item.get("show_name", "")),
                        "heat_score": item.get("heat_score", 0),
                        "url": f"https://search.bilibili.com/all?keyword={item.get('keyword', '')}",
                    })
                if results:
                    _cache.set(cache_key, results)
                    logger.info(f"[B站原生] 获取到 {len(results)} 条热搜")
                    return results
    except Exception as e:
        logger.warning(f"[B站原生] 获取失败: {e}")
    return []


async def _fetch_weibo_native(limit: int = 30) -> list[dict]:
    """微博原生 API 热搜"""
    cache_key = "weibo_native"
    cached = _cache.get(cache_key)
    if cached:
        return cached[:limit]

    try:
        async with CrawlerClient(base_delay=1.0, max_retries=2) as client:
            data = await client.get(
                "https://weibo.com/ajax/side/hotSearch",
                referer="https://weibo.com",
            )
            if data and data.get("data", {}).get("realtime"):
                results = []
                for item in data["data"]["realtime"][:limit]:
                    word = item.get("word", "")
                    if not word:
                        continue
                    results.append({
                        "keyword": word,
                        "heat_score": item.get("num", item.get("raw_hot", 0)),
                        "label": item.get("label_name", ""),
                        "url": f"https://s.weibo.com/weibo?q=%23{word}%23",
                    })
                if results:
                    _cache.set(cache_key, results)
                    logger.info(f"[微博原生] 获取到 {len(results)} 条热搜")
                    return results
    except Exception as e:
        logger.warning(f"[微博原生] 获取失败: {e}")
    return []


async def _fetch_douyin_native(limit: int = 30) -> list[dict]:
    """抖音原生 API 热搜（先获取临时 Cookie）"""
    cache_key = "douyin_native"
    cached = _cache.get(cache_key)
    if cached:
        return cached[:limit]

    try:
        async with CrawlerClient(base_delay=1.0, max_retries=2) as client:
            # 先访问主页获取 __ac_nonce Cookie
            await client.get_html("https://www.douyin.com/", referer="https://www.douyin.com/")
            # 调用热搜 API
            data = await client.get(
                "https://www.douyin.com/aweme/v1/web/hot/search/list/",
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
                        "url": f"https://www.douyin.com/search/{item.get('word', '')}",
                    })
                if results:
                    _cache.set(cache_key, results)
                    logger.info(f"[抖音原生] 获取到 {len(results)} 条热搜")
                    return results
    except Exception as e:
        logger.warning(f"[抖音原生] 获取失败: {e}")
    return []


async def _fetch_xiaohongshu_native(limit: int = 30) -> list[dict]:
    """小红书 SSR 页面解析推荐内容"""
    cache_key = "xiaohongshu_native"
    cached = _cache.get(cache_key)
    if cached:
        return cached[:limit]

    try:
        import re as _re, json as _json

        async with CrawlerClient(base_delay=1.0, max_retries=2) as client:
            html = await client.get_html(
                "https://www.xiaohongshu.com/explore",
                referer="https://www.xiaohongshu.com",
            )
            if not html:
                return []

            match = _re.search(
                r'window\.__INITIAL_STATE__\s*=\s*({.+?})\s*</script>',
                html, _re.DOTALL,
            )
            if not match:
                return []

            raw = match.group(1).replace('undefined', 'null')
            data = _json.loads(raw)
            feeds = data.get("feed", {}).get("feeds", [])
            if not feeds:
                return []

            results = []
            for f in feeds[:limit]:
                nc = f.get("noteCard", {})
                title = nc.get("displayTitle", "")
                if not title:
                    continue
                likes_str = nc.get("interactInfo", {}).get("likedCount", "0")
                heat = _parse_count(likes_str)
                results.append({
                    "keyword": title,
                    "heat_score": heat,
                    "author": nc.get("user", {}).get("nickname", ""),
                    "url": f"https://www.xiaohongshu.com/explore/{f.get('id', '')}",
                })

            if results:
                _cache.set(cache_key, results)
                logger.info(f"[小红书原生] SSR 解析获取到 {len(results)} 条推荐内容")
                return results
    except Exception as e:
        logger.warning(f"[小红书原生] 获取失败: {e}")
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


# ── MCP 数据源（优先级最高）────────────────────────────────

async def _fetch_via_mcp(platform: str, limit: int = 30) -> list[dict]:
    """通过 MCP Server 获取数据"""
    try:
        from mcp_clients.sources import (
            bilibili_hot_via_mcp,
            weibo_hot_via_mcp,
            xiaohongshu_recommend_via_mcp,
        )

        mcp_fetchers = {
            "bilibili": lambda: bilibili_hot_via_mcp(limit),
            "weibo": lambda: weibo_hot_via_mcp(limit),
            "xiaohongshu": lambda: xiaohongshu_recommend_via_mcp(limit),
            # 抖音 MCP 主要是视频解析，不做热搜
        }

        fetcher = mcp_fetchers.get(platform)
        if not fetcher:
            return []

        results = await fetcher()
        if results:
            logger.info(f"[MCP] {platform} 获取到 {len(results)} 条数据")
        return results

    except ImportError:
        logger.debug("[MCP] mcp_clients 模块未安装，跳过")
        return []
    except Exception as e:
        logger.warning(f"[MCP] {platform} 获取失败: {e}")
        return []


# ── 统一入口 ──────────────────────────────────────────────

async def fetch_hot_search(platform: str, limit: int = 30) -> list[dict]:
    """获取指定平台热搜 — MCP 优先 → 原生 API → tophub 兜底

    Args:
        platform: bilibili / douyin / xiaohongshu / weibo
        limit: 返回条数

    Returns:
        [{"keyword": "...", "heat_score": 123, "url": "..."}]
    """
    cache_key = f"hot_{platform}_{limit}"
    cached = _cache.get(cache_key)
    if cached:
        return cached

    results = []

    # 层级1: MCP Server
    results = await _fetch_via_mcp(platform, limit)
    if results:
        _cache.set(cache_key, results)
        return results

    # 层级2: 平台原生 API。抖音优先只走原生接口，避免失效聚合节点产生误导性 404。
    tasks = []

    if platform == "bilibili":
        tasks.append(_fetch_bilibili_native(limit))
    elif platform == "weibo":
        tasks.append(_fetch_weibo_native(limit))
    elif platform == "douyin":
        tasks.append(_fetch_douyin_native(limit))
    elif platform == "xiaohongshu":
        tasks.append(_fetch_xiaohongshu_native(limit))

    node_id = _TOPHUB_NODES.get(platform)
    if node_id and platform != "douyin":
        tasks.append(_fetch_tophub_node(node_id, platform, limit))

    if tasks:
        # 用 as_completed 遍历所有结果，任一成功即返回
        async_tasks = [asyncio.create_task(t) for t in tasks]
        try:
            for coro in asyncio.as_completed(async_tasks, timeout=15.0):
                try:
                    r = await coro
                    if r and len(r) > len(results):
                        results = r
                        break  # 有有效数据就立即返回
                except Exception:
                    continue
        except (asyncio.TimeoutError, TimeoutError):
            logger.warning(f"[数据源] {platform} 所有请求超时")
        finally:
            # 取消剩余未完成的任务，避免资源泄漏
            for t in async_tasks:
                if not t.done():
                    t.cancel()

    if results:
        # 按热度降序排序
        results.sort(key=lambda x: x.get("heat_score", 0), reverse=True)
        _cache.set(cache_key, results)
        logger.info(f"[数据源] {platform} 最终获取 {len(results)} 条热搜")
    else:
        logger.warning(f"[数据源] {platform} 所有数据源均失败")

    return results


async def fetch_platform_popular(platform: str, limit: int = 20) -> list[dict]:
    """获取平台热门内容详情（目前仅支持 bilibili）"""
    if platform != "bilibili":
        return []

    cache_key = f"popular_{platform}_{limit}"
    cached = _cache.get(cache_key)
    if cached:
        return cached

    results = []

    # MCP 优先
    try:
        from mcp_clients.sources import bilibili_hot_via_mcp
        results = await bilibili_hot_via_mcp(limit)
    except Exception:
        pass

    # 原生 API 降级
    if not results:
        results = await _fetch_bilibili_popular(limit)

    if results:
        _cache.set(cache_key, results)
    return results


async def _fetch_bilibili_popular(limit: int = 20) -> list[dict]:
    """B站热门视频（原生 API）"""
    try:
        async with CrawlerClient(base_delay=0.5) as client:
            data = await client.get(
                "https://api.bilibili.com/x/web-interface/popular",
                params={"ps": str(limit), "pn": "1"},
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
                        "tname": v.get("tname", ""),
                        "url": f"https://www.bilibili.com/video/{v.get('bvid', '')}",
                    })
                logger.info(f"[B站] 获取到 {len(results)} 条热门视频")
                return results
    except Exception as e:
        logger.warning(f"[B站] 热门视频获取失败: {e}")
    return []


def clear_cache():
    """清空缓存"""
    _cache.clear()
    logger.info("[数据源] 缓存已清空")
