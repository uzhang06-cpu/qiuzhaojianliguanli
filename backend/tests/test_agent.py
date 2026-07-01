"""
Phase 2 — Agent 智能体框架全链路测试。

覆盖:
  - MockLLMBackend 意图分类/实体提取/校验
  - 感知层 (Perception)
  - 规划层 (Planning)
  - 执行层 Skills (TextParser, ScheduleParser, DBOps)
  - 反思层 (Reflection)
  - Pipeline 端到端
  - API 端点
"""
from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from app.agent.execution import (
    DatabaseOpsSkill,
    ScheduleParsingSkill,
    SkillRegistry,
    TextParsingSkill,
)
from app.agent.llm import MockLLMBackend, set_llm_backend
from app.agent.models import IntentType, SkillType
from app.agent.perception import process as perception
from app.agent.planning import plan as planning
from app.agent.reflection import reflect as reflection

# ── Fixtures ─────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def _use_mock_backend():
    """所有测试使用 Mock 后端。"""
    set_llm_backend(MockLLMBackend())
    yield


@pytest.fixture
def registry():
    r = SkillRegistry()
    r.register(TextParsingSkill())
    r.register(ScheduleParsingSkill())
    r.register(DatabaseOpsSkill())
    return r


# ── MockLLMBackend 单元测试 ─────────────────────────────────────────


class TestMockLLMBackend:
    """规则引擎后端的单元测试。"""

    def setup_method(self):
        self.backend = MockLLMBackend()
        self.now = datetime(2026, 7, 1)  # Wednesday

    # -- 意图分类 --

    @pytest.mark.parametrize("text,intent", [
        ("字节跳动前端开发岗位 25k-40k 北京", IntentType.CREATE_POSITION),
        ("收到字节跳动二面通知下周三下午两点", IntentType.UPDATE_INTERVIEW),
        ("腾讯云智 后台开发 20k 西安", IntentType.CREATE_POSITION),
        ("今天下午3点腾讯会议面试", IntentType.UPDATE_INTERVIEW),
        ("刚才的面试体验很好，记录一下面经", IntentType.ADD_NOTES),
        ("阿里巴巴 前端 实习 杭州", IntentType.CREATE_POSITION),
    ])
    def test_classify_intent(self, text, intent):
        result_intent, conf, _ = self.backend.classify_intent(text, self.now)
        assert result_intent == intent, f"期望 {intent}，得到 {result_intent} (text={text})"
        assert conf > 0.0

    # -- 文本实体提取 --

    def test_extract_company(self):
        entities = self.backend.extract_entities(
            "字节跳动前端开发工程师 25k-40k 北京", SkillType.TEXT_PARSING, self.now
        )
        company = next((e for e in entities if e["field"] == "company"), None)
        assert company is not None
        assert "字节" in company["value"]

    def test_extract_salary(self):
        entities = self.backend.extract_entities(
            "薪资范围 30k-50k 16薪", SkillType.TEXT_PARSING, self.now
        )
        salary = next((e for e in entities if e["field"] == "salary_range"), None)
        assert salary is not None
        assert salary["value"] == "30k-50k"

    def test_extract_location(self):
        entities = self.backend.extract_entities(
            "base 深圳 腾讯", SkillType.TEXT_PARSING, self.now
        )
        loc = next((e for e in entities if e["field"] == "base_location"), None)
        assert loc is not None
        assert loc["value"] == "深圳"

    # -- 日程实体提取 --

    def test_extract_schedule_with_relative_time(self):
        """下周三下午两点 → 绝对时间 (当前是周三 2026-07-01)"""
        entities = self.backend.extract_entities(
            "下周三下午两点面试", SkillType.SCHEDULE_PARSING, self.now
        )
        ddl = next((e for e in entities if e["field"] == "next_ddl"), None)
        assert ddl is not None, f"未提取到时间: {entities}"
        # 当前 7月1日周三，下周三 = 7月8日
        assert "2026-07-08" in ddl["value"]
        assert "14:00" in ddl["value"]  # 下午2点

    def test_extract_schedule_with_platform(self):
        entities = self.backend.extract_entities(
            "飞书会议面试", SkillType.SCHEDULE_PARSING, self.now
        )
        platform = next((e for e in entities if e["field"] == "interview_platform"), None)
        assert platform is not None
        assert platform["value"] == "飞书"

    def test_extract_schedule_with_link(self):
        entities = self.backend.extract_entities(
            "腾讯会议链接 https://meeting.tencent.com/123",
            SkillType.SCHEDULE_PARSING, self.now
        )
        link = next((e for e in entities if e["field"] == "interview_link"), None)
        assert link is not None
        assert link["value"] == "https://meeting.tencent.com/123"

    def test_extract_schedule_tomorrow(self):
        """明天 → 7月2日"""
        entities = self.backend.extract_entities(
            "明天上午10点半面试", SkillType.SCHEDULE_PARSING, self.now
        )
        ddl = next((e for e in entities if e["field"] == "next_ddl"), None)
        assert ddl is not None
        assert "2026-07-02" in ddl["value"]
        assert "10:30" in ddl["value"]

    def test_extract_specific_date(self):
        """7月15日 → 2026-07-15"""
        entities = self.backend.extract_entities(
            "7月15日下午3点笔试", SkillType.SCHEDULE_PARSING, self.now
        )
        ddl = next((e for e in entities if e["field"] == "next_ddl"), None)
        assert ddl is not None
        assert "2026-07-15" in ddl["value"]

    # -- 校验 --

    def test_validate_missing_company(self):
        valid, data, error = self.backend.validate_and_fix(
            {"position": "前端"}, "create_position"
        )
        assert valid is False
        assert "公司" in error

    def test_validate_ok(self):
        valid, data, error = self.backend.validate_and_fix(
            {"company": "字节", "position": "前端"}, "create_position"
        )
        assert valid is True
        assert error is None


# ── 感知层测试 ───────────────────────────────────────────────────────


class TestPerception:
    """感知层单元测试。"""

    def test_basic_packet(self):
        packet = perception("  字节跳动 前端开发  ")
        assert packet.raw_input == "字节跳动 前端开发"
        assert packet.system_time is not None
        assert packet.hints["input_length"] == 9

    def test_url_detection(self):
        packet = perception("腾讯会议 https://meeting.tencent.com/123")
        assert packet.hints["has_url"] is True

    def test_time_ref_detection(self):
        packet = perception("下周三下午两点面试")
        assert packet.hints["has_time_ref"] is True


# ── 规划层测试 ───────────────────────────────────────────────────────


class TestPlanning:
    """规划层单元测试。"""

    def test_plan_create_position(self):
        packet = perception("字节跳动 前端开发 25k 北京")
        plan = planning(packet)
        assert plan.intent == IntentType.CREATE_POSITION
        assert SkillType.TEXT_PARSING in plan.required_skills
        assert SkillType.DB_OPS in plan.required_skills
        assert plan.confidence > 0.0

    def test_plan_update_interview(self):
        packet = perception("下周三下午两点字节二面")
        plan = planning(packet)
        assert plan.intent == IntentType.UPDATE_INTERVIEW
        assert SkillType.SCHEDULE_PARSING in plan.required_skills

    def test_plan_unknown_fallback(self):
        """非结构化短文本进入 UNKNOWN"""
        packet = perception("你好")
        plan = planning(packet)
        assert plan.intent == IntentType.UNKNOWN


# ── 执行层测试 ───────────────────────────────────────────────────────


class TestExecutionSkills:
    """执行层 Skills 单元测试。"""

    def test_text_parsing_skill(self, registry):
        packet = perception("字节跳动 前端开发 25k-40k 北京")
        plan = planning(packet)
        result = registry.execute_plan(plan, packet)
        assert SkillType.TEXT_PARSING in result
        tp_result = result[SkillType.TEXT_PARSING]
        assert tp_result.success is True
        fields = [e.field for e in tp_result.entities]
        assert "company" in fields

    def test_schedule_parsing_skill(self, registry):
        packet = perception("下周三下午两点腾讯会议面试")
        plan = planning(packet)
        result = registry.execute_plan(plan, packet)
        assert SkillType.SCHEDULE_PARSING in result
        sc_result = result[SkillType.SCHEDULE_PARSING]
        fields = [e.field for e in sc_result.entities]
        assert "next_ddl" in fields or "interview_platform" in fields

    def test_db_ops_creates_operation(self, registry):
        """DB Ops 应该生成操作指令。"""
        packet = perception("字节跳动 前端开发")
        plan = planning(packet)
        result = registry.execute_plan(plan, packet)
        assert SkillType.DB_OPS in result
        op_field = next(
            (e for e in result[SkillType.DB_OPS].entities if e.field == "operation"), None
        )
        assert op_field is not None
        operation = op_field.value
        assert operation["action"] == "create"


# ── 反思层测试 ───────────────────────────────────────────────────────


class TestReflection:
    """反思层单元测试。"""

    def test_reflection_create_position_ok(self):
        packet = perception("字节跳动 前端开发 25k 北京")
        plan = planning(packet)
        registry = SkillRegistry()
        registry.register(TextParsingSkill())
        registry.register(ScheduleParsingSkill())
        registry.register(DatabaseOpsSkill())
        results = registry.execute_plan(plan, packet)
        result = reflection(packet, plan, results)

        assert result.action_type == IntentType.CREATE_POSITION
        assert result.needs_human_review is False
        assert len(result.display_fields) > 0

    def test_reflection_unknown_triggers_review(self):
        packet = perception("随便说点啥")
        plan = planning(packet)
        results = {}
        result = reflection(packet, plan, results)

        assert result.needs_human_review is True


# ── Pipeline 端到端测试 ──────────────────────────────────────────────


class TestPipeline:
    """完整管线集成测试。"""

    def test_pipeline_create_position(self, client: TestClient):
        resp = client.post("/api/agent/parse", json={
            "text": "字节跳动 前端开发工程师 25k-40k 北京"
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        data = body["data"]
        assert data["action_type"] == IntentType.CREATE_POSITION.value
        assert data["needs_human_review"] is False
        # 应该有展示字段
        assert len(data["display_fields"]) > 0
        # 应该有公司名
        companies = [f for f in data["display_fields"] if f["key"] == "company"]
        assert len(companies) == 1
        assert "字节" in companies[0]["value"]

    def test_pipeline_update_interview(self, client: TestClient):
        resp = client.post("/api/agent/parse", json={
            "text": "字节跳动前端开发二面通知，下周三下午2点，腾讯会议链接 https://meeting.tencent.com/abc"
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        data = body["data"]
        assert data["action_type"] == IntentType.UPDATE_INTERVIEW.value
        # 应该提取到时间
        ddl_fields = [f for f in data["display_fields"] if f["key"] == "next_ddl"]
        assert len(ddl_fields) > 0

    def test_pipeline_unknown_triggers_review(self, client: TestClient):
        resp = client.post("/api/agent/parse", json={
            "text": "你好啊"
        })
        assert resp.status_code == 200
        body = resp.json()
        data = body["data"]
        assert data["needs_human_review"] is True

    def test_pipeline_empty_text_rejected(self, client: TestClient):
        resp = client.post("/api/agent/parse", json={"text": ""})
        assert resp.status_code == 422  # Validation error

    def test_pipeline_with_skill_details(self, client: TestClient):
        """结果中应包含各 Skill 的执行明细。"""
        resp = client.post("/api/agent/parse", json={
            "text": "字节跳动 前端开发 25k 北京"
        })
        data = resp.json()["data"]
        assert len(data["skill_results"]) > 0
        assert data["total_latency_ms"] > 0
