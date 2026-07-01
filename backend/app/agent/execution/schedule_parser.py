"""
日程解析 Skill (Schedule Parsing) — 提取面试/笔试时间与入会信息。

职责：
  - 解析相对时间（"下周二下午两点" → 绝对 Unix 时间戳）
  - 提取面试平台（腾讯会议、飞书等）
  - 提取入会链接
"""
from __future__ import annotations

from app.agent.execution.base import BaseSkill, SkillResult
from app.agent.llm import get_llm_backend
from app.agent.models import ExtractedEntity, PerceptPacket, Plan, SkillType


class ScheduleParsingSkill(BaseSkill):
    """日程解析技能。"""

    skill_type = SkillType.SCHEDULE_PARSING

    def execute(
        self,
        packet: PerceptPacket,
        plan: Plan,
        prev_results: dict[SkillType, SkillResult],
    ) -> SkillResult:
        llm = get_llm_backend()
        raw_entities = llm.extract_entities(
            packet.raw_input, SkillType.SCHEDULE_PARSING, packet.system_time
        )

        entities = []
        for item in raw_entities:
            entities.append(ExtractedEntity(
                field=item.get("field", ""),
                value=item.get("value"),
                confidence=item.get("confidence", 0.5),
                display_text=item.get("display_text", str(item.get("value", ""))),
            ))

        return SkillResult(
            skill=self.skill_type,
            success=True,  # 即使没提取到也视为成功（可能没有日程信息）
            entities=entities,
            raw_output=str([e.model_dump() for e in entities]),
        )
