"""
平台数据同步模块 - 爆款采集 + CSV 导入
"""
import csv
import io
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel

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


# 存储
sync_storage = {}
collected_videos = []


@router.post("/collect")
async def collect_video(request: CollectRequest):
    """采集单条视频"""
    global collected_videos
    
    video = request.video.dict()
    video['platform'] = request.platform
    video['collected_at'] = video.get('collected_at') or datetime.now().isoformat()
    
    # 去重
    if any(v['url'] == video['url'] and video['url'] for v in collected_videos):
        return {"success": True, "message": "已采集过该视频", "total": len(collected_videos)}
    
    collected_videos.insert(0, video)
    return {"success": True, "message": "采集成功", "total": len(collected_videos)}


@router.post("/collect/batch")
async def collect_batch(request: BatchCollectRequest):
    """批量采集视频"""
    global collected_videos
    
    existing_urls = {v['url'] for v in collected_videos if v['url']}
    new_count = 0
    
    for video in request.videos:
        v = video.dict()
        v['platform'] = request.platform
        v['collected_at'] = v.get('collected_at') or datetime.now().isoformat()
        
        if v['url'] not in existing_urls:
            collected_videos.insert(0, v)
            existing_urls.add(v['url'])
            new_count += 1
    
    return {
        "success": True,
        "message": f"新增 {new_count} 条，共 {len(collected_videos)} 条",
        "new_count": new_count,
        "total": len(collected_videos),
    }


@router.get("/collect/list")
async def list_collected(
    platform: Optional[str] = None,
    page: int = 1,
    size: int = 20,
):
    """获取采集列表"""
    global collected_videos
    
    items = collected_videos
    if platform:
        items = [v for v in items if v.get('platform') == platform]
    
    start = (page - 1) * size
    end = start + size
    
    return {
        "total": len(items),
        "page": page,
        "size": size,
        "items": items[start:end],
    }


@router.post("/sync")
async def sync_platform_data(request: PlatformSyncRequest):
    """接收浏览器插件推送的数据"""
    platform = request.platform.lower()
    if platform not in ['douyin', 'bilibili', 'xiaohongshu', 'weibo', 'kuaishou']:
        raise HTTPException(status_code=400, detail=f"不支持的平台: {platform}")

    sync_storage[platform] = {
        "platform": platform,
        "account_name": request.account_name,
        "data": request.data,
        "synced_at": datetime.now().isoformat(),
    }

    videos = request.data.get("videos", [])
    return {"success": True, "platform": platform, "message": f"成功同步 {len(videos)} 条"}


@router.post("/import/csv")
async def import_csv(platform: str, file: UploadFile = File(...)):
    """导入 CSV 文件"""
    content = await file.read()
    text = content.decode('utf-8-sig', errors='ignore')
    
    reader = csv.DictReader(io.StringIO(text))
    videos = []
    total_views = 0
    total_likes = 0

    for row in reader:
        title = (row.get('视频标题') or row.get('标题') or
                 row.get('title') or row.get('作品名称') or '')
        views = int(row.get('播放量', row.get('播放次数', row.get('views', 0))) or 0)
        likes = int(row.get('点赞数', row.get('点赞', row.get('likes', 0))) or 0)
        comments = int(row.get('评论数', row.get('评论', row.get('comments', 0))) or 0)
        shares = int(row.get('转发数', row.get('转发', row.get('shares', 0))) or 0)

        if title:
            videos.append({'title': title.strip(), 'views': views, 'likes': likes,
                          'comments': comments, 'shares': shares})
            total_views += views
            total_likes += likes

    if not videos:
        raise HTTPException(status_code=400, detail="未能解析出视频数据")

    sync_storage[platform] = {
        "platform": platform,
        "data": {"videos": videos, "overview": {"total_views": total_views, "total_likes": total_likes}},
        "synced_at": datetime.now().isoformat(),
        "source": "csv_import",
    }

    return {"success": True, "message": f"成功导入 {len(videos)} 条", "video_count": len(videos)}


@router.get("/data")
async def get_all_platform_data():
    return {"platforms": list(sync_storage.keys()), "data": sync_storage}


@router.get("/data/{platform}")
async def get_platform_data(platform: str):
    if platform not in sync_storage:
        raise HTTPException(status_code=404, detail=f"没有 {platform} 的数据")
    return sync_storage[platform]
