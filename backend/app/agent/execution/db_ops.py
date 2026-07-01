"""
DB 操作 Skill (Database Ops) — 数据库增删改查操作。

职责：
  - 根据感知层和规划层的结果，构造数据库操作
  - 在每次状态流转时强制向 StatusLog 写入变更日志
  - 当前返回结构化指令描述，由 Router 层实际执行
"""
from __future__ import annotations

from typing import Any

from app.agent.execution.base import BaseSkill
from app.agent.models import (
    ExtractedEntity,
    IntentType,
    PerceptPacket,
    Plan,
    SkillResult,
    SkillType,
)


class DatabaseOpsSkill(BaseSkill):
    """数据库操作技能 — 生成操作指令而非直接写库。"""

    skill_type = SkillType.DB_OPS

    def execute(
        self,
        packet: PerceptPacket,
        plan: Plan,
        prev_results: dict[SkillType, SkillResult],
    ) -> SkillResult:
        # 合并所有前序 Skill 的提取结果
        all_entities: dict[str, Any] = {}
        for sr in prev_results.values():
            for entity in sr.entities:
                all_entities[entity.field] = entity.value

        # 根据意图构造操作指令
        operation = self._build_operation(plan.intent, all_entities, packet)

        return SkillResult(
            skill=self.skill_type,
            success=True,
            entities=[
                ExtractedEntity(
                    field="operation",
                    value=operation,
                    confidence=1.0,
                    display_text=self._operation_summary(operation),
                ),
                ExtractedEntity(
                    field="position_id",
                    value=plan.position_id_hint,
                    confidence=0.9 if plan.position_id_hint else 0.0,
                    display_text=str(plan.position_id_hint or "新岗位"),
                ),
            ],
            raw_output=str(operation),
        )

    def _build_operation(
        self,
        intent: IntentType,
        entities: dict[str, Any],
        packet: PerceptPacket,
    ) -> dict:
        """根据意图和数据构造操作指令字典。"""
        base = {
            "intent": intent.value,
            "position_id": entities.get("position_id"),
            "timestamp": packet.system_time.isoformat(),
        }

        if intent == IntentType.CREATE_POSITION:
            return {
                **base,
                "action": "create",
                "data": {
                    "company": entities.get("company"),
                    "position": entities.get("position"),
                    "status": "interested",
                    "base_location": entities.get("base_location"),
                    "salary_range": entities.get("salary_range"),
                    "job_description": packet.raw_input,
                },
            }

        if intent == IntentType.UPDATE_INTERVIEW:
            return {
                **base,
                "action": "update",
                "data": {
                    "next_ddl": entities.get("next_ddl"),
                    "interview_link": entities.get("interview_link"),
                    "interview_platform": entities.get("interview_platform"),
                },
            }

        if intent == IntentType.UPDATE_STATUS:
            return {
                **base,
                "action": "update_status",
                "data": {
                    "status": entities.get("status"),
                },
            }

        if intent == IntentType.ADD_NOTES:
            return {
                **base,
                "action": "update",
                "data": {
                    "notes": packet.raw_input,
                },
            }

        return {**base, "action": "noop", "data": {}}

    def _operation_summary(self, op: dict) -> str:
        action = op.get("action", "unknown")
        summaries = {
            "create": "📝 新增岗位",
            "update": "✏️ 更新信息",
            "update_status": "🔄 变更状态",
            "noop": "⏭️ 无需操作",
        }
        return summaries.get(action, "❓ 未知操作")
