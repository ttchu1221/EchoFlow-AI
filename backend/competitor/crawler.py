# -*- coding: utf-8 -*-
"""竞品内容自动采集 — 定时爬取竞品账号的最新内容

支持平台：
- bilibili: 通过 B站搜索/空间 API 获取用户视频
- douyin: 通过搜索接口获取用户内容
- xiaohongshu: 通过搜索接口获取用户笔记

采集策略：
- 每次采集获取每个竞品账号最新 10 条内容
- 与已存内容去重（通过 platform_content_id）
- 采集完成后更新竞品账号的 last_checked_at 和 content_count
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from crawlers.base import CrawlerClient

logger = logging.getLogger("echoflow.competitor.crawler")


# ── B站竞品采集 ─────────────────────────────────────────────

async def _fetch_bilibili_user_videos(account_id: str, account_name: str, limit: int = 10) -> list[dict]:
    """获取 B站用户最新投稿视频
    
    account_id: B站 UID 或用户名
    account_name: 用户昵称（用于搜索降级）
    """
    results = []

    # 方式1: 通过 space API（公开）
    try:
        async with CrawlerClient(base_delay=1.0, max_retries=2) as client:
            data = await client.get(
                "https://api.bilibili.com/x/space/wbi/arc/search",
                params={
                    "mid": account_id,
                    "ps": str(limit),
                    "pn": "1",
                    "order": "pubdate",
                },
                referer=f"https://space.bilibili.com/{account_id}/video",
            )
            if data and data.get("data", {}).get("list", {}).get("vlist"):
                for v in data["data"]["list"]["vlist"][:limit]:
                    results.append({
                        "platform_content_id": v.get("bvid", ""),
                        "title": v.get("title", ""),
                        "description": v.get("description", ""),
                        "views": v.get("play", 0),
                        "likes": v.get("like", 0),
                        "comments": v.get("comment", 0),
                        "shares": 0,
                        "duration": v.get("length", ""),
                        "cover_url": v.get("pic", ""),
                        "content_url": f"https://www.bilibili.com/video/{v.get('bvid', '')}",
                        "published_at": datetime.fromtimestamp(v.get("created", 0)).isoformat() if v.get("created") else None,
                    })
                if results:
                    logger.info(f"[竞品-B站] UID {account_id} 获取到 {len(results)} 条视频")
                    return results
    except Exception as e:
        logger.warning(f"[竞品-B站] space API 失败: {e}")

    # 方式2: 通过搜索接口（用用户名搜索）
    if account_name:
        try:
            async with CrawlerClient(base_delay=1.5, max_retries=2) as client:
                data = await client.get(
                    "https://api.bilibili.com/x/web-interface/search/type",
                    params={
                        "keyword": account_name,
                        "search_type": "video",
                        "page": "1",
                        "pagesize": str(limit),
                        "order": "pubdate",
                    },
                    referer=f"https://search.bilibili.com/video?keyword={account_name}",
                )
                if data and data.get("data", {}).get("result"):
                    for v in data["data"]["result"][:limit]:
                        results.append({
                            "platform_content_id": v.get("bvid", ""),
                            "title": (v.get("title", "")
                                      .replace("<em class=\"keyword\">", "")
                                      .replace("</em>", "")),
                            "description": v.get("description", ""),
                            "views": v.get("play", 0),
                            "likes": v.get("like", 0),
                            "comments": v.get("review", 0),
                            "shares": 0,
                            "content_url": v.get("arcurl", ""),
                            "published_at": datetime.fromtimestamp(v.get("pubdate", 0)).isoformat() if v.get("pubdate") else None,
                        })
                    if results:
                        logger.info(f"[竞品-B站] 搜索「{account_name}」获取到 {len(results)} 条")
                        return results
        except Exception as e:
            logger.warning(f"[竞品-B站] 搜索失败: {e}")

    return results


# ── 抖音竞品采集 ─────────────────────────────────────────────

async def _fetch_douyin_user_content(account_id: str, account_name: str, limit: int = 10) -> list[dict]:
    """获取抖音用户最新内容
    
    策略：通过抖音搜索接口搜索用户名
    """
    results = []

    # 通过 tophub/搜索 获取用户内容（抖音反爬严格，使用搜索降级）
    try:
        async with CrawlerClient(base_delay=2.0, max_retries=2) as client:
            # 搜索用户视频
            data = await client.get(
                "https://www.douyin.com/aweme/v1/web/general/search/single/",
                params={
                    "keyword": account_name or account_id,
                    "search_channel": "aweme_video_web",
                    "sort_type": "0",  # 综合排序
                    "publish_time": "0",
                    "count": str(limit),
                    "device_platform": "webapp",
                    "aid": "6383",
                },
                referer="https://www.douyin.com/search/",
            )
            if data and data.get("data"):
                items = data["data"] if isinstance(data["data"], list) else data.get("data", {}).get("data", [])
                for item in items[:limit]:
                    aweme = item.get("aweme_info", item)
                    if not isinstance(aweme, dict):
                        continue
                    stats = aweme.get("statistics", {})
                    desc = aweme.get("desc", "")
                    aweme_id = aweme.get("aweme_id", "")
                    results.append({
                        "platform_content_id": aweme_id,
                        "title": desc[:100] if desc else "",
                        "description": desc,
                        "views": int(stats.get("play_count", 0)),
                        "likes": int(stats.get("digg_count", 0)),
                        "comments": int(stats.get("comment_count", 0)),
                        "shares": int(stats.get("share_count", 0)),
                        "content_url": f"https://www.douyin.com/video/{aweme_id}" if aweme_id else "",
                        "published_at": None,
                    })
                if results:
                    logger.info(f"[竞品-抖音] 搜索「{account_name}」获取到 {len(results)} 条")
                    return results
    except Exception as e:
        logger.debug(f"[竞品-抖音] 搜索 API 失败（预期中）: {e}")

    # 降级：从 tophub 或页面获取（有限数据）
    logger.info(f"[竞品-抖音] 「{account_name}」暂无法通过 API 获取，跳过")
    return results


# ── 小红书竞品采集 ────────────────────────────────────────────

async def _fetch_xiaohongshu_user_content(account_id: str, account_name: str, limit: int = 10) -> list[dict]:
    """获取小红书用户最新笔记
    
    策略：通过小红书搜索接口搜索用户名
    """
    results = []

    try:
        async with CrawlerClient(base_delay=2.0, max_retries=2) as client:
            # 尝试搜索用户笔记
            html = await client.get_html(
                f"https://www.xiaohongshu.com/search_result?keyword={account_name or account_id}&source=web_search_result_notes",
                referer="https://www.xiaohongshu.com",
            )
            if html:
                import re
                import json as json_mod

                # 提取 SSR 数据
                match = re.search(
                    r'window\.__INITIAL_STATE__\s*=\s*({.+?})\s*</script>',
                    html, re.DOTALL,
                )
                if match:
                    raw = match.group(1).replace('undefined', 'null')
                    data = json_mod.loads(raw)
                    feeds = data.get("search", {}).get("feeds", [])
                    for f in feeds[:limit]:
                        nc = f.get("noteCard", f)
                        note_id = f.get("id", nc.get("noteId", ""))
                        title = nc.get("displayTitle", nc.get("title", ""))
                        interact = nc.get("interactInfo", {})
                        results.append({
                            "platform_content_id": note_id,
                            "title": title,
                            "description": nc.get("desc", ""),
                            "views": 0,
                            "likes": _parse_xhs_count(interact.get("likedCount", "0")),
                            "comments": _parse_xhs_count(interact.get("commentCount", "0")),
                            "shares": 0,
                            "content_url": f"https://www.xiaohongshu.com/explore/{note_id}" if note_id else "",
                            "published_at": None,
                        })
                    if results:
                        logger.info(f"[竞品-小红书] 搜索「{account_name}」获取到 {len(results)} 条笔记")
                        return results
    except Exception as e:
        logger.debug(f"[竞品-小红书] 搜索失败: {e}")

    logger.info(f"[竞品-小红书] 「{account_name}」暂无法获取，跳过")
    return results


def _parse_xhs_count(text) -> int:
    """解析小红书的数字格式（如 '6.5万'）"""
    if isinstance(text, (int, float)):
        return int(text)
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


# ── 统一采集入口 ─────────────────────────────────────────────

_PLATFORM_FETCHERS = {
    "bilibili": _fetch_bilibili_user_videos,
    "douyin": _fetch_douyin_user_content,
    "xiaohongshu": _fetch_xiaohongshu_user_content,
}


async def fetch_competitor_content(
    platform: str,
    account_id: str,
    account_name: str = "",
    limit: int = 10,
) -> list[dict]:
    """根据平台类型获取竞品内容"""
    fetcher = _PLATFORM_FETCHERS.get(platform)
    if not fetcher:
        logger.warning(f"[竞品采集] 不支持的平台: {platform}")
        return []
    return await fetcher(account_id, account_name, limit)


async def crawl_all_competitors() -> dict:
    """采集所有竞品账号的最新内容（定时任务入口）
    
    返回: {"total_accounts": N, "new_content": M, "errors": E}
    """
    from memory import db
    if db is None:
        logger.warning("[竞品采集] MongoDB 未初始化，跳过")
        return {"total_accounts": 0, "new_content": 0, "errors": 0}

    competitor_coll = db["competitors"]
    content_coll = db["competitor_content"]

    # 获取所有竞品账号
    accounts = []
    async for doc in competitor_coll.find({}):
        accounts.append(doc)

    if not accounts:
        logger.info("[竞品采集] 暂无竞品账号")
        return {"total_accounts": 0, "new_content": 0, "errors": 0}

    total_new = 0
    total_errors = 0

    for acc in accounts:
        competitor_id = str(acc["_id"])
        platform = acc.get("platform", "")
        account_id = acc.get("account_id", "")
        account_name = acc.get("account_name") or acc.get("name", "")

        try:
            contents = await fetch_competitor_content(
                platform=platform,
                account_id=account_id,
                account_name=account_name,
                limit=10,
            )

            new_count = 0
            for content in contents:
                # 去重：检查是否已存在
                platform_content_id = content.get("platform_content_id", "")
                if not platform_content_id:
                    continue

                exists = await content_coll.find_one({
                    "competitor_id": competitor_id,
                    "platform_content_id": platform_content_id,
                })
                if exists:
                    # 更新指标数据
                    await content_coll.update_one(
                        {"_id": exists["_id"]},
                        {"$set": {
                            "views": content.get("views", 0),
                            "likes": content.get("likes", 0),
                            "comments": content.get("comments", 0),
                            "shares": content.get("shares", 0),
                            "updated_at": datetime.utcnow(),
                        }},
                    )
                    continue

                # 新内容，插入
                doc = {
                    "competitor_id": competitor_id,
                    "platform": platform,
                    **content,
                    "fetched_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                }
                await content_coll.insert_one(doc)
                try:
                    from data_collection.service import record_raw_event
                    await record_raw_event(platform, "competitor_content", doc)
                except Exception as e:
                    logger.debug(f"[竞品采集] 统一采集层写入失败: {e}")
                new_count += 1

            # 更新竞品账号元数据
            total_content = await content_coll.count_documents({"competitor_id": competitor_id})
            await competitor_coll.update_one(
                {"_id": acc["_id"]},
                {"$set": {
                    "last_checked_at": datetime.utcnow(),
                    "content_count": total_content,
                    "updated_at": datetime.utcnow(),
                }},
            )

            total_new += new_count
            if new_count > 0:
                logger.info(f"[竞品采集] {acc.get('name', '')} ({platform}) 新增 {new_count} 条内容")

        except Exception as e:
            total_errors += 1
            logger.error(f"[竞品采集] {acc.get('name', '')} 采集失败: {e}")

    logger.info(
        f"[竞品采集] 完成 — 共 {len(accounts)} 个账号, "
        f"新增 {total_new} 条内容, {total_errors} 个错误"
    )
    return {
        "total_accounts": len(accounts),
        "new_content": total_new,
        "errors": total_errors,
    }
