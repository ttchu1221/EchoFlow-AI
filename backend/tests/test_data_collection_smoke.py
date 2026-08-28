from __future__ import annotations

import asyncio
import copy
import os
import sys
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class FakeInsertResult:
    def __init__(self, inserted_id):
        self.inserted_id = inserted_id


class FakeCursor:
    def __init__(self, docs):
        self.docs = [copy.deepcopy(doc) for doc in docs]

    def sort(self, key, direction):
        reverse = direction < 0
        self.docs.sort(key=lambda doc: doc.get(key) is None or doc.get(key), reverse=reverse)
        return self

    def skip(self, count):
        self.docs = self.docs[count:]
        return self

    def limit(self, count):
        self.docs = self.docs[:count]
        return self

    async def to_list(self, length=None):
        return self.docs[:length] if length else self.docs

    def __aiter__(self):
        self._iter = iter(self.docs)
        return self

    async def __anext__(self):
        try:
            return next(self._iter)
        except StopIteration as exc:
            raise StopAsyncIteration from exc


class FakeCollection:
    def __init__(self):
        self.docs = []
        self.next_id = 1

    async def create_index(self, *args, **kwargs):
        return "ok"

    async def insert_one(self, doc):
        stored = copy.deepcopy(doc)
        stored.setdefault("_id", str(self.next_id))
        self.next_id += 1
        self.docs.append(stored)
        return FakeInsertResult(stored["_id"])

    async def find_one(self, query):
        for doc in self.docs:
            if self._matches(doc, query):
                return copy.deepcopy(doc)
        return None

    async def update_one(self, query, update, upsert=False):
        for doc in self.docs:
            if self._matches(doc, query):
                if "$set" in update:
                    doc.update(copy.deepcopy(update["$set"]))
                if "$inc" in update:
                    for key, value in update["$inc"].items():
                        doc[key] = doc.get(key, 0) + value
                return SimpleNamespace(modified_count=1)
        if upsert:
            new_doc = copy.deepcopy(query)
            new_doc.update(copy.deepcopy(update.get("$set", {})))
            await self.insert_one(new_doc)
        return SimpleNamespace(modified_count=0)

    async def count_documents(self, query):
        return sum(1 for doc in self.docs if self._matches(doc, query))

    def find(self, query=None, projection=None):
        query = query or {}
        matched = []
        for doc in self.docs:
            if self._matches(doc, query):
                selected = copy.deepcopy(doc)
                if projection:
                    selected = self._project(selected, projection)
                matched.append(selected)
        return FakeCursor(matched)

    def _matches(self, doc, query):
        for key, expected in query.items():
            actual = self._get(doc, key)
            if isinstance(expected, dict):
                if "$gte" in expected and not (actual and actual >= expected["$gte"]):
                    return False
                continue
            if actual != expected:
                return False
        return True

    def _project(self, doc, projection):
        if all(value == 0 for value in projection.values()):
            for key, value in projection.items():
                if value == 0:
                    doc.pop(key, None)
            return doc
        selected = {}
        for key, value in projection.items():
            if value:
                current = self._get(doc, key)
                if current is not None:
                    self._set(selected, key, current)
        return selected

    def _get(self, doc, key):
        current = doc
        for part in key.split("."):
            if not isinstance(current, dict):
                return None
            current = current.get(part)
        return current

    def _set(self, doc, key, value):
        current = doc
        parts = key.split(".")
        for part in parts[:-1]:
            current = current.setdefault(part, {})
        current[parts[-1]] = value


class FakeDB(dict):
    def __getitem__(self, name):
        if name not in self:
            self[name] = FakeCollection()
        return dict.__getitem__(self, name)


async def main():
    os.environ["SMART_COLLECTION_USE_LLM"] = "false"

    import crawlers.data_source as data_source
    import data_collection.router as router
    import data_collection.service as service
    import data_collection.smart_query as smart_query
    import memory

    fake_db = FakeDB()
    memory.db = fake_db

    async def fake_hot_search(platform, limit=30):
        return [
            {
                "keyword": f"{platform} 护肤热点",
                "title": "夏季护肤降温喷雾爆发",
                "heat_score": "12万",
                "url": "https://example.com/hot/1",
            },
            {
                "keyword": f"{platform} 防晒",
                "title": "通勤防晒补涂技巧",
                "heat_score": 88000,
                "url": "https://example.com/hot/2",
            },
        ][:limit]

    async def fake_competitor_content(platform, account_id, account_name, limit=20):
        return [
            {
                "platform_content_id": "video-001",
                "title": f"{account_name} 爆款短视频",
                "account_name": account_name,
                "views": "3.5万",
                "likes": 2600,
                "url": "https://example.com/video/001",
            },
            {
                "platform_content_id": "video-002",
                "title": f"{account_name} 新品测评",
                "account_name": account_name,
                "views": 42000,
                "likes": 3100,
                "url": "https://example.com/video/002",
            },
        ][:limit]

    data_source.fetch_hot_search = fake_hot_search
    router.fetch_hot_search = fake_hot_search
    smart_query.fetch_hot_search = fake_hot_search

    import competitor.crawler as competitor_crawler

    competitor_crawler.fetch_competitor_content = fake_competitor_content

    await service.ensure_indexes()

    hot_plan = smart_query.infer_collection_plan("最近小红书护肤有什么热点？")
    assert hot_plan["platform"] == "xiaohongshu"
    assert hot_plan["source_type"] == "hot_search"

    hot_result = await smart_query.answer_with_auto_collection("最近小红书护肤有什么热点？")
    assert hot_result["collection"]["items_recorded"] == 2
    assert hot_result["evidence"]
    assert "已围绕" in hot_result["answer"]

    competitor_plan = smart_query.infer_collection_plan("帮我看抖音竞品账号 张三 最近内容表现")
    assert competitor_plan["platform"] == "douyin"
    assert competitor_plan["source_type"] == "competitor_content"
    assert competitor_plan["account_name"] == "张三"

    keyword_plan = smart_query.infer_collection_plan("找珀莱雅的东西在抖音相关的内容")
    assert keyword_plan["platform"] == "douyin"
    assert keyword_plan["source_type"] == "keyword_content"
    assert keyword_plan["keyword"] == "珀莱雅"

    ecommerce_keyword_cases = [
        ("我想看珀莱雅在抖音的内容", "douyin", "珀莱雅"),
        ("珀莱雅 抖音 内容", "douyin", "珀莱雅"),
        ("抖音 珀莱雅 双抗水乳", "douyin", "珀莱雅 双抗水乳"),
        ("帮我查一下抖音上珀莱雅双抗水乳相关视频", "douyin", "珀莱雅双抗水乳"),
        ("小红书双抗水乳爆款笔记", "xiaohongshu", "双抗水乳爆款"),
        ("看看韩束官方旗舰店最近抖音作品", "douyin", "韩束官方旗舰店"),
    ]
    for question, expected_platform, expected_keyword in ecommerce_keyword_cases:
        plan = smart_query.infer_collection_plan(question)
        assert plan["platform"] == expected_platform, question
        assert plan["source_type"] == "keyword_content", question
        assert plan["keyword"] == expected_keyword, question

    generic_hot_plan = smart_query.infer_collection_plan("最近小红书护肤有什么热点？")
    assert generic_hot_plan["platform"] == "xiaohongshu"
    assert generic_hot_plan["source_type"] == "hot_search"

    quoted_keyword_plan = smart_query.infer_collection_plan("毫无关联，用`找珀莱雅的东西在抖音相关的内容`这个")
    assert quoted_keyword_plan["source_type"] == "keyword_content"
    assert quoted_keyword_plan["keyword"] == "珀莱雅"

    first = await smart_query.answer_with_auto_collection("帮我看抖音竞品账号 张三 最近内容表现")
    second = await smart_query.answer_with_auto_collection("帮我看抖音竞品账号 张三 最近内容表现")
    assert first["collection"]["items_recorded"] == 2
    assert second["collection"]["duplicates"] >= 2

    keyword_result = await smart_query.answer_with_auto_collection("找珀莱雅的东西在抖音相关的内容")
    assert keyword_result["collection"]["items_recorded"] == 2
    assert keyword_result["collection"]["duplicates"] == 2
    assert keyword_result["evidence"]
    assert "珀莱雅" in keyword_result["answer"]

    overview = await service.overview(7)
    assert overview["raw_events"] == 8
    assert overview["standard_contents"] == 4
    assert overview["avg_quality"] > 0.7

    quality = await router.quality_report(current_user={"username": "tester"})
    assert quality["code"] == 200
    assert quality["data"]["sample_size"] == 4

    print("data_collection_smoke: ok")
    print({
        "hot_collection": hot_result["collection"],
        "competitor_collection": second["collection"],
        "keyword_collection": keyword_result["collection"],
        "overview": overview,
        "quality": quality["data"],
    })


if __name__ == "__main__":
    asyncio.run(main())
