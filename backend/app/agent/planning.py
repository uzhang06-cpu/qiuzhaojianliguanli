"""
规划层 (Planning) — 系统的「路由大脑」。

职责：
  1. 接收 PerceptPacket
  2. 调用 LLM 后端进行意图分类
  3. 根据意图编排 Skill 执行链路
  4. 输出 Plan
"""
from __future__ import annotations

import re

from app.agent.llm import get_llm_backend
from app.agent.models import (
    IntentType,
    PerceptPacket,
    Plan,
    SkillType,
)

# 意图 → Skill 编排映射
_INTENT_SKILL_MAP: dict[IntentType, list[SkillType]] = {
    IntentType.CREATE_POSITION: [
        SkillType.TEXT_PARSING,
        SkillType.SCHEDULE_PARSING,
        SkillType.DB_OPS,
    ],
    IntentType.UPDATE_INTERVIEW: [
        SkillType.SCHEDULE_PARSING,
        SkillType.DB_OPS,
    ],
    IntentType.UPDATE_STATUS: [
        SkillType.TEXT_PARSING,
        SkillType.DB_OPS,
    ],
    IntentType.ADD_NOTES: [
        SkillType.DB_OPS,
    ],
    IntentType.QUERY: [
        SkillType.DB_OPS,
    ],
    IntentType.UNKNOWN: [],
}


def plan(packet: PerceptPacket) -> Plan:
    """
    规划入口：对感知包进行意图分析并编排执行计划。

    策略：
      1. 先用 LLM 后端进行意图分类
      2. 尝试从文本中解析关联的 position_id（如 "更新xxx岗位"）
      3. 根据意图编排 Skill 列表
    """
    llm = get_llm_backend()
    intent, confidence, raw_intent = llm.classify_intent(
        packet.raw_input, packet.system_time
    )

    # 兜底：LLM 返回 UNKNOWN 但输入包含明显的时间/面试信息
    if intent == IntentType.UNKNOWN and confidence < 0.5:
        if packet.hints.get("has_time_ref") or packet.hints.get("has_url"):
            intent = IntentType.UPDATE_INTERVIEW
            confidence = max(confidence, 0.4)
            raw_intent = "根据时间/链接线索推测为更新面试信息"
        elif packet.hints.get("input_length", 0) > 20:
            intent = IntentType.CREATE_POSITION
            confidence = max(confidence, 0.3)
            raw_intent = "输入较长，推测为新增岗位线索"

    required_skills = _INTENT_SKILL_MAP.get(intent, [])
    position_id_hint = _extract_position_id(packet.raw_input)

    return Plan(
        intent=intent,
        confidence=confidence,
        required_skills=required_skills,
        position_id_hint=position_id_hint,
        raw_intent=raw_intent,
    )


def _extract_position_id(text: str) -> int | None:
    """
    尝试从输入中提取关联的岗位 ID。
    格式: #123 或 id=123
    """
    m = re.search(r"[##](\d+)", text)
    if m:
        return int(m.group(1))
    m = re.search(r"id[=:](\d+)", text, re.IGNORECASE)
    if m:
        return int(m.group(1))
    return None
