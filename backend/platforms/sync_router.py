"""
平台数据同步模块 - 爆款采集 + CSV 导入（MongoDB 持久化版）
"""
from __future__ import annotations

import csv
import io
import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel

from data_collection.normalizer import parse_int_value

logger = logging.getLogger("echoflow.sync")

router = APIRouter(prefix="/api/platform", tags=["platform-sync"])


class VideoItem(BaseModel):
    title: str = ''
    author: str = ''
    url: str = ''
    likes: int = 0
    comments: int = 0
    collects: int = 0
    shares: int = 0
    collected_at: Optional[str] = None


class CollectRequest(BaseModel):
    platform: str = 'douyin'
    video: VideoItem


class BatchCollectRequest(BaseModel):
    platform: str = 'douyin'
    videos: list[VideoItem]


class PlatformSyncRequest(BaseModel):
    platform: str
    account_name: Optional[str] = None
    data: dict


def _get_videos_collection():
    from memory import db
    if db is None:
        raise RuntimeError("MongoDB 未初始化")
    return db["collected_videos"]


def _get_sync_collection():
    from memory import db
    if db is None:
        raise RuntimeError("MongoDB 未初始化")
    return db["platform_sync"]


@router.post("/collect")
async def collect_video(request: CollectRequest):
    """采集单条视频（MongoDB 持久化）"""
    coll = _get_videos_collection()

    video = request.video.model_dump()
    video["platform"] = request.platform
    video["collected_at"] = video.get("collected_at") or datetime.now().isoformat()

    # 去重：通过 URL 检查
    if video["url"]:
        existing = await coll.find_one({"url": video["url"], "platform": request.platform})
        if existing:
            total = await coll.count_documents({})
            return {"success": True, "message": "已采集过该视频", "total": total}

    await coll.insert_one(video)
    try:
        from data_collection.service import record_raw_event
        await record_raw_event(request.platform, "manual_collect", video)
    except Exception as e:
        logger.debug(f"统一采集层写入失败: {e}")
    total = await coll.count_documents({})
    return {"success": True, "message": "采集成功", "total": total}


@router.post("/collect/batch")
async def collect_batch(request: BatchCollectRequest):
    """批量采集视频（MongoDB 持久化）"""
    coll = _get_videos_collection()

    new_count = 0
    for video in request.videos:
        v = video.model_dump()
        v["platform"] = request.platform
        v["collected_at"] = v.get("collected_at") or datetime.now().isoformat()

        if v["url"]:
            existing = await coll.find_one({"url": v["url"], "platform": request.platform})
            if existing:
                continue

        await coll.insert_one(v)
        try:
            from data_collection.service import record_raw_event
            await record_raw_event(request.platform, "manual_collect", v)
        except Exception as e:
            logger.debug(f"统一采集层写入失败: {e}")
        new_count += 1

    total = await coll.count_documents({})
    return {"success": True, "message": f"新增 {new_count} 条，共 {total} 条", "new_count": new_count, "total": total}


@router.get("/collect/list")
async def list_collected(
    platform: Optional[str] = None,
    page: int = 1,
    size: int = 20,
):
    """获取采集列表（MongoDB 分页查询）"""
    coll = _get_videos_collection()
    query = {}
    if platform:
        query["platform"] = platform

    total = await coll.count_documents(query)
    skip = (page - 1) * size
    cursor = coll.find(query).sort("collected_at", -1).skip(skip).limit(size)
    items = []
    async for doc in cursor:
        doc["id"] = str(doc.pop("_id"))
        items.append(doc)

    return {"total": total, "page": page, "size": size, "items": items}


@router.post("/sync")
async def sync_platform_data(request: PlatformSyncRequest):
    """接收浏览器插件推送的数据（MongoDB 持久化）"""
    platform = request.platform.lower()
    if platform not in ['douyin', 'bilibili', 'xiaohongshu', 'weibo', 'kuaishou']:
        raise HTTPException(status_code=400, detail=f"不支持的平台: {platform}")

    coll = _get_sync_collection()
    doc = {
        "platform": platform,
        "account_name": request.account_name,
        "data": request.data,
        "synced_at": datetime.now().isoformat(),
    }

    # upsert 替换该平台的同步数据
    await coll.replace_one({"platform": platform}, doc, upsert=True)

    videos = request.data.get("videos", [])
    if videos:
        try:
            from data_collection.service import record_many
            await record_many(platform, "platform_sync", [{**v, "platform": platform} for v in videos])
        except Exception as e:
            logger.debug(f"统一采集层写入失败: {e}")
    logger.info(f"平台同步: {platform} - {len(videos)} 条数据")
    return {"success": True, "platform": platform, "message": f"成功同步 {len(videos)} 条"}


@router.post("/import/csv")
async def import_csv(platform: str, file: UploadFile = File(...)):
    """导入 CSV 文件（MongoDB 持久化）"""
    content = await file.read()
    text = content.decode('utf-8-sig', errors='ignore')

    reader = csv.DictReader(io.StringIO(text))
    videos = []
    total_views = 0
    total_likes = 0

    for row in reader:
        title = (row.get('视频标题') or row.get('标题') or
                 row.get('title') or row.get('作品名称') or '')
        views = parse_int_value(row.get('播放量', row.get('播放次数', row.get('views', 0))))
        likes = parse_int_value(row.get('点赞数', row.get('点赞', row.get('likes', 0))))
        comments = parse_int_value(row.get('评论数', row.get('评论', row.get('comments', 0))))
        shares = parse_int_value(row.get('转发数', row.get('转发', row.get('shares', 0))))

        if title:
            videos.append({'title': title.strip(), 'views': views, 'likes': likes,
                          'comments': comments, 'shares': shares})
            total_views += views
            total_likes += likes

    if not videos:
        raise HTTPException(status_code=400, detail="未能解析出视频数据")

    # 持久化到 MongoDB
    sync_coll = _get_sync_collection()
    await sync_coll.replace_one(
        {"platform": platform},
        {"platform": platform, "data": {"videos": videos, "overview": {"total_views": total_views, "total_likes": total_likes}},
         "synced_at": datetime.now().isoformat(), "source": "csv_import"},
        upsert=True,
    )
    try:
        from data_collection.service import record_many
        await record_many(platform, "csv_import", [{**v, "platform": platform} for v in videos])
    except Exception as e:
        logger.debug(f"统一采集层写入失败: {e}")

    logger.info(f"CSV 导入: {platform} - {len(videos)} 条")
    return {"success": True, "message": f"成功导入 {len(videos)} 条", "video_count": len(videos)}


@router.get("/data")
async def get_all_platform_data():
    """获取所有平台同步数据（MongoDB）"""
    coll = _get_sync_collection()
    data = {}
    async for doc in coll.find({}):
        plat = doc.get("platform", "unknown")
        doc["id"] = str(doc.pop("_id"))
        data[plat] = doc
    return {"platforms": list(data.keys()), "data": data}


@router.get("/data/{platform}")
async def get_platform_data(platform: str):
    """获取指定平台同步数据"""
    coll = _get_sync_collection()
    doc = await coll.find_one({"platform": platform})
    if not doc:
        raise HTTPException(status_code=404, detail=f"没有 {platform} 的数据")
    doc["id"] = str(doc.pop("_id"))
    return doc
