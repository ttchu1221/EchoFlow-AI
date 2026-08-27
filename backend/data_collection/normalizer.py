from __future__ import annotations

from datetime import datetime
from typing import Any

from .quality import evaluate_content


def parse_int_value(value: Any) -> int:
    if isinstance(value, bool):
        return 0
    if isinstance(value, (int, float)):
        return int(value)
    if not isinstance(value, str) or not value.strip():
        return 0
    text = value.strip().replace(",", "").replace("+", "")
    if text in {"-", "--", "—", "暂无", "无", "null", "None"}:
        return 0
    try:
        if "万" in text:
            return int(float(text.replace("万", "").strip()) * 10000)
        if "亿" in text:
            return int(float(text.replace("亿", "").strip()) * 100000000)
        return int(float(text))
    except ValueError:
        return 0


def _int_value(value: Any) -> int:
    return parse_int_value(value)


def normalize_content(source: str, source_type: str, payload: dict, job_id: str | None = None) -> dict:
    entity_id = (
        payload.get("platform_content_id")
        or payload.get("content_id")
        or payload.get("post_id")
        or payload.get("url")
        or payload.get("keyword")
        or payload.get("title")
        or ""
    )
    title = payload.get("title") or payload.get("keyword") or payload.get("name") or ""
    metrics = {
        "views": _int_value(payload.get("views", payload.get("view_count", payload.get("play_count", 0)))),
        "likes": _int_value(payload.get("likes", payload.get("like_count", payload.get("digg_count", 0)))),
        "comments": _int_value(payload.get("comments", payload.get("comment_count", 0))),
        "shares": _int_value(payload.get("shares", payload.get("share_count", 0))),
        "saves": _int_value(payload.get("saves", payload.get("collects", payload.get("collect_count", 0)))),
        "heat_score": _int_value(payload.get("heat_score", 0)),
    }
    now = datetime.utcnow()
    doc = {
        "source": source,
        "source_type": source_type,
        "platform": payload.get("platform") or source,
        "entity_type": payload.get("entity_type", "content"),
        "entity_id": str(entity_id),
        "title": title,
        "author": payload.get("author", payload.get("account_name", "")),
        "description": payload.get("description", payload.get("desc", "")),
        "url": payload.get("url", payload.get("content_url", "")),
        "cover_url": payload.get("cover_url", ""),
        "keyword": payload.get("keyword") or payload.get("search_keyword") or "",
        "search_keyword": payload.get("search_keyword") or payload.get("keyword") or "",
        "account_name": payload.get("account_name", ""),
        "source_note": payload.get("source_note", ""),
        "metrics": metrics,
        "published_at": payload.get("published_at"),
        "collected_at": payload.get("collected_at") or now,
        "updated_at": now,
        "job_id": job_id,
        "raw": payload,
    }
    doc["quality"] = evaluate_content(doc).model_dump()
    return doc
