"""
状态机引擎 — 定义 Pipeline 状态下允许的流转规则。

规则遵循「单向为主、允许回退」的原则：
  - 允许向前流转（跳过中间状态也允许，如 applied → human_interview）
  - 允许回退到相邻的上一个状态
  - 归档池为终止状态，但允许重新激活回 interested
"""
from __future__ import annotations

from dataclasses import dataclass, field

from app.engine.pipeline import PipelineStatus


# ── 显式定义所有允许的 (from → to) 转移 ──────────────────────────────
# 使用集合以便 O(1) 查询
_TRANSITIONS: set[tuple[PipelineStatus, PipelineStatus]] = {
    # --- 向前流转（允许跳过中间状态）---
    # interested 可跳转到任何非终止状态
    (PipelineStatus.INTERESTED, PipelineStatus.APPLIED),
    (PipelineStatus.INTERESTED, PipelineStatus.ASSESSMENT),
    (PipelineStatus.INTERESTED, PipelineStatus.AI_INTERVIEW),
    (PipelineStatus.INTERESTED, PipelineStatus.HUMAN_INTERVIEW),
    (PipelineStatus.INTERESTED, PipelineStatus.OFFER_EVALUATION),
    (PipelineStatus.INTERESTED, PipelineStatus.ARCHIVED),
    # applied 向前
    (PipelineStatus.APPLIED, PipelineStatus.ASSESSMENT),
    (PipelineStatus.APPLIED, PipelineStatus.AI_INTERVIEW),
    (PipelineStatus.APPLIED, PipelineStatus.HUMAN_INTERVIEW),
    (PipelineStatus.APPLIED, PipelineStatus.OFFER_EVALUATION),
    (PipelineStatus.APPLIED, PipelineStatus.ARCHIVED),
    # assessment 向前
    (PipelineStatus.ASSESSMENT, PipelineStatus.AI_INTERVIEW),
    (PipelineStatus.ASSESSMENT, PipelineStatus.HUMAN_INTERVIEW),
    (PipelineStatus.ASSESSMENT, PipelineStatus.OFFER_EVALUATION),
    (PipelineStatus.ASSESSMENT, PipelineStatus.ARCHIVED),
    # ai_interview 向前
    (PipelineStatus.AI_INTERVIEW, PipelineStatus.HUMAN_INTERVIEW),
    (PipelineStatus.AI_INTERVIEW, PipelineStatus.OFFER_EVALUATION),
    (PipelineStatus.AI_INTERVIEW, PipelineStatus.ARCHIVED),
    # human_interview 向前
    (PipelineStatus.HUMAN_INTERVIEW, PipelineStatus.OFFER_EVALUATION),
    (PipelineStatus.HUMAN_INTERVIEW, PipelineStatus.ARCHIVED),
    # offer_evaluation 向前
    (PipelineStatus.OFFER_EVALUATION, PipelineStatus.ARCHIVED),
    # --- 回退（允许退到相邻前序状态）---
    (PipelineStatus.APPLIED, PipelineStatus.INTERESTED),
    (PipelineStatus.ASSESSMENT, PipelineStatus.APPLIED),
    (PipelineStatus.AI_INTERVIEW, PipelineStatus.ASSESSMENT),
    (PipelineStatus.HUMAN_INTERVIEW, PipelineStatus.AI_INTERVIEW),
    (PipelineStatus.HUMAN_INTERVIEW, PipelineStatus.ASSESSMENT),
    (PipelineStatus.OFFER_EVALUATION, PipelineStatus.HUMAN_INTERVIEW),
    # --- 归档池重新激活 ---
    (PipelineStatus.ARCHIVED, PipelineStatus.INTERESTED),
}

# 额外的同状态「重入」通常用于记录（如面试时间变更）: 所有状态都允许 self-loop
# 但我们只在引擎层允许，通过 is_reentry 判断
_ALLOW_SELF_LOOP = True


@dataclass
class TransitionResult:
    """状态变更结果。"""
    success: bool
    from_status: PipelineStatus
    to_status: PipelineStatus
    message: str = ""
    is_reentry: bool = False  # 是否为同状态重入（如更新面试时间）


def can_transition(
    from_status: PipelineStatus,
    to_status: PipelineStatus,
) -> TransitionResult:
    """
    判断从 from_status 到 to_status 是否允许。

    规则：
    1. 相同状态且 _ALLOW_SELF_LOOP → 允许 (reentry)
    2. 在 _TRANSITIONS 白名单中 → 允许
    3. 其余 → 拒绝
    """
    # 1. 同状态重入
    if from_status == to_status:
        if _ALLOW_SELF_LOOP:
            return TransitionResult(
                success=True,
                from_status=from_status,
                to_status=to_status,
                message=f"状态不变（重入）: {from_status.label_cn}",
                is_reentry=True,
            )
        return TransitionResult(
            success=False,
            from_status=from_status,
            to_status=to_status,
            message="不允许同状态重入",
        )

    # 2. 白名单检查
    if (from_status, to_status) in _TRANSITIONS:
        direction = "向前流转" if to_status.order > from_status.order else "回退"
        return TransitionResult(
            success=True,
            from_status=from_status,
            to_status=to_status,
            message=f"{direction}: {from_status.label_cn} → {to_status.label_cn}",
        )

    # 3. 拒绝
    return TransitionResult(
        success=False,
        from_status=from_status,
        to_status=to_status,
        message=f"不允许的流转: {from_status.label_cn} → {to_status.label_cn}",
    )


def get_allowed_transitions(from_status: PipelineStatus) -> list[PipelineStatus]:
    """获取从当前状态允许跳转的所有目标状态列表。"""
    return [
        to_s
        for from_s, to_s in _TRANSITIONS
        if from_s == from_status and to_s != from_status
    ] + ([from_status] if _ALLOW_SELF_LOOP else [])


def get_forward_transitions(from_status: PipelineStatus) -> list[PipelineStatus]:
    """获取从当前状态允许向前跳转的目标状态。"""
    return [
        s for s in get_allowed_transitions(from_status)
        if s.order > from_status.order or s == from_status
    ]
