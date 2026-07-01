"""通知 API — 按用户隔离的轮询引擎。"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_optional_user
from app.auth.models import User
from app.database import get_db
from app.engine.scheduler import scan

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("")
def get_notifications(
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_optional_user),
):
    """
    获取当前用户需要触发的通知。

    每次请求都会执行一次全量扫描。
    未登录用户返回空结果（前端静默处理）。
    """
    result = scan(db, user_id=user.id if user else None)
    return result
