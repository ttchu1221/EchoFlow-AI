from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from bson import ObjectId

from .normalizer import normalize_content
from .quality import evaluate_content

logger = logging.getLogger("echoflow.data_collection")


def _db():
    from memory import db
    if db is None:
        raise RuntimeError("MongoDB 未初始化")
    return db


def _clean_id(doc: dict) -> dict:
    if "_id" in doc:
        doc["id"] = str(doc.pop("_id"))
    return doc


async def ensure_indexes():
    db = _db()
    await db["raw_events"].create_index([("source", 1), ("source_type", 1), ("entity_id", 1)])
    await db["standard_contents"].create_index([("platform", 1), ("entity_id", 1)], unique=False)
    await db["standard_contents"].create_index([("collected_at", -1)])
    await db["collection_jobs"].create_index([("status", 1), ("created_at", -1)])


async def record_raw_event(
    source: str,
    source_type: str,
    payload: dict[str, Any],
    entity_type: str = "content",
    entity_id: str = "",
    job_id: str | None = None,
) -> dict:
    db = _db()
    now = datetime.utcnow()
    entity_id = entity_id or str(
        payload.get("platform_content_id")
        or payload.get("content_id")
        or payload.get("post_id")
        or payload.get("url")
        or payload.get("keyword")
        or payload.get("title")
        or ""
    )
    raw_doc = {
        "source": source,
        "source_type": source_type,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "payload": payload,
        "job_id": job_id,
        "collected_at": now,
    }
    await db["raw_events"].insert_one(raw_doc)

    standard = normalize_content(source, source_type, payload, job_id)
    existing = None
    if standard.get("entity_id"):
        existing = await db["standard_contents"].find_one({
            "platform": standard["platform"],
            "entity_id": standard["entity_id"],
        })
    standard["quality"] = evaluate_content(standard, is_duplicate=bool(existing)).model_dump()
    if existing:
        await db["standard_contents"].update_one({"_id": existing["_id"]}, {"$set": standard})
        standard["_id"] = existing["_id"]
    else:
        result = await db["standard_contents"].insert_one(standard)
        standard["_id"] = result.inserted_id

    return _clean_id(standard)


async def record_many(source: str, source_type: str, items: list[dict], job_id: str | None = None) -> dict:
    inserted = 0
    duplicates = 0
    quality_total = 0.0
    for item in items:
        doc = await record_raw_event(source, source_type, item, job_id=job_id)
        inserted += 1
        if doc.get("quality", {}).get("is_duplicate"):
            duplicates += 1
        quality_total += doc.get("quality", {}).get("score", 0)
    return {
        "items_seen": len(items),
        "items_recorded": inserted,
        "duplicates": duplicates,
        "avg_quality": round(quality_total / max(inserted, 1), 2),
    }


async def create_job(data: dict, user: dict | None = None) -> dict:
    db = _db()
    now = datetime.utcnow()
    doc = {
        **data,
        "created_by": user.get("username") if user else "",
        "created_at": now,
        "updated_at": now,
        "last_run_at": None,
        "last_status": "never_run",
        "last_error": "",
        "run_count": 0,
    }
    result = await db["collection_jobs"].insert_one(doc)
    doc["_id"] = result.inserted_id
    return _clean_id(doc)


async def update_job_run(job_id: str, status: str, result: dict | None = None, error: str = ""):
    db = _db()
    update = {
        "last_run_at": datetime.utcnow(),
        "last_status": status,
        "last_error": error,
        "updated_at": datetime.utcnow(),
    }
    if result is not None:
        update["last_result"] = result
    await db["collection_jobs"].update_one(
        {"_id": ObjectId(job_id)},
        {"$set": update, "$inc": {"run_count": 1}},
    )


async def overview(days: int = 7) -> dict:
    db = _db()
    cutoff = datetime.utcnow() - timedelta(days=days)
    total_jobs = await db["collection_jobs"].count_documents({})
    active_jobs = await db["collection_jobs"].count_documents({"status": "active"})
    raw_events = await db["raw_events"].count_documents({"collected_at": {"$gte": cutoff}})
    standard_contents = await db["standard_contents"].count_documents({"collected_at": {"$gte": cutoff}})
    quality_docs = await db["standard_contents"].find(
        {"collected_at": {"$gte": cutoff}},
        {"quality.score": 1, "platform": 1, "source_type": 1},
    ).to_list(length=1000)
    avg_quality = round(
        sum(d.get("quality", {}).get("score", 0) for d in quality_docs) / max(len(quality_docs), 1),
        2,
    )
    platforms = {}
    source_types = {}
    for doc in quality_docs:
        platforms[doc.get("platform", "unknown")] = platforms.get(doc.get("platform", "unknown"), 0) + 1
        source_types[doc.get("source_type", "unknown")] = source_types.get(doc.get("source_type", "unknown"), 0) + 1
    return {
        "period_days": days,
        "total_jobs": total_jobs,
        "active_jobs": active_jobs,
        "raw_events": raw_events,
        "standard_contents": standard_contents,
        "avg_quality": avg_quality,
        "platform_distribution": platforms,
        "source_type_distribution": source_types,
    }

