"""Obsidian 导出 — 将每日热点总结保存为 Obsidian 兼容的 Markdown 文件

保存路径: /Users/chuxinhui/home/日记/信息/YYYY-MM-DD 每日热点.md
"""

from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)

# Obsidian Vault 路径
OBSIDIAN_VAULT = os.path.expanduser("/Users/chuxinhui/home/日记")
DIGEST_FOLDER = "信息"


def _ensure_folder():
    """确保目标文件夹存在"""
    folder = os.path.join(OBSIDIAN_VAULT, DIGEST_FOLDER)
    os.makedirs(folder, exist_ok=True)
    return folder


def _heat_icon(heat: str) -> str:
    """热度等级对应图标"""
    return {"极高": "🔴", "高": "🟠", "中": "🟡", "低": "⚪"}.get(heat, "⚪")


def _format_platforms_with_urls(topic_data: dict) -> str:
    """平台列表带链接格式"""
    platforms = topic_data.get("platforms", [])
    urls = topic_data.get("urls", {})
    if urls:
        parts = []
        for p in platforms:
            url = urls.get(p, "")
            if url:
                parts.append(f"[{p}]({url})")
            else:
                parts.append(f"`{p}`")
        return " ".join(parts)
    return " ".join(f"`{p}`" for p in platforms)


def export_to_obsidian(digest: dict[str, Any]) -> str:
    """将每日热点总结导出为 Obsidian Markdown 文件

    Args:
        digest: generate_daily_digest() 返回的完整数据

    Returns:
        保存的文件路径
    """
    folder = _ensure_folder()
    date = digest.get("date", datetime.now().strftime("%Y-%m-%d"))
    filename = f"{date} 每日热点.md"
    filepath = os.path.join(folder, filename)

    # ── 构建 Markdown ──────────────────────────────────

    lines: list[str] = []

    # YAML Frontmatter
    focus = digest.get("focus_topic")
    track = digest.get("track")
    tags = ["每日热点", "趋势分析"]
    if focus:
        tags.append(focus)
    if track:
        tags.append(track)

    lines.append("---")
    lines.append(f"date: {date}")
    lines.append(f"created: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"type: daily-digest")
    lines.append(f"tags: [{', '.join(tags)}]")
    if focus:
        lines.append(f"focus: \"{focus}\"")
    if track:
        lines.append(f"track: \"{track}\"")
    lines.append(f"total_items: {digest.get('total_hot_items', 0)}")
    # 平台统计
    stats = digest.get("platform_stats", {})
    if stats:
        lines.append("platforms:")
        for p, count in stats.items():
            lines.append(f"  {p}: {count}")
    lines.append("---")
    lines.append("")

    # 标题
    lines.append(f"# 📰 {date} 每日热点总结")
    lines.append("")

    # 今日概览
    overview = digest.get("overview", "")
    if overview:
        lines.append("> [!abstract] 今日概览")
        for line in overview.split("\n"):
            lines.append(f"> {line}")
        lines.append("")

    # 统计摘要
    lines.append(f"📊 共覆盖 **{len(PLATFORM_NAMES := {'bilibili': 'B站', 'douyin': '抖音', 'xiaohongshu': '小红书', 'weibo': '微博'})}** 个平台，采集 **{digest.get('total_hot_items', 0)}** 条热搜数据")
    lines.append("")

    # ── 热点分类 ──────────────────────────────────────
    categories = digest.get("categories", [])
    if categories:
        lines.append("## 🔖 热点分类")
        lines.append("")
        for cat in categories:
            icon = cat.get("icon", "📌")
            name = cat.get("name", "未分类")
            topics = cat.get("topics", [])
            lines.append(f"### {icon} {name}")
            lines.append("")
            for t in topics:
                heat = t.get("heat", "中")
                topic_name = t.get("topic", "")
                summary = t.get("summary", "")
                angle = t.get("content_angle", "")
                ai_take = t.get("ai_take", "")

                lines.append(f"- {_heat_icon(heat)} **{topic_name}** {_format_platforms_with_urls(t)}")
                if summary:
                    lines.append(f"  - {summary}")
                if ai_take:
                    lines.append(f"  - 🧠 *{ai_take}*")
                if angle:
                    lines.append(f"  - 💡 创作角度：{angle}")
            lines.append("")

    # ── 跨平台热点 ──────────────────────────────────────
    cross = digest.get("cross_platform", [])
    if cross:
        lines.append("## 🔥 跨平台热点")
        lines.append("")
        lines.append("> [!tip] 多个平台同时上榜的话题，说明传播力强，值得重点关注")
        lines.append("")
        for item in cross:
            topic = item.get("topic", "")
            analysis = item.get("analysis", "")
            ai_take = item.get("ai_take", "")
            lines.append(f"- **{topic}** {_format_platforms_with_urls(item)}")
            if analysis:
                lines.append(f"  - {analysis}")
            if ai_take:
                lines.append(f"  - 🧠 *{ai_take}*")
        lines.append("")

    # ── 创作机会 ──────────────────────────────────────
    opps = digest.get("opportunities", [])
    if opps:
        lines.append("## 💡 创作机会")
        lines.append("")
        for i, opp in enumerate(opps, 1):
            title = opp.get("title", "")
            platform = opp.get("platform", "")
            fmt = opp.get("format", "")
            angle = opp.get("angle", "")
            timing = opp.get("timing", "")

            timing_badge = {"立即": "🔴", "今天内": "🟠", "本周内": "🟡"}.get(timing, "⚪")

            lines.append(f"### {i}. {title}")
            lines.append("")
            lines.append(f"| 平台 | 形式 | 时效性 |")
            lines.append(f"|------|------|--------|")
            lines.append(f"| {platform} | {fmt} | {timing_badge} {timing} |")
            lines.append("")
            if angle:
                lines.append(f"> [!info] 切入角度")
                lines.append(f"> {angle}")
                lines.append("")

    # ── 趋势洞察 ──────────────────────────────────────
    insights = digest.get("insights", [])
    if insights:
        lines.append("## 🔮 趋势洞察")
        lines.append("")
        for insight in insights:
            pattern = insight.get("pattern", "")
            implication = insight.get("implication", "")
            lines.append(f"- **{pattern}**")
            if implication:
                lines.append(f"  - 👉 {implication}")
        lines.append("")

    # ── AI 主编手记 ──────────────────────────────────────
    commentary = digest.get("ai_commentary", "")
    if commentary:
        lines.append("## 🖊️ AI 主编手记")
        lines.append("")
        lines.append("> [!quote] 以下内容由 AI 基于今日热搜数据独立撰写，代表 AI 的分析观点")
        lines.append("")
        for para in commentary.split("\n"):
            para = para.strip()
            if para:
                lines.append(para)
                lines.append("")

    # ── 尾部 ──────────────────────────────────────────
    lines.append("---")
    lines.append(f"*由 EchoFlow AI 自动生成于 {digest.get('generated_at', '')[:19]}*")
    lines.append("")
    lines.append("⬅️ [[前一天]] | [[后一天]] ➡️")

    # ── 写入文件 ──────────────────────────────────────
    content = "\n".join(lines)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    logger.info(f"[Obsidian] 已导出: {filepath}")
    return filepath
