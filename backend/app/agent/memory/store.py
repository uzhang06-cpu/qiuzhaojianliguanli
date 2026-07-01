"""
MemoryStore — 记忆存储核心。

功能 A (对话上下文):
  - save_conversation(): 保存每次 Agent 调用记录
  - get_recent_context(): 获取近期相关对话历史 → 注入到感知层

功能 B (纠错学习):
  - save_correction(): 保存用户修正数据
  - get_corrections_for(): 检索同公司/岗位的修正历史 → 注入到执行层
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.agent.memory.models import AgentConversation, AgentCorrection


class MemoryStore:
    """记忆存储层，依赖 SQLAlchemy Session。"""

    def __init__(self, db: Session):
        self.db = db

    # ── 通道 A：对话上下文 ────────────────────────────────────────

    def save_conversation(
        self,
        session_id: str,
        raw_input: str,
        intent: str,
        confidence: float,
        extracted: Optional[dict] = None,
        had_correction: bool = False,
    ) -> AgentConversation:
        """保存一次 Agent 调用记录。"""
        # 安全序列化：确保 extracted 中的所有值都可 JSON 序列化
        extracted_json = None
        if extracted is not None:
            try:
                extracted_json = json.dumps(extracted, ensure_ascii=False, default=str)
            except (TypeError, ValueError) as e:
                # 降级：将不可序列化的值转字符串
                sanitized = {
                    k: str(v) if not isinstance(v, (str, int, float, bool, type(None), list, dict))
                    else v for k, v in extracted.items()
                }
                extracted_json = json.dumps(sanitized, ensure_ascii=False, default=str)

        conv = AgentConversation(
            session_id=session_id,
            raw_input=raw_input,
            intent=intent,
            confidence=int(confidence * 100),
            extracted_json=extracted_json,
            had_correction=1 if had_correction else 0,
        )
        self.db.add(conv)
        self.db.commit()
        self.db.refresh(conv)
        return conv

    def get_recent_context(
        self,
        session_id: str,
        limit: int = 5,
        hours: int = 24,
    ) -> list[dict]:
        """获取近期对话历史，用于注入到感知层上下文。"""
        cutoff = datetime.now() - timedelta(hours=hours)
        rows = (
            self.db.query(AgentConversation)
            .filter(
                AgentConversation.session_id == session_id,
                AgentConversation.created_at >= cutoff,
            )
            .order_by(AgentConversation.created_at.desc())
            .limit(limit)
            .all()
        )

        return [
            {
                "id": r.id,
                "input": r.raw_input[:200],
                "intent": r.intent,
                "confidence": r.confidence,
                "time": r.created_at.isoformat(),
            }
            for r in rows
        ]

    # ── 通道 B：纠错学习 ──────────────────────────────────────────

    def save_correction(
        self,
        conversation_id: int,
        session_id: str,
        field_name: str,
        original_value: Optional[str],
        corrected_value: str,
    ) -> AgentCorrection:
        """保存一条用户修正记录。"""
        corr = AgentCorrection(
            conversation_id=conversation_id,
            session_id=session_id,
            field_name=field_name,
            original_value=original_value,
            corrected_value=corrected_value,
        )
        self.db.add(corr)
        self.db.commit()
        self.db.refresh(corr)
        return corr

    def save_corrections_batch(
        self,
        conversation_id: int,
        session_id: str,
        corrections: dict[str, tuple[Optional[str], str]],
    ) -> list[AgentCorrection]:
        """批量保存修正记录。

        参数:
            corrections: { field_name: (original_value, corrected_value) }
        """
        saved = []
        for field_name, (original, corrected) in corrections.items():
            if original != corrected:  # 只有真正改了才记
                c = self.save_correction(
                    conversation_id=conversation_id,
                    session_id=session_id,
                    field_name=field_name,
                    original_value=original,
                    corrected_value=corrected,
                )
                saved.append(c)
        return saved

    def get_corrections_for(
        self,
        session_id: str,
        limit: int = 20,
        hours: int = 168,  # 7 天
    ) -> list[dict]:
        """获取近期修正记录，用于注入到执行层提示词。"""
        cutoff = datetime.now() - timedelta(hours=hours)
        rows = (
            self.db.query(AgentCorrection)
            .filter(
                AgentCorrection.session_id == session_id,
                AgentCorrection.created_at >= cutoff,
            )
            .order_by(AgentCorrection.created_at.desc())
            .limit(limit)
            .all()
        )

        return [
            {
                "field": r.field_name,
                "original": r.original_value,
                "corrected": r.corrected_value,
                "time": r.created_at.isoformat(),
            }
            for r in rows
        ]

    def get_correction_stats(self, session_id: str) -> dict:
        """获取纠错统计。"""
        total = (
            self.db.query(AgentCorrection)
            .filter(AgentCorrection.session_id == session_id)
            .count()
        )
        by_field = (
            self.db.query(AgentCorrection.field_name)
            .filter(AgentCorrection.session_id == session_id)
            .distinct()
            .count()
        )
        return {"total_corrections": total, "fields_corrected": by_field}
