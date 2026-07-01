"""
文本解析 Skill (Text Parsing) — 从岗位描述/JD 中提取结构化信息。

职责：
  - 提取公司名、岗位名
  - 提取薪资范围、Base 地
  - 提取核心能力要求
"""
from __future__ import annotations

from app.agent.execution.base import BaseSkill, SkillResult
from app.agent.llm import get_llm_backend
from app.agent.models import ExtractedEntity, PerceptPacket, Plan, SkillType


class TextParsingSkill(BaseSkill):
    """文本解析技能。"""

    skill_type = SkillType.TEXT_PARSING

    def execute(
        self,
        packet: PerceptPacket,
        plan: Plan,
        prev_results: dict[SkillType, SkillResult],
    ) -> SkillResult:
        llm = get_llm_backend()
        raw_entities = llm.extract_entities(
            packet.raw_input, SkillType.TEXT_PARSING, packet.system_time
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
            success=len(entities) > 0,
            entities=entities,
            raw_output=str([e.model_dump() for e in entities]),
            error=None if len(entities) > 0 else "未能提取任何文本实体",
        )
