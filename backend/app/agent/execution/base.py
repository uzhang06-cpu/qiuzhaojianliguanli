"""
Skill 抽象基类与注册表。

每个 Skill 继承 BaseSkill，实现 execute() 方法。
SkillRegistry 负责按 SkillType 查找对应的 Skill 实例。
"""
from __future__ import annotations

import abc
from typing import Optional

from app.agent.models import PerceptPacket, Plan, SkillResult, SkillType


class BaseSkill(abc.ABC):
    """Skill 抽象基类。"""

    skill_type: SkillType

    @abc.abstractmethod
    def execute(
        self,
        packet: PerceptPacket,
        plan: Plan,
        prev_results: dict[SkillType, SkillResult],
    ) -> SkillResult:
        """执行技能并返回结果。"""
        ...


class SkillRegistry:
    """Skill 注册表 — 管理所有可用 Skill 实例。"""

    def __init__(self):
        self._skills: dict[SkillType, BaseSkill] = {}

    def register(self, skill: BaseSkill):
        self._skills[skill.skill_type] = skill

    def get(self, skill_type: SkillType) -> Optional[BaseSkill]:
        return self._skills.get(skill_type)

    def execute_plan(
        self,
        plan: Plan,
        packet: PerceptPacket,
    ) -> dict[SkillType, SkillResult]:
        """按 Plan 中的 required_skills 顺序执行。"""
        results: dict[SkillType, SkillResult] = {}

        for skill_type in plan.required_skills:
            skill = self.get(skill_type)
            if skill is None:
                results[skill_type] = SkillResult(
                    skill=skill_type,
                    success=False,
                    error=f"Skill {skill_type.value} 未注册",
                )
                continue

            result = skill.execute(packet, plan, results)
            results[skill_type] = result

        return results
