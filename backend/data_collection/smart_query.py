from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime

from .service import _db, record_many

logger = logging.getLogger("echoflow.data_collection.smart_query")


PLATFORM_ALIASES = {
    "douyin": ["抖音", "douyin"],
    "xiaohongshu": ["小红书", "xhs", "xiaohongshu"],
    "bilibili": ["b站", "bilibili", "哔哩哔哩"],
    "weibo": ["微博", "weibo"],
}


INTENT_TOKENS = (
    "我想", "最近", "现在", "帮我", "分析", "看看", "看下", "看一下", "看", "查一下", "查",
    "了解", "一下", "什么", "有哪些", "有没有", "热点", "热搜", "趋势", "榜单", "数据",
    "找", "搜索", "获取", "相关", "内容", "东西", "在", "的", "关于", "品牌", "产品", "商品",
    "视频", "笔记", "作品", "信息",
)

SEARCH_INTENT_TOKENS = (
    "找", "搜索", "获取", "查", "看", "了解", "分析", "相关", "关于",
)

CONTENT_INTENT_TOKENS = (
    "内容", "视频", "笔记", "作品", "商品", "产品", "爆款", "测评", "种草", "带货", "直播",
    "旗舰店", "店铺", "口碑", "评价", "评论", "素材", "案例",
)

HOT_ONLY_TOKENS = ("热点", "热搜", "趋势", "榜单", "热榜")

GENERIC_KEYWORDS = {
    "", "护肤", "美妆", "彩妆", "电商", "运营", "短视频", "内容", "品牌", "产品", "商品",
}


def infer_collection_plan(question: str) -> dict:
    question = _focus_question(question)
    text = question.lower()
    platform = "douyin"
    for key, aliases in PLATFORM_ALIASES.items():
        if any(alias.lower() in text for alias in aliases):
            platform = key
            break

    account_name = _extract_account_name(question)
    keyword = _extract_keyword(question, platform, account_name)

    source_type = "hot_search"
    if account_name or any(word in question for word in ("竞品", "对手", "账号", "达人", "博主")):
        source_type = "competitor_content"
    elif _should_collect_keyword_content(question, platform, keyword):
        source_type = "keyword_content"
    else:
        keyword = ""

    confidence = 0.72
    if source_type == "keyword_content" and keyword:
        confidence = 0.9
    elif source_type == "competitor_content" and (account_name or keyword):
        confidence = 0.86

    return {
        "platform": platform,
        "source_type": source_type,
        "keyword": keyword,
        "object_type": "account" if account_name else ("keyword" if source_type == "keyword_content" else "trend"),
        "confidence": confidence,
        "account_id": "",
        "account_name": account_name,
        "limit": 20,
        "reason": "根据问题中的平台、竞品/热点/关键词意图自动选择采集源",
    }


def _extract_account_name(question: str) -> str:
    account_match = re.search(r"(?:账号|博主|达人)[:：\s]+([\w\u4e00-\u9fa5\-_.]+)", question)
    if not account_match:
        account_match = re.search(r"竞品(?:账号|博主|达人)?[:：\s]+([\w\u4e00-\u9fa5\-_.]+)", question)
    if account_match:
        return account_match.group(1)
    return ""


def _should_collect_keyword_content(question: str, platform: str, keyword: str) -> bool:
    if not keyword or keyword in GENERIC_KEYWORDS:
        return False

    has_hot_only_intent = any(token in question for token in HOT_ONLY_TOKENS)
    has_search_intent = any(token in question for token in SEARCH_INTENT_TOKENS)
    has_content_intent = any(token in question for token in CONTENT_INTENT_TOKENS)
    has_platform = any(alias.lower() in question.lower() for alias in PLATFORM_ALIASES.get(platform, []))

    if has_search_intent or has_content_intent:
        return True
    if has_platform and not has_hot_only_intent:
        return True
    return False


def _focus_question(question: str) -> str:
    quoted = re.findall(r"[`「『“\"]([^`」』”\"]{2,120})[`」』”\"]", question)
    if quoted:
        return quoted[-1].strip()
    return question.strip()


def _extract_keyword(question: str, platform: str, account_name: str = "") -> str:
    if account_name:
        return account_name

    alias_pattern = "|".join(re.escape(alias) for alias in PLATFORM_ALIASES.get(platform, []))
    before_platform = re.search(
        rf"([\w\u4e00-\u9fa5\-_.]{{2,40}}?)(?:在|\s+)?(?:{alias_pattern})(?:上|的)?(?:相关|内容|东西|视频|笔记|作品|信息|$)",
        question,
        re.I,
    )
    if before_platform:
        cleaned = _clean_keyword(before_platform.group(1), platform)
        if cleaned:
            return cleaned

    platform_scoped = re.search(
        rf"(?:{alias_pattern})(?:上|的)?\s*([\w\u4e00-\u9fa5\-_.]{{2,40}}?)(?:的|相关|内容|东西|视频|笔记|作品|信息|$)",
        question,
        re.I,
    )
    if platform_scoped:
        cleaned = _clean_keyword(platform_scoped.group(1), platform)
        if cleaned:
            return cleaned

    explicit = re.search(r"(?:找|搜索|获取|关于|查|看|了解|分析)(?:一下)?\s*([\w\u4e00-\u9fa5\-_.]{2,40}?)(?:的|在|上|相关|内容|东西|视频|笔记|作品|信息)", question)
    if explicit:
        cleaned = _clean_keyword(explicit.group(1), platform)
        if cleaned:
            return cleaned

    before_de = re.search(r"([\w\u4e00-\u9fa5\-_.]{2,30}?)的(?:东西|相关|内容|视频|笔记|作品|信息)", question)
    if before_de:
        cleaned = _clean_keyword(before_de.group(1), platform)
        if cleaned:
            return cleaned

    keyword = question
    return _clean_keyword(keyword, platform)


def _clean_keyword(keyword: str, platform: str) -> str:
    aliases = PLATFORM_ALIASES.get(platform, [])
    for token in (*INTENT_TOKENS, *aliases):
        keyword = keyword.replace(token, " ")
    keyword = re.sub(r"\s+", " ", keyword).strip()[:80]
    return keyword


async def answer_with_auto_collection(question: str) -> dict:
    plan = infer_collection_plan(question)
    logger.info(
        "[智能采集] 计划生成 question=%s platform=%s source_type=%s keyword=%s account=%s confidence=%s",
        question,
        plan["platform"],
        plan["source_type"],
        plan.get("keyword", ""),
        plan.get("account_name", ""),
        plan.get("confidence", 0),
    )
    items = await _collect_by_plan(plan)
    stats = await record_many(
        plan["platform"],
        plan["source_type"],
        [{**item, "platform": plan["platform"]} for item in items],
    )
    stats.update({
        "source_status": "success" if items else "empty",
        "fallback_used": any(item.get("source_note") for item in items),
        "failure_reason": "" if items else "未从目标平台或兜底源获取到有效内容",
    })
    context_items = await _latest_context(plan, limit=12)
    if not items and context_items:
        stats["source_status"] = "cache_fallback"
        stats["failure_reason"] = "实时采集未返回新数据，已使用库内同平台同关键词的历史内容作为参考"
    stats["evidence_count"] = len(context_items)
    logger.info(
        "[智能采集] 采集完成 platform=%s source_type=%s keyword=%s items_seen=%s items_recorded=%s evidence=%s fallback=%s status=%s",
        plan["platform"],
        plan["source_type"],
        plan.get("keyword", ""),
        stats.get("items_seen", 0),
        stats.get("items_recorded", 0),
        stats.get("evidence_count", 0),
        stats.get("fallback_used", False),
        stats.get("source_status", ""),
    )
    answer = await _summarize(question, plan, context_items, stats)
    return {
        "question": question,
        "answer": answer,
        "plan": plan,
        "collection": stats,
        "evidence": context_items[:8],
        "answered_at": datetime.utcnow().isoformat(),
    }


async def _collect_by_plan(plan: dict) -> list[dict]:
    if plan["source_type"] == "competitor_content":
        from competitor.crawler import fetch_competitor_content
        return await fetch_competitor_content(
            plan["platform"],
            plan.get("account_id") or plan.get("account_name") or plan.get("keyword", ""),
            plan.get("account_name") or plan.get("keyword", ""),
            plan["limit"],
        )
    if plan["source_type"] == "keyword_content":
        from crawlers.content_search import fetch_keyword_content
        return await fetch_keyword_content(plan["platform"], plan.get("keyword", ""), plan["limit"])

    from crawlers.data_source import fetch_hot_search
    return await fetch_hot_search(plan["platform"], plan["limit"])


async def _latest_context(plan: dict, limit: int = 12) -> list[dict]:
    db = _db()
    base_query = {
        "platform": plan["platform"],
        "source_type": plan["source_type"],
    }
    if plan["source_type"] == "keyword_content" and plan.get("keyword"):
        return await _latest_matching_context(
            db,
            base_query,
            [
                {"keyword": plan["keyword"]},
                {"search_keyword": plan["keyword"]},
                {"raw.keyword": plan["keyword"]},
                {"raw.search_keyword": plan["keyword"]},
            ],
            limit,
        )
    elif plan["source_type"] == "competitor_content" and (plan.get("account_name") or plan.get("keyword")):
        account = plan.get("account_name") or plan.get("keyword")
        return await _latest_matching_context(
            db,
            base_query,
            [
                {"account_name": account},
                {"author": account},
                {"raw.account_name": account},
            ],
            limit,
        )
    cursor = (
        db["standard_contents"]
        .find(base_query, {"_id": 0, "raw": 0})
        .sort("collected_at", -1)
        .limit(limit)
    )
    return await cursor.to_list(length=limit)


async def _latest_matching_context(db, base_query: dict, selectors: list[dict], limit: int) -> list[dict]:
    seen = set()
    docs = []
    for selector in selectors:
        query = {**base_query, **selector}
        cursor = (
            db["standard_contents"]
            .find(query, {"_id": 0, "raw": 0})
            .sort("collected_at", -1)
            .limit(limit)
        )
        for doc in await cursor.to_list(length=limit):
            dedupe_key = doc.get("entity_id") or doc.get("url") or doc.get("title")
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            docs.append(doc)
            if len(docs) >= limit:
                return docs
    return docs


async def _summarize(question: str, plan: dict, items: list[dict], stats: dict) -> str:
    if not items:
        return (
            f"我已尝试按「{plan['platform']} / {plan['source_type']}」自动采集，但这次没有拿到有效数据。"
            "建议检查平台登录状态、关键词或竞品账号是否可访问。"
        )

    compact = [
        {
            "title": item.get("title"),
            "platform": item.get("platform"),
            "metrics": item.get("metrics", {}),
            "quality": item.get("quality", {}).get("score"),
        }
        for item in items[:12]
    ]
    if os.getenv("SMART_COLLECTION_USE_LLM", "true").lower() in {"0", "false", "no"}:
        return _fallback_summary(plan, items, stats)

    try:
        from agents.base import call_llm_with_retry, get_llm
        from langchain_core.messages import HumanMessage, SystemMessage

        llm = get_llm(temperature=0.35, max_tokens=1600)
        messages = [
            SystemMessage(content=(
                "你是 EchoFlow AI 的数据采集分析 Agent。你必须基于刚采集的数据回答，"
                "输出中文，结构为：结论、数据依据、运营建议、下一步采集建议。"
            )),
            HumanMessage(content=json.dumps({
                "用户问题": question,
                "自动采集计划": plan,
                "采集统计": stats,
                "样本数据": compact,
            }, ensure_ascii=False)),
        ]
        result = await call_llm_with_retry(
            llm,
            messages,
            max_retries=0,
            timeout=8,
            agent_name="smart_data_collection",
        )
        return result.content if hasattr(result, "content") else str(result)
    except Exception:
        return _fallback_summary(plan, items, stats)


def _fallback_summary(plan: dict, items: list[dict], stats: dict) -> str:
    top_titles = [item.get("title") for item in items[:5] if item.get("title")]
    avg_quality = stats.get("avg_quality", 0)
    target = plan.get("keyword") or plan.get("account_name") or "当前热榜"
    source_note = "，其中包含兜底公开搜索结果" if stats.get("fallback_used") else ""
    if stats.get("source_status") == "cache_fallback":
        return (
            f"本次已围绕「{target}」请求 {plan['platform']} 的 {plan['source_type']} 实时采集，但实时源暂时没有返回新数据。"
            f"我已改用库内同关键词历史内容作为参考，共找到 {stats.get('evidence_count', len(items))} 条可用证据。\n\n"
            f"当前最值得关注的样本包括：{'、'.join(top_titles) or '暂无标题'}。\n\n"
            "运营建议：先基于这些历史样本提炼卖点、标题和脚本方向；同时建议稍后重试实时采集，或接入平台登录态/API 以获得最新互动指标。"
        )
    return (
        f"已围绕「{target}」自动采集 {plan['platform']} 的 {plan['source_type']} 数据，共记录 "
        f"{stats.get('items_recorded', 0)} 条{source_note}，平均质量分 {avg_quality}。\n\n"
        f"当前最值得关注的样本包括：{'、'.join(top_titles) or '暂无标题'}。\n\n"
        "运营建议：优先围绕高热词做标题/脚本测试，并把发布后的播放、点赞、评论、分享回流到采集中心，形成下一轮判断依据。"
    )
