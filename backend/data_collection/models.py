from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class CollectionTarget(BaseModel):
    platform: str = Field(default="douyin")
    source_type: str = Field(default="hot_search")
    keyword: str = ""
    account_id: str = ""
    account_name: str = ""
    limit: int = Field(default=20, ge=1, le=100)


class CollectionJobCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    target: CollectionTarget
    schedule: str = Field(default="manual")
    purpose: str = Field(default="trend_analysis")
    status: str = Field(default="active")


class ManualCollectRequest(BaseModel):
    platform: str = Field(default="douyin")
    source_type: str = Field(default="hot_search")
    keyword: str = ""
    account_id: str = ""
    account_name: str = ""
    limit: int = Field(default=20, ge=1, le=100)


class SmartCollectQuestion(BaseModel):
    question: str = Field(..., min_length=2, max_length=500)


class RawEventIn(BaseModel):
    source: str
    source_type: str
    entity_type: str = "content"
    entity_id: str = ""
    payload: dict[str, Any] = Field(default_factory=dict)
    collected_at: datetime = Field(default_factory=datetime.utcnow)
    job_id: Optional[str] = None


class QualityReport(BaseModel):
    score: float
    missing_fields: list[str] = Field(default_factory=list)
    is_duplicate: bool = False
    warnings: list[str] = Field(default_factory=list)
