"""
反思层 (Reflection) — 结果约束与质量检验防线。

职责：
  1. 校验执行层输出的数据是否完整合规
  2. 核心字段缺失时打回重试（暂未实现自动重试）
  3. 重试失败后降级标记 Needs_Human_Review
  4. 构造前端友好的 DisplayField 列表
"""
from __future__ import annotations

from typing import Optional

from app.agent.llm import get_llm_backend
from app.agent.models import (
    AgentResult,
    DisplayField,
    IntentType,
    PerceptPacket,
    Plan,
    SkillResult,
    SkillType,
)

# 每个意图对应的「核心字段」
CORE_FIELDS: dict[IntentType, list[str]] = {
    IntentType.CREATE_POSITION: ["company", "position"],
    IntentType.UPDATE_INTERVIEW: ["next_ddl"],
    IntentType.UPDATE_STATUS: ["status"],
    IntentType.ADD_NOTES: [],  # 复盘无强制字段
    IntentType.QUERY: [],
    IntentType.UNKNOWN: [],
}

# 字段 → 展示标签映射
FIELD_LABELS: dict[str, str] = {
    "company": "公司名称",
    "position": "岗位名称",
    "base_location": "Base 地",
    "salary_range": "薪资范围",
    "next_ddl": "面试时间",
    "interview_link": "面试链接",
    "interview_platform": "面试平台",
    "status": "状态",
    "notes": "复盘笔记",
}


def reflect(
    packet: PerceptPacket,
    plan: Plan,
    skill_results: dict[SkillType, SkillResult],
) -> AgentResult:
    """
    反思入口：校验执行结果，构造前端展示数据。

    流程：
      1. 合并所有 Skill 提取的实体
      2. 校验核心字段完整性
      3. 构造 DisplayField 列表
      4. 必要时标记 needs_human_review
    """
    # 1. 合并实体
    merged = _merge_entities(skill_results)

    # 2. 校验核心字段
    core_fields = CORE_FIELDS.get(plan.intent, [])
    missing_fields = [f for f in core_fields if not merged.get(f)]
    all_valid = len(missing_fields) == 0

    # 3. 构造展示字段
    display_fields = _build_display_fields(merged, plan.intent)

    # 4. 标记缺失字段
    for field_name in missing_fields:
        for df in display_fields:
            if df.key == field_name:
                df.highlight = True

    # 5. 是否需要人工审核
    needs_review = False
    review_reason = ""

    if plan.intent == IntentType.UNKNOWN:
        needs_review = True
        review_reason = "无法识别意图，请手动选择操作类型"
    elif not all_valid and plan.confidence < 0.5:
        needs_review = True
        review_reason = f"关键字段缺失且置信度较低: {', '.join(missing_fields)}"
    elif not all_valid:
        # 高置信度但缺字段 — 按 PRD 描述打回重试（此处简化，直接降级）
        needs_review = True
        review_reason = f"关键字段缺失，需人工补充: {', '.join(missing_fields)}"

    return AgentResult(
        action_type=plan.intent,
        action_label=plan.intent.value,  # 前端自己映射中文
        confidence=plan.confidence,
        position_id=plan.position_id_hint,
        display_fields=display_fields,
        needs_human_review=needs_review,
        human_review_reason=review_reason,
        raw_input=packet.raw_input,
        skill_results=list(skill_results.values()),
    )


def _merge_entities(
    skill_results: dict[SkillType, SkillResult],
) -> dict:
    """合并所有 Skill 的实体数据，后面的覆盖前面的。"""
    merged: dict = {}
    for sr in skill_results.values():
        for entity in sr.entities:
            if entity.value is not None:
                # DB_OPS 的 operation 和 position_id 不参与预填数据展示
                if entity.field not in ("operation", "position_id"):
                    merged[entity.field] = entity.value
    return merged


def _build_display_fields(
    data: dict,
    intent: IntentType,
    confidence: float = 0.8,
) -> list[DisplayField]:
    """根据合并后的数据构造展示字段列表。"""
    fields = []

    # 按意图决定字段顺序
    if intent == IntentType.CREATE_POSITION:
        field_order = ["company", "position", "base_location", "salary_range", "next_ddl"]
    elif intent == IntentType.UPDATE_INTERVIEW:
        field_order = ["next_ddl", "interview_platform", "interview_link"]
    else:
        field_order = list(data.keys())

    for key in field_order:
        if key in data:
            fields.append(DisplayField(
                key=key,
                label=FIELD_LABELS.get(key, key),
                value=data[key],
                confidence=confidence,
                editable=True,
                highlight=False,
            ))

    return fields
