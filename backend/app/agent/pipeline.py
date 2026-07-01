"""
Pipeline 编排器 — 串联感知 → 规划 → 执行 → 反思 四层管线。

提供 run() 入口函数，接收原始文本，输出 AgentResult。
"""
from __future__ import annotations

import time

from app.agent.execution import (
    DatabaseOpsSkill,
    OutreachSkill,
    ScheduleParsingSkill,
    SkillRegistry,
    TextParsingSkill,
)
from app.agent.models import AgentResult, PerceptPacket
from app.agent.perception import process as perception
from app.agent.planning import plan as planning
from app.agent.reflection import reflect as reflection

# 全局 Skill 注册表（单例）
_skill_registry: SkillRegistry | None = None


def _get_registry() -> SkillRegistry:
    """获取全局 Skill 注册表。"""
    global _skill_registry
    if _skill_registry is None:
        _skill_registry = SkillRegistry()
        _skill_registry.register(TextParsingSkill())
        _skill_registry.register(ScheduleParsingSkill())
        _skill_registry.register(DatabaseOpsSkill())
        _skill_registry.register(OutreachSkill())
    return _skill_registry


def run(raw_input: str) -> AgentResult:
    """
    执行完整的 Agent 管线。

    参数:
        raw_input: 用户原始输入文本

    返回:
        AgentResult — 可直接用于前端展示的结构化结果
    """
    start = time.perf_counter()

    # 1️⃣ 感知层
    packet = perception(raw_input)

    # 2️⃣ 规划层
    plan = planning(packet)

    # 3️⃣ 执行层
    registry = _get_registry()
    skill_results = registry.execute_plan(plan, packet)

    # 4️⃣ 反思层
    result = reflection(packet, plan, skill_results)

    # 附加元信息
    elapsed = (time.perf_counter() - start) * 1000
    result.total_latency_ms = round(elapsed, 1)

    return result
