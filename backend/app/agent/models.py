"""
Agent 系统数据模型 — 定义四层管线之间的通信契约。
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# ── 意图枚举 ─────────────────────────────────────────────────────────


class IntentType(str, Enum):
    """用户输入意图分类。"""

    CREATE_POSITION = "create_position"          # 新增岗位线索
    UPDATE_STATUS = "update_status"              # 变更状态
    UPDATE_INTERVIEW = "update_interview"        # 更新面试时间/链接
    ADD_NOTES = "add_notes"                      # 记录复盘总结
    QUERY = "query"                              # 查询岗位信息
    UNKNOWN = "unknown"                          # 无法识别


INTENT_LABELS = {
    IntentType.CREATE_POSITION: "新增岗位线索",
    IntentType.UPDATE_STATUS: "变更状态",
    IntentType.UPDATE_INTERVIEW: "更新面试信息",
    IntentType.ADD_NOTES: "记录复盘",
    IntentType.QUERY: "查询信息",
    IntentType.UNKNOWN: "无法识别",
}


# ── 执行层 Skill 枚举 ────────────────────────────────────────────────


class SkillType(str, Enum):
    """原子化执行技能。"""

    TEXT_PARSING = "text_parsing"            # 文本解析（JD 提取）
    SCHEDULE_PARSING = "schedule_parsing"    # 日程解析（时间/平台/链接）
    DB_OPS = "db_ops"                        # 数据库操作
    OUTREACH = "outreach"                    # 自动化触达（预留）


# ── 感知层 (Perception) ─────────────────────────────────────────────


class PerceptPacket(BaseModel):
    """感知层输出 — 经过包装的结构化输入包。"""

    raw_input: str = Field(..., description="用户原始输入文本")
    system_time: datetime = Field(..., description="感知时的系统时间")
    processed_text: str = Field("", description="清洗后的文本")
    hints: dict[str, Any] = Field(default_factory=dict, description="附加线索")


# ── 规划层 (Planning) ───────────────────────────────────────────────


class Plan(BaseModel):
    """规划层输出 — 意图 + 执行计划。"""

    intent: IntentType = Field(..., description="识别的意图")
    confidence: float = Field(..., ge=0.0, le=1.0, description="置信度")
    required_skills: list[SkillType] = Field(..., description="需要调用的 Skill 列表")
    position_id_hint: Optional[int] = Field(None, description="关联岗位 ID（如果可推断）")
    raw_intent: str = Field("", description="意图原始描述")


# ── 执行层输出项 ─────────────────────────────────────────────────────


class ExtractedEntity(BaseModel):
    """执行层提取的单个实体项。"""

    field: str = Field(..., description="字段名")
    value: Any = Field(None, description="提取的值")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="提取置信度")
    display_text: str = Field("", description="用于前端展示的文本")


class SkillResult(BaseModel):
    """单个 Skill 的执行结果。"""

    skill: SkillType = Field(..., description="技能类型")
    success: bool = Field(True, description="是否成功")
    entities: list[ExtractedEntity] = Field(default_factory=list, description="提取的实体")
    raw_output: str = Field("", description="原始输出文本")
    error: Optional[str] = Field(None, description="错误信息")


# ── 反思层输出 ───────────────────────────────────────────────────────


class DisplayField(BaseModel):
    """前端预填确认表单的单个字段。"""

    key: str = Field(..., description="字段标识")
    label: str = Field(..., description="前端展示标签")
    value: Any = Field(None, description="值")
    confidence: float = Field(1.0, description="置信度，低于阈值则高亮提醒")
    editable: bool = Field(True, description="是否允许编辑")
    highlight: bool = Field(False, description="是否需要用户关注确认")


class AgentResult(BaseModel):
    """Agent 管线最终输出 — 前端可以直接消费。"""

    action_type: IntentType = Field(..., description="确定的动作类型")
    action_label: str = Field("", description="动作中文描述")

    confidence: float = Field(0.0, ge=0.0, le=1.0, description="整体置信度")
    position_id: Optional[int] = Field(None, description="关联的岗位 ID")

    # 预填数据（用于确认表单）
    display_fields: list[DisplayField] = Field(
        default_factory=list, description="前端展示字段列表"
    )

    # 是否需要人工审核
    needs_human_review: bool = Field(False, description="是否降级为人工填写")
    human_review_reason: str = Field("", description="降级原因")
    raw_input: str = Field("", description="原始输入（降级时回传）")

    # 执行元信息
    skill_results: list[SkillResult] = Field(
        default_factory=list, description="各 Skill 执行明细"
    )
    total_latency_ms: float = Field(0.0, description="管线总耗时")
