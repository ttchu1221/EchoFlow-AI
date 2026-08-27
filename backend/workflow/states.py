# -*- coding: utf-8 -*-
"""内容工作流状态机 — 草稿→审核→发布"""

import enum
import logging
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("echowflow.workflow")


class ContentStatus(str, enum.Enum):
    """内容状态"""
    DRAFT = "draft"            # 草稿（AI 生成 / 手动创建）
    PENDING_REVIEW = "pending_review"  # 待审核
    APPROVED = "approved"      # 审核通过
    REJECTED = "rejected"      # 驳回
    PUBLISHING = "publishing"  # 发布中
    PUBLISHED = "published"    # 已发布
    FAILED = "failed"          # 发布失败


class ReviewAction(str, enum.Enum):
    """审核动作"""
    SUBMIT = "submit"          # 提交审核
    APPROVE = "approve"        # 通过
    REJECT = "reject"          # 驳回
    PUBLISH = "publish"        # 发布
    EDIT = "edit"              # 编辑后重新提交
    CANCEL = "cancel"          # 撤回


# 合法的状态转换
VALID_TRANSITIONS = {
    ContentStatus.DRAFT: [ContentStatus.PENDING_REVIEW],
    ContentStatus.PENDING_REVIEW: [ContentStatus.APPROVED, ContentStatus.REJECTED, ContentStatus.DRAFT],
    ContentStatus.APPROVED: [ContentStatus.PUBLISHING, ContentStatus.DRAFT],
    ContentStatus.REJECTED: [ContentStatus.DRAFT, ContentStatus.PENDING_REVIEW],
    ContentStatus.PUBLISHING: [ContentStatus.PUBLISHED, ContentStatus.FAILED],
    ContentStatus.FAILED: [ContentStatus.PUBLISHING, ContentStatus.DRAFT],
    ContentStatus.PUBLISHED: [],  # 已发布不可回退
}

# 动作 → 目标状态
ACTION_TARGET = {
    ReviewAction.SUBMIT: ContentStatus.PENDING_REVIEW,
    ReviewAction.APPROVE: ContentStatus.APPROVED,
    ReviewAction.REJECT: ContentStatus.REJECTED,
    ReviewAction.PUBLISH: ContentStatus.PUBLISHING,
    ReviewAction.EDIT: ContentStatus.DRAFT,
    ReviewAction.CANCEL: ContentStatus.DRAFT,
}


def can_transition(current: ContentStatus, action: ReviewAction) -> bool:
    """检查状态转换是否合法"""
    target = ACTION_TARGET.get(action)
    if not target:
        return False
    return target in VALID_TRANSITIONS.get(current, [])


def transition(current: ContentStatus, action: ReviewAction) -> ContentStatus:
    """执行状态转换"""
    if not can_transition(current, action):
        raise ValueError(f"非法状态转换: {current.value} --{action.value}--> {ACTION_TARGET[action].value}")
    return ACTION_TARGET[action]


# --- Pydantic Schemas ---

class ContentItem(BaseModel):
    """内容项"""
    id: Optional[str] = None
    title: str = Field(..., max_length=200)
    content: dict  # 完整内容（hook, script, cover 等）
    platform: str
    status: ContentStatus = ContentStatus.DRAFT
    author_id: str = ""
    author_name: str = ""
    reviewer_id: Optional[str] = None
    reviewer_name: Optional[str] = None
    review_comment: Optional[str] = None
    ab_test_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    history: list = Field(default_factory=list)  # 状态变更历史


class ReviewRequest(BaseModel):
    """审核请求"""
    action: ReviewAction
    comment: Optional[str] = None
    content: Optional[dict] = None  # 编辑时可附带修改内容


class BulkReviewRequest(BaseModel):
    """批量审核"""
    content_ids: list[str]
    action: ReviewAction
    comment: Optional[str] = None


class ContentListResponse(BaseModel):
    """内容列表响应"""
    items: list[ContentItem]
    total: int
    page: int
    page_size: int
