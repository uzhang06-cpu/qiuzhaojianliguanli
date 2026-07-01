"""
岗位 CRUD 与状态变更 API。

每个变更状态的请求都会自动向 status_logs 表写入一条日志。
所有数据按 user_id 隔离，用户只能看到自己的数据。
"""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.database import get_db
from app.engine.pipeline import PipelineStatus
from app.engine.state_machine import can_transition
from app.models import Position, StatusLog
from app.schemas.position import (
    PositionCreate,
    PositionResponse,
    PositionStatusUpdate,
    PositionUpdate,
)

router = APIRouter(prefix="/positions", tags=["positions"])


# ── List / Search ───────────────────────────────────────────────────


@router.get("", response_model=List[PositionResponse])
def list_positions(
    status: Optional[str] = Query(None, description="按状态筛选"),
    keyword: Optional[str] = Query(None, description="按公司/岗位关键词搜索"),
    is_active: Optional[bool] = Query(True, description="仅显示活跃记录"),
    sort_by: Optional[str] = Query("updated_at", description="排序字段"),
    sort_dir: Optional[str] = Query("desc", description="排序方向"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """获取当前用户的岗位列表。"""
    query = db.query(Position).filter(Position.user_id == user.id)

    if is_active is not None:
        query = query.filter(Position.is_active == is_active)

    if status:
        query = query.filter(Position.status == status)

    if keyword:
        like = f"%{keyword}%"
        query = query.filter(
            Position.company.ilike(like) | Position.position.ilike(like)
        )

    sort_column = getattr(Position, sort_by, Position.updated_at)
    if sort_dir == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    return query.all()


# ── Get by ID ───────────────────────────────────────────────────────


@router.get("/{position_id}", response_model=PositionResponse)
def get_position(
    position_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """获取单个岗位详情（仅限自己的数据）。"""
    position = (
        db.query(Position)
        .filter(Position.id == position_id, Position.user_id == user.id)
        .first()
    )
    if not position:
        raise HTTPException(status_code=404, detail="岗位不存在")
    return position


# ── Create ──────────────────────────────────────────────────────────


@router.post("", response_model=PositionResponse, status_code=201)
def create_position(
    data: PositionCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """创建新岗位（归当前用户）。"""
    position = Position(
        user_id=user.id,
        company=data.company,
        position=data.position,
        status=data.status.value,
        base_location=data.base_location,
        salary_range=data.salary_range,
        job_description=data.job_description,
        next_ddl=data.next_ddl,
        interview_link=data.interview_link,
        interview_platform=data.interview_platform,
        notes=data.notes,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    db.add(position)
    db.flush()

    log = StatusLog(
        position_id=position.id,
        from_status="",
        to_status=data.status.value,
        changed_by=data.changed_by,
        remark="创建岗位",
    )
    db.add(log)
    db.commit()
    db.refresh(position)
    return position


# ── Update ──────────────────────────────────────────────────────────


@router.patch("/{position_id}", response_model=PositionResponse)
def update_position(
    position_id: int,
    data: PositionUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """更新岗位信息（仅限自己的数据）。"""
    position = (
        db.query(Position)
        .filter(Position.id == position_id, Position.user_id == user.id)
        .first()
    )
    if not position:
        raise HTTPException(status_code=404, detail="岗位不存在")

    update_data = data.model_dump(exclude_unset=True)
    if not update_data:
        return position

    for field, value in update_data.items():
        setattr(position, field, value)

    position.updated_at = datetime.now()
    db.commit()
    db.refresh(position)
    return position


# ── Status Transition ───────────────────────────────────────────────


@router.post("/{position_id}/status", response_model=PositionResponse)
def transition_status(
    position_id: int,
    data: PositionStatusUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """变更岗位状态（仅限自己的数据）。"""
    position = (
        db.query(Position)
        .filter(Position.id == position_id, Position.user_id == user.id)
        .first()
    )
    if not position:
        raise HTTPException(status_code=404, detail="岗位不存在")

    from_status = PipelineStatus(position.status)
    to_status = data.status

    result = can_transition(from_status, to_status)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)

    old_status = position.status
    position.status = to_status.value
    position.updated_at = datetime.now()
    db.flush()

    log = StatusLog(
        position_id=position.id,
        from_status=old_status,
        to_status=to_status.value,
        changed_by=data.changed_by,
        remark=data.remark or result.message,
    )
    db.add(log)
    db.commit()
    db.refresh(position)
    return position


# ── Delete ──────────────────────────────────────────────────────────


@router.delete("/{position_id}")
def delete_position(
    position_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """软删除岗位（仅限自己的数据）。"""
    position = (
        db.query(Position)
        .filter(Position.id == position_id, Position.user_id == user.id)
        .first()
    )
    if not position:
        raise HTTPException(status_code=404, detail="岗位不存在")

    position.is_active = False
    position.updated_at = datetime.now()
    db.commit()
    return {"message": "删除成功", "id": position_id}
