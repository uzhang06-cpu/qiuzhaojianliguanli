"""
状态机引擎单元测试。

覆盖范围：
  - 所有允许的向前流转
  - 所有允许的回退
  - 不允许的跳过/回退
  - 同状态重入
  - 归档池激活
  - 终端状态约束
"""
import pytest

from app.engine.pipeline import PipelineStatus
from app.engine.state_machine import can_transition, get_allowed_transitions


class TestPipelineStatus:
    """状态枚举辅助属性测试。"""

    def test_label_cn(self):
        assert PipelineStatus.INTERESTED.label_cn == "意向待投"
        assert PipelineStatus.ARCHIVED.label_cn == "归档池"

    def test_order_ascending(self):
        assert PipelineStatus.INTERESTED.order < PipelineStatus.APPLIED.order
        assert PipelineStatus.APPLIED.order < PipelineStatus.ASSESSMENT.order
        assert PipelineStatus.ASSESSMENT.order < PipelineStatus.AI_INTERVIEW.order
        assert PipelineStatus.AI_INTERVIEW.order < PipelineStatus.HUMAN_INTERVIEW.order
        assert PipelineStatus.HUMAN_INTERVIEW.order < PipelineStatus.OFFER_EVALUATION.order
        assert PipelineStatus.OFFER_EVALUATION.order < PipelineStatus.ARCHIVED.order

    def test_is_terminal(self):
        assert PipelineStatus.ARCHIVED.is_terminal is True
        assert PipelineStatus.INTERESTED.is_terminal is False


class TestStateMachineTransitions:
    """状态机流转规则测试。"""

    # ── 向前流转 ─────────────────────────────────────────────────

    @pytest.mark.parametrize(
        "from_status, to_status",
        [
            (PipelineStatus.INTERESTED, PipelineStatus.APPLIED),
            (PipelineStatus.INTERESTED, PipelineStatus.ASSESSMENT),
            (PipelineStatus.INTERESTED, PipelineStatus.AI_INTERVIEW),
            (PipelineStatus.INTERESTED, PipelineStatus.HUMAN_INTERVIEW),
            (PipelineStatus.INTERESTED, PipelineStatus.OFFER_EVALUATION),
            (PipelineStatus.INTERESTED, PipelineStatus.ARCHIVED),
            (PipelineStatus.APPLIED, PipelineStatus.ASSESSMENT),
            (PipelineStatus.APPLIED, PipelineStatus.AI_INTERVIEW),
            (PipelineStatus.APPLIED, PipelineStatus.HUMAN_INTERVIEW),
            (PipelineStatus.APPLIED, PipelineStatus.OFFER_EVALUATION),
            (PipelineStatus.APPLIED, PipelineStatus.ARCHIVED),
            (PipelineStatus.ASSESSMENT, PipelineStatus.AI_INTERVIEW),
            (PipelineStatus.ASSESSMENT, PipelineStatus.HUMAN_INTERVIEW),
            (PipelineStatus.ASSESSMENT, PipelineStatus.OFFER_EVALUATION),
            (PipelineStatus.ASSESSMENT, PipelineStatus.ARCHIVED),
            (PipelineStatus.AI_INTERVIEW, PipelineStatus.HUMAN_INTERVIEW),
            (PipelineStatus.AI_INTERVIEW, PipelineStatus.OFFER_EVALUATION),
            (PipelineStatus.AI_INTERVIEW, PipelineStatus.ARCHIVED),
            (PipelineStatus.HUMAN_INTERVIEW, PipelineStatus.OFFER_EVALUATION),
            (PipelineStatus.HUMAN_INTERVIEW, PipelineStatus.ARCHIVED),
            (PipelineStatus.OFFER_EVALUATION, PipelineStatus.ARCHIVED),
        ],
    )
    def test_forward_transition_allowed(self, from_status, to_status):
        """所有定义的向前流转应该成功。"""
        result = can_transition(from_status, to_status)
        assert result.success, (
            f"预期 {from_status.label_cn} → {to_status.label_cn} 应允许, "
            f"但被拒绝: {result.message}"
        )
        assert not result.is_reentry

    # ── 回退 ─────────────────────────────────────────────────────

    @pytest.mark.parametrize(
        "from_status, to_status",
        [
            (PipelineStatus.APPLIED, PipelineStatus.INTERESTED),
            (PipelineStatus.ASSESSMENT, PipelineStatus.APPLIED),
            (PipelineStatus.AI_INTERVIEW, PipelineStatus.ASSESSMENT),
            (PipelineStatus.HUMAN_INTERVIEW, PipelineStatus.AI_INTERVIEW),
            (PipelineStatus.HUMAN_INTERVIEW, PipelineStatus.ASSESSMENT),
            (PipelineStatus.OFFER_EVALUATION, PipelineStatus.HUMAN_INTERVIEW),
        ],
    )
    def test_backward_transition_allowed(self, from_status, to_status):
        """所有定义的回退应该成功。"""
        result = can_transition(from_status, to_status)
        assert result.success, (
            f"预期 {from_status.label_cn} 回退到 {to_status.label_cn} 应允许, "
            f"但被拒绝: {result.message}"
        )

    # ── 不允许的流转 ─────────────────────────────────────────────

    @pytest.mark.parametrize(
        "from_status, to_status",
        [
            # 严重跨状态回退
            (PipelineStatus.OFFER_EVALUATION, PipelineStatus.INTERESTED),
            (PipelineStatus.OFFER_EVALUATION, PipelineStatus.APPLIED),
            (PipelineStatus.ARCHIVED, PipelineStatus.APPLIED),
            (PipelineStatus.ARCHIVED, PipelineStatus.ASSESSMENT),
            (PipelineStatus.ARCHIVED, PipelineStatus.AI_INTERVIEW),
            (PipelineStatus.ARCHIVED, PipelineStatus.HUMAN_INTERVIEW),
            (PipelineStatus.ARCHIVED, PipelineStatus.OFFER_EVALUATION),
        ],
    )
    def test_disallowed_transition(self, from_status, to_status):
        """不应该允许的流转应该被拒绝。"""
        result = can_transition(from_status, to_status)
        assert not result.success, (
            f"预期 {from_status.label_cn} → {to_status.label_cn} 应拒绝, "
            f"但被允许: {result.message}"
        )

    # ── 同状态重入 ───────────────────────────────────────────────

    @pytest.mark.parametrize("status", list(PipelineStatus))
    def test_self_loop_allowed(self, status):
        """所有状态应允许同状态重入（用于更新信息）。"""
        result = can_transition(status, status)
        assert result.success
        assert result.is_reentry

    # ── 归档池重新激活 ───────────────────────────────────────────

    def test_archived_reopen(self):
        """归档池应允许回到 interested。"""
        result = can_transition(PipelineStatus.ARCHIVED, PipelineStatus.INTERESTED)
        assert result.success, f"归档池重新激活被拒绝: {result.message}"

    # ── 辅助函数 ─────────────────────────────────────────────────

    def test_get_allowed_transitions(self):
        """get_allowed_transitions 应返回合理的目标列表。"""
        targets = get_allowed_transitions(PipelineStatus.INTERESTED)
        assert PipelineStatus.APPLIED in targets
        assert PipelineStatus.ARCHIVED in targets
        assert PipelineStatus.INTERESTED in targets  # self-loop

        # archived 只能回到 interested 或原地
        archived_targets = get_allowed_transitions(PipelineStatus.ARCHIVED)
        assert PipelineStatus.INTERESTED in archived_targets
        assert PipelineStatus.ARCHIVED in archived_targets
        assert PipelineStatus.APPLIED not in archived_targets
