"""
自动化触达 Skill (Outreach) — 预留的外部 Webhook 接口。

职责：
  - 在关键节点（面试将至、状态变更）抛出标准化 Payload
  - 通过 OpenClaw 等工具触发 PC 端弹窗或微信推送
  - 一期只做骨架和标准定义，不实现具体推送
"""
from __future__ import annotations

from app.agent.execution.base import BaseSkill, SkillResult
from app.agent.models import ExtractedEntity, PerceptPacket, Plan, SkillType


class OutreachSkill(BaseSkill):
    """自动化触达技能（预留骨架）。"""

    skill_type = SkillType.OUTREACH

    def execute(
        self,
        packet: PerceptPacket,
        plan: Plan,
        prev_results: dict[SkillType, SkillResult],
    ) -> SkillResult:
        # 一期：仅构造标准化 Payload，实际推送由外部系统接管
        payload = {
            "trigger": f"agent_{plan.intent.value}",
            "channel": "webhook",
            "payload": {
                "title": "SmartTracker 通知",
                "body": f"检测到操作: {plan.raw_intent or plan.intent.value}",
                "timestamp": packet.system_time.isoformat(),
            },
        }

        return SkillResult(
            skill=self.skill_type,
            success=True,
            entities=[
                ExtractedEntity(
                    field="outreach_payload",
                    value=payload,
                    confidence=1.0,
                    display_text="📬 触达 Payload 已构建（待对接）",
                ),
            ],
            raw_output=str(payload),
        )
