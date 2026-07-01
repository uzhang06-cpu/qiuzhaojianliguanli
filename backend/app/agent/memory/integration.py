"""
Memory 集成层 — 将记忆系统挂载到 Agent 管线中。

在现有四层管线的基础上，在关键节点注入记忆操作：
  1. 感知层之后 → 注入近期对话上下文到 hints
  2. 反思层之后 → 保存本次对话记录
  3. 前端提交修正 → 通过 feedback API 写入纠错学习
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.agent.memory.store import MemoryStore
from app.agent.models import AgentResult, PerceptPacket


def inject_memory_context(
    packet: PerceptPacket,
    session_id: str,
    db: Session,
) -> PerceptPacket:
    """
    感知层后调用：将近期对话历史和纠错学习注入到 hints 中。

    这些 hint 在规划层/执行层可通过 packet.hints 读取。
    """
    store = MemoryStore(db)

    # 通道 A：近期对话
    recent = store.get_recent_context(session_id)
    if recent:
        packet.hints["recent_conversations"] = recent

    # 通道 B：纠错学习
    corrections = store.get_corrections_for(session_id)
    if corrections:
        packet.hints["known_corrections"] = corrections

    return packet


def save_agent_memory(
    packet: PerceptPacket,
    result: AgentResult,
    session_id: str,
    db: Session,
    corrections: Optional[dict[str, tuple[Optional[str], str]]] = None,
) -> int:
    """
    管线结束后调用：保存对话记录和修正数据。

    返回 conversation_id，用于后续关联修正。
    """
    store = MemoryStore(db)

    # 保存对话
    conv = store.save_conversation(
        session_id=session_id,
        raw_input=packet.raw_input,
        intent=result.action_type,
        confidence=result.confidence,
        extracted={
            f.key: f.value
            for f in result.display_fields
        },
        had_correction=bool(corrections),
    )

    # 保存修正
    if corrections:
        store.save_corrections_batch(
            conversation_id=conv.id,
            session_id=session_id,
            corrections=corrections,
        )

    return conv.id
