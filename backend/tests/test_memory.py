"""
Agent 记忆系统测试。

覆盖:
  - MemoryStore: 保存对话 / 查询上下文 / 保存修正 / 检索修正
  - POST /agent/feedback: 接收前端修正数据
  - 记忆注入到感知层 hints
  - 统计查询
"""
import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.agent.memory.integration import inject_memory_context, save_agent_memory
from app.agent.memory.store import MemoryStore
from app.agent.models import AgentResult, PerceptPacket
from app.agent.perception import process as perception
from app.database import get_db


class TestMemoryStore:
    """记忆存储层单元测试。"""

    def test_save_and_query_conversation(self, db_session: Session):
        store = MemoryStore(db_session)
        conv = store.save_conversation(
            session_id="test-session",
            raw_input="字节跳动 前端开发",
            intent="create_position",
            confidence=0.85,
            extracted={"company": "字节跳动", "position": "前端开发"},
        )
        assert conv.id > 0
        assert conv.intent == "create_position"

        # 查询最近对话
        recent = store.get_recent_context("test-session")
        assert len(recent) == 1
        assert recent[0]["intent"] == "create_position"

    def test_save_and_query_correction(self, db_session: Session):
        store = MemoryStore(db_session)

        # 先保存对话
        conv = store.save_conversation("s", "test input", "create_position", 0.7)

        # 再保存修正
        corr = store.save_correction(
            conversation_id=conv.id,
            session_id="s",
            field_name="company",
            original_value="字节跳动",
            corrected_value="字节",
        )
        assert corr.id > 0
        assert corr.corrected_value == "字节"

        # 查询修正
        corrections = store.get_corrections_for("s")
        assert len(corrections) == 1
        assert corrections[0]["field"] == "company"
        assert corrections[0]["corrected"] == "字节"

    def test_batch_save_corrections(self, db_session: Session):
        store = MemoryStore(db_session)
        conv = store.save_conversation("s", "test", "create_position", 0.7)

        saved = store.save_corrections_batch(conv.id, "s", {
            "company": ("字节跳动", "字节"),
            "position": ("前端开发", "前端开发工程师"),
            "base_location": (None, "北京"),  # unchanged, no save
        })
        # base_location: None → "北京" is a change, should be saved
        # Wait, original is None and corrected is "北京" — that IS a change
        assert len(saved) == 3

    def test_correction_stats(self, db_session: Session):
        store = MemoryStore(db_session)
        conv = store.save_conversation("s", "test", "create_position", 0.7)

        store.save_correction(conv.id, "s", "company", "字节", "字节跳动")
        store.save_correction(conv.id, "s", "position", "前端", "全栈")

        stats = store.get_correction_stats("s")
        assert stats["total_corrections"] == 2
        assert stats["fields_corrected"] >= 2

    def test_session_isolation(self, db_session: Session):
        """不同 session 的数据互不干扰。"""
        store = MemoryStore(db_session)
        store.save_conversation("session-a", "input A", "create", 0.5)
        store.save_conversation("session-b", "input B", "update", 0.5)

        ctx_a = store.get_recent_context("session-a")
        ctx_b = store.get_recent_context("session-b")

        assert len(ctx_a) == 1
        assert len(ctx_b) == 1
        assert ctx_a[0]["input"] == "input A"
        assert ctx_b[0]["input"] == "input B"


class TestMemoryIntegration:
    """记忆集成到 Agent 管线测试。"""

    def test_inject_memory_context(self, db_session: Session):
        """感知层后注入记忆上下文。"""
        # 先保存一些对话记录
        store = MemoryStore(db_session)
        store.save_conversation("test", "之前提到的字节", "create_position", 0.8)

        # 执行感知层
        packet = perception("字节跳动")
        packet = inject_memory_context(packet, "test", db_session)

        assert "recent_conversations" in packet.hints
        assert len(packet.hints["recent_conversations"]) == 1

    def test_save_agent_memory(self, db_session: Session):
        """管线结束后保存记忆。"""
        packet = perception("测试输入")
        result = AgentResult(
            action_type="create_position",
            action_label="新增",
            confidence=0.8,
            display_fields=[],
            needs_human_review=False,
            human_review_reason="",
            raw_input="测试输入",
            skill_results=[],
            total_latency_ms=0,
        )

        conv_id = save_agent_memory(packet, result, "test-session", db_session)
        assert conv_id > 0

        # 验证已保存
        store = MemoryStore(db_session)
        recent = store.get_recent_context("test-session")
        assert len(recent) == 1

    def test_save_memory_with_corrections(self, db_session: Session):
        """保存带修正的记忆。"""
        packet = perception("字节 前端")
        result = AgentResult(
            action_type="create_position",
            action_label="新增",
            confidence=0.7,
            display_fields=[],
            needs_human_review=False,
            human_review_reason="",
            raw_input="字节 前端",
            skill_results=[],
            total_latency_ms=0,
        )

        conv_id = save_agent_memory(
            packet, result, "test-session", db_session,
            corrections={
                "company": ("字节跳动", "字节"),
                "position": (None, "前端开发"),
            },
        )

        store = MemoryStore(db_session)
        corrections = store.get_corrections_for("test-session")
        assert len(corrections) == 2


class TestFeedbackAPI:
    """/api/agent/feedback 端点测试。"""

    def test_feedback_endpoint(self, client: TestClient, db_session: Session):
        """提交修正数据。"""
        # 先调一次 parse 获得 conversation_id
        parse_resp = client.post("/api/agent/parse", json={"text": "字节跳动 前端开发 25k 北京", "session_id": "fb-test"})
        assert parse_resp.status_code == 200
        conv_id = parse_resp.json()["conversation_id"]
        assert conv_id > 0

        # 提交修正
        resp = client.post("/api/agent/feedback", json={
            "conversation_id": conv_id,
            "session_id": "fb-test",
            "corrections": [
                {"field_name": "company", "original_value": "字节跳动", "corrected_value": "字节跳动有限公司"},
                {"field_name": "position", "original_value": "前端开发", "corrected_value": "资深前端开发"},
            ],
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["corrections_saved"] == 2

    def test_feedback_no_corrections(self, client: TestClient, db_session: Session):
        """无修正数据时返回 0。"""
        resp = client.post("/api/agent/feedback", json={
            "conversation_id": 1,
            "session_id": "test",
            "corrections": [],
        })
        assert resp.status_code == 200
        assert resp.json()["corrections_saved"] == 0
