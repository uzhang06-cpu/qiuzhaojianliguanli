"""
Pipeline 状态定义 — 秋招求职管线的七个状态节点。

每个状态对应一个中英文标识，直观映射到看板视图的列。
"""
from __future__ import annotations

from enum import Enum


class PipelineStatus(str, Enum):
    """求职管线的标准状态枚举。"""

    INTERESTED = "interested"          # 意向待投 — 发现线索，尚未网申
    APPLIED = "applied"                # 已投递 — 完成网申，简历初筛阶段
    ASSESSMENT = "assessment"          # 笔试 / 测评 — 行测、性格测试或专业笔试
    AI_INTERVIEW = "ai_interview"      # AI面 — 机器单向录制面试
    HUMAN_INTERVIEW = "human_interview"  # 人工面试 — 一面、二面、HR面、交叉面
    OFFER_EVALUATION = "offer_evaluation"  # Offer 评估 — 收到口头/正式 Offer
    ARCHIVED = "archived"              # 归档池 — 终止状态

    @property
    def label_cn(self) -> str:
        return LABEL_MAP[self]

    @property
    def order(self) -> int:
        return ORDER_MAP[self]

    @property
    def is_terminal(self) -> bool:
        """是否为终止状态（归档池）。"""
        return self == PipelineStatus.ARCHIVED


LABEL_MAP = {
    PipelineStatus.INTERESTED: "意向待投",
    PipelineStatus.APPLIED: "已投递",
    PipelineStatus.ASSESSMENT: "笔试 / 测评",
    PipelineStatus.AI_INTERVIEW: "AI面",
    PipelineStatus.HUMAN_INTERVIEW: "人工面试",
    PipelineStatus.OFFER_EVALUATION: "Offer 评估",
    PipelineStatus.ARCHIVED: "归档池",
}

ORDER_MAP = {
    PipelineStatus.INTERESTED: 0,
    PipelineStatus.APPLIED: 1,
    PipelineStatus.ASSESSMENT: 2,
    PipelineStatus.AI_INTERVIEW: 3,
    PipelineStatus.HUMAN_INTERVIEW: 4,
    PipelineStatus.OFFER_EVALUATION: 5,
    PipelineStatus.ARCHIVED: 6,
}
