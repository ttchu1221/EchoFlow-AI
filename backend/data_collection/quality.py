from __future__ import annotations

from .models import QualityReport


REQUIRED_CONTENT_FIELDS = ["title", "platform"]


def evaluate_content(doc: dict, is_duplicate: bool = False) -> QualityReport:
    missing = [field for field in REQUIRED_CONTENT_FIELDS if not doc.get(field)]
    warnings = []
    metrics = doc.get("metrics", {})
    if not doc.get("url") and not doc.get("entity_id"):
        warnings.append("缺少内容 URL 或平台内容 ID，后续去重和归因会变弱")
    if not any(metrics.get(k, 0) for k in ("views", "likes", "comments", "shares", "saves")):
        warnings.append("缺少有效互动指标")

    score = 1.0
    score -= len(missing) * 0.2
    score -= len(warnings) * 0.1
    if is_duplicate:
        score -= 0.15
    return QualityReport(
        score=max(round(score, 2), 0),
        missing_fields=missing,
        is_duplicate=is_duplicate,
        warnings=warnings,
    )

