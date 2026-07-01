"""
Memory 数据模型 — 两张表实现双通道记忆。

通道 A — agent_conversations: 对话历史
  每次 Agent 调用记录一条，包含原始输入、识别意图、提取结果。
  用于后续调用时注入上下文（"上次你提过字节跳动"）。

通道 B — agent_corrections: 纠错学习
  用户在预填确认表单中修正的字段被记录到这里。
  下次 AI 再提取同公司/岗位时，优先使用已纠正的值。
"""
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from app.database import Base


class AgentConversation(Base):
    """通道 A：Agent 对话记录 — 每次 /agent/parse 调用的完整快照。"""

    __tablename__ = "agent_conversations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), nullable=False, index=True, comment="会话标识")
    raw_input = Column(Text, nullable=False, comment="用户原始输入")
    intent = Column(String(32), nullable=False, comment="识别到的意图")
    confidence = Column(Integer, nullable=False, default=0, comment="置信度 0-100")

    # 提取的结构化结果（JSON 字符串）
    extracted_json = Column(Text, nullable=True, comment="AI 提取的结构化数据 JSON")

    # 是否被用户修正过（关联到 correction）
    had_correction = Column(Integer, nullable=False, default=0, comment="是否被修正 0/1")

    created_at = Column(DateTime, default=datetime.now, nullable=False, comment="创建时间")

    def __repr__(self):
        return f"<AgentConversation #{self.id} intent={self.intent}>"


class AgentCorrection(Base):
    """通道 B：纠错学习 — 用户修正 AI 提取结果的记录。"""

    __tablename__ = "agent_corrections"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, nullable=False, index=True, comment="关联的对话 ID")
    session_id = Column(String(64), nullable=False, index=True, comment="会话标识")

    # 修正前的原始提取值
    field_name = Column(String(64), nullable=False, comment="字段名，如 company")
    original_value = Column(Text, nullable=True, comment="AI 原始提取值")
    corrected_value = Column(Text, nullable=False, comment="用户修正后的值")

    created_at = Column(DateTime, default=datetime.now, nullable=False, comment="修正时间")

    def __repr__(self):
        return f"<AgentCorrection #{self.id} {self.field_name}: {self.original_value} → {self.corrected_value}>"
