# -*- coding: utf-8 -*-
"""A/B 测试数据自动采集 — 定时拉取已发布变体的平台指标

流程：
1. 查找所有状态为 "running" 的 A/B 测试
2. 对每个变体，根据 content_id (platform_post_id) 从平台拉取指标
3. 更新 A/B 测试的 results 字段
4. 如果测试已运行超过 auto_select_hours，自动判定优胜并完成测试
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

logger = logging.getLogger("echoflow.abtest.collector")


def _get_abtest_collection():
    from memory import db
    if db is None:
        raise RuntimeError("MongoDB 未初始化")
    return db["ab_tests"]


async def collect_abtest_metrics() -> dict:
    """采集所有运行中 A/B 测试的变体指标
    
    返回: {"tests_checked": N, "variants_updated": M, "auto_completed": C}
    """
    from memory import db
    if db is None:
        logger.warning("[A/B采集] MongoDB 未初始化，跳过")
        return {"tests_checked": 0, "variants_updated": 0, "auto_completed": 0}

    coll = _get_abtest_collection()

    # 查找所有运行中的测试
    running_tests = []
    async for doc in coll.find({"status": "running"}):
        running_tests.append(doc)

    if not running_tests:
        logger.debug("[A/B采集] 无运行中的测试")
        return {"tests_checked": 0, "variants_updated": 0, "auto_completed": 0}

    # 获取平台管理器
    try:
        from platforms.manager import PlatformManager
        import memory as _mem
        pm = PlatformManager(use_mock=False)
    except Exception as e:
        logger.warning(f"[A/B采集] 平台管理器初始化失败: {e}")
        # 降级：使用 Mock 数据
        pm = None

    total_updated = 0
    auto_completed = 0

    for test in running_tests:
        test_id = test["_id"]
        variants = test.get("variants", [])
        metric_key = test.get("metric", "engagement_rate")
        auto_select = test.get("auto_select", True)
        auto_hours = test.get("auto_select_hours", 24)
        started_at = test.get("started_at")

        # 为每个变体采集指标
        results = test.get("results", [])
        results_map = {r["variant_id"]: r for r in results}

        for variant in variants:
            variant_id = variant.get("variant_id", "")
            content_id = variant.get("content_id", "")
            platform = variant.get("platform", "")

            if not content_id or not platform:
                # 没有发布的变体，跳过
                continue

            # 从平台获取指标
            metrics_data = await _fetch_variant_metrics(pm, platform, content_id)
            if not metrics_data:
                continue

            # 计算互动率
            views = metrics_data.get("views", 0)
            likes = metrics_data.get("likes", 0)
            comments = metrics_data.get("comments", 0)
            shares = metrics_data.get("shares", 0)
            engagement_rate = 0.0
            if views > 0:
                engagement_rate = round((likes + comments + shares) / views, 4)

            # 更新结果
            result_entry = {
                "variant_id": variant_id,
                "variant_name": variant.get("name", ""),
                "platform": platform,
                "content_id": content_id,
                "views": views,
                "likes": likes,
                "comments": comments,
                "shares": shares,
                "engagement_rate": engagement_rate,
                "collected_at": datetime.utcnow().isoformat(),
            }
            results_map[variant_id] = result_entry
            total_updated += 1

        # 更新数据库中的 results
        updated_results = list(results_map.values())
        update_data = {
            "results": updated_results,
            "updated_at": datetime.utcnow(),
        }

        # 检查是否需要自动完成
        if auto_select and started_at:
            elapsed = datetime.utcnow() - started_at
            if elapsed >= timedelta(hours=auto_hours) and len(updated_results) >= 2:
                # 自动判定优胜
                winner = _determine_winner(updated_results, metric_key)
                if winner:
                    update_data["status"] = "completed"
                    update_data["winner_variant_id"] = winner
                    update_data["completed_at"] = datetime.utcnow()
                    auto_completed += 1
                    logger.info(
                        f"[A/B采集] 测试 {test.get('name', '')} 自动完成，"
                        f"优胜变体: {winner}"
                    )

        await coll.update_one({"_id": test_id}, {"$set": update_data})

    logger.info(
        f"[A/B采集] 完成 — 检查 {len(running_tests)} 个测试, "
        f"更新 {total_updated} 个变体, 自动完成 {auto_completed} 个"
    )
    return {
        "tests_checked": len(running_tests),
        "variants_updated": total_updated,
        "auto_completed": auto_completed,
    }


async def _fetch_variant_metrics(pm, platform: str, content_id: str) -> dict | None:
    """从平台获取变体指标"""
    if pm is None:
        return None

    try:
        metrics = await pm.fetch_metrics(platform, content_id)
        if metrics:
            return {
                "views": metrics.views,
                "likes": metrics.likes,
                "comments": metrics.comments,
                "shares": metrics.shares,
                "saves": metrics.saves,
            }
    except Exception as e:
        logger.debug(f"[A/B采集] 获取 {platform}/{content_id} 指标失败: {e}")

    return None


def _determine_winner(results: list[dict], metric_key: str) -> str | None:
    """根据指标判定优胜变体
    
    规则：
    1. 选取指标最高的变体
    2. 如果最高的比第二名高出 10% 以上，直接判定
    3. 否则选择数据量（views）更大的
    """
    if not results or len(results) < 2:
        return None

    # 按主指标降序排列
    sorted_results = sorted(
        results,
        key=lambda r: r.get(metric_key, 0),
        reverse=True,
    )

    best = sorted_results[0]
    second = sorted_results[1]

    best_val = best.get(metric_key, 0)
    second_val = second.get(metric_key, 0)

    # 如果最佳变体有明显优势
    if best_val > 0 and (second_val == 0 or best_val / max(second_val, 0.0001) >= 1.1):
        return best.get("variant_id")

    # 如果指标接近，选 views 更高的
    if best.get("views", 0) >= second.get("views", 0):
        return best.get("variant_id")

    return best.get("variant_id")
