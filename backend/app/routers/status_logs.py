"""状态变更日志查询 API。"""
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import StatusLog
from app.schemas.status_log import StatusLogResponse

router = APIRouter(prefix="/status-logs", tags=["status-logs"])


@router.get("", response_model=List[StatusLogResponse])
def list_status_logs(
    position_id: Optional[int] = Query(None, description="按岗位筛选"),
    limit: int = Query(50, ge=1, le=200, description="返回条数"),
    db: Session = Depends(get_db),
):
    """获取状态变更日志列表。"""
    query = db.query(StatusLog).order_by(StatusLog.created_at.desc())

    if position_id is not None:
        query = query.filter(StatusLog.position_id == position_id)

    return query.limit(limit).all()
