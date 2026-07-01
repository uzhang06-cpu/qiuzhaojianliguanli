"""
Agent API 路由 — AI 闪电录入 + 用户反馈（纠错学习）。
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.agent.memory.integration import inject_memory_context, save_agent_memory
from app.agent.models import AgentResult
from app.agent.pipeline import run as run_agent
from app.database import get_db

router = APIRouter(prefix="/agent", tags=["agent"])


class ParseRequest(BaseModel):
    """AI 解析请求体。"""
    text: str = Field(..., min_length=1, max_length=5000, description="用户输入的文本")
    session_id: str = Field(default="default", max_length=64, description="会话标识")


class ParseResponse(BaseModel):
    """AI 解析响应体。"""
    success: bool
    data: AgentResult
    conversation_id: int = 0
    message: str = ""


@router.post("/parse", response_model=ParseResponse)
def agent_parse(req: ParseRequest, db: Session = Depends(get_db)):
    """
    AI 闪电录入接口。

    接收非结构化文本，经过 Agent 四层管线处理后，
    返回结构化预填数据供前端确认表单使用。

    同时记录对话到记忆库（通道 A）。
    """
    try:
        import time
        _start = time.perf_counter()

        # 1️⃣ 感知层
        from app.agent.perception import process as perception
        packet = perception(req.text)

        # 1b) 注入记忆上下文
        packet = inject_memory_context(packet, req.session_id, db)

        # 2️⃣ 规划层
        from app.agent.planning import plan as planning
        plan = planning(packet)

        # 3️⃣ 执行层
        from app.agent.execution import (
            DatabaseOpsSkill,
            OutreachSkill,
            ScheduleParsingSkill,
            SkillRegistry,
            TextParsingSkill,
        )
        registry = SkillRegistry()
        registry.register(TextParsingSkill())
        registry.register(ScheduleParsingSkill())
        registry.register(DatabaseOpsSkill())
        registry.register(OutreachSkill())
        skill_results = registry.execute_plan(plan, packet)

        # 4️⃣ 反思层
        from app.agent.reflection import reflect as reflection
        result = reflection(packet, plan, skill_results)

        # 5️⃣ 保存记忆（通道 A）
        conv_id = save_agent_memory(packet, result, req.session_id, db)

        # 计时
        result.total_latency_ms = round((time.perf_counter() - _start) * 1000, 1)

        return ParseResponse(
            success=True,
            data=result,
            conversation_id=conv_id,
            message="解析完成" if not result.needs_human_review else result.human_review_reason,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent 管线异常: {str(e)}")


# ── 反馈 / 纠错学习 ─────────────────────────────────────────────────


class FeedbackField(BaseModel):
    """单个字段的修正数据。"""
    field_name: str
    original_value: Optional[str] = None
    corrected_value: str


class FeedbackRequest(BaseModel):
    """用户反馈请求体。"""
    conversation_id: int = Field(..., description="关联的对话 ID")
    session_id: str = Field(default="default", max_length=64)
    corrections: list[FeedbackField] = Field(default_factory=list, description="修正的字段列表")


class FeedbackResponse(BaseModel):
    success: bool
    corrections_saved: int
    message: str = "修正已记录，AI 将从本次修正中学习"


@router.post("/feedback", response_model=FeedbackResponse)
def agent_feedback(req: FeedbackRequest, db: Session = Depends(get_db)):
    """
    用户反馈接口 — 接收前端确认表单中的修正数据（通道 B）。

    每次用户在预填表单中手动修改了 AI 提取的字段，
    前端都应该调用此接口，将修正值记录下来。
    后续 Agent 遇到类似输入时，会优先使用已修正的值。
    """
    if not req.corrections:
        return FeedbackResponse(success=True, corrections_saved=0, message="无修正数据")

    from app.agent.memory.store import MemoryStore
    store = MemoryStore(db)
    saved_count = 0

    for c in req.corrections:
        store.save_correction(
            conversation_id=req.conversation_id,
            session_id=req.session_id,
            field_name=c.field_name,
            original_value=c.original_value,
            corrected_value=c.corrected_value,
        )
        saved_count += 1

    return FeedbackResponse(
        success=True,
        corrections_saved=saved_count,
        message=f"已记录 {saved_count} 条修正，AI 将从本次修正中学习",
    )
