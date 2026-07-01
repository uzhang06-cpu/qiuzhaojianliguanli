"""
智能日程与状态引擎 (Smart Scheduler & Engine)

纯站内轮询引擎，定期扫描 positions 表，生成三类通知：

1. 临期强提醒 (Pre-event) — DDL < 24h / < 2h
2. 复盘驱动器 (Post-event) — 面试结束 > 2h 需补充笔记
3. 僵尸状态唤醒 (Dead-state) — 某阶段停滞 > 7 天
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.engine.pipeline import PipelineStatus
from app.models import Position, StatusLog


@dataclass
class Notification:
    """一条通知。"""
    type: str                # "pre_event" | "post_review" | "dead_state"
    severity: str            # "danger" | "warning" | "info"
    title: str
    message: str
    position_id: int
    position_title: str      # "公司-岗位"
    created_at: str          # ISO datetime


@dataclass
class ScanResult:
    """一次轮询的结果。"""
    scanned_at: str = ""
    total_positions: int = 0
    pre_event_count: int = 0
    post_review_count: int = 0
    dead_state_count: int = 0
    notifications: list[Notification] = field(default_factory=list)


def scan(db: Session, user_id: Optional[int] = None) -> ScanResult:
    """
    执行一次扫描，返回需要触发的通知。

    参数:
      user_id: 可选，只扫描指定用户的数据。不传则扫全部。
    """
    now = datetime.now()
    result = ScanResult(scanned_at=now.isoformat())

    query = db.query(Position).filter(Position.is_active == True)
    if user_id is not None:
        query = query.filter(Position.user_id == user_id)
    active_positions = query.all()
    result.total_positions = len(active_positions)

    for pos in active_positions:
        n: Optional[Notification] = None

        # 1. 临期强提醒 (只对有时间字段的非归档状态)
        if pos.next_ddl and pos.status != PipelineStatus.ARCHIVED.value:
            n = _check_pre_event(pos, now)

        # 2. 复盘驱动器 (人工面试/AI面/笔试结束 > 2h 且无笔记)
        if n is None and pos.status in (
            PipelineStatus.HUMAN_INTERVIEW.value,
            PipelineStatus.AI_INTERVIEW.value,
            PipelineStatus.ASSESSMENT.value,
        ):
            n = _check_post_review(pos, now, db)

        # 3. 僵尸状态唤醒 (非归档且非 offer 评估，停滞 > 7 天)
        if n is None and pos.status not in (
            PipelineStatus.OFFER_EVALUATION.value,
            PipelineStatus.ARCHIVED.value,
        ):
            n = _check_dead_state(pos, now, db)

        if n:
            result.notifications.append(n)
            _increment_count(result, n.type)

    return result


def _check_pre_event(pos: Position, now: datetime) -> Optional[Notification]:
    """检查临期事件。"""
    diff = pos.next_ddl - now
    title = f"{pos.company}-{pos.position}"

    if diff < timedelta(hours=2) and diff >= timedelta(0):
        return Notification(
            type="pre_event",
            severity="danger",
            title="面试即将开始",
            message=f"⏰ {title} 的面试/笔试将在 {_fmt_diff(diff)} 后开始",
            position_id=pos.id,
            position_title=title,
            created_at=now.isoformat(),
        )

    if diff < timedelta(hours=24) and diff >= timedelta(hours=2):
        return Notification(
            type="pre_event",
            severity="warning",
            title="面试/笔试临近",
            message=f"📅 {title} 将在 {_fmt_diff(diff)} 后进行",
            position_id=pos.id,
            position_title=title,
            created_at=now.isoformat(),
        )

    return None


def _check_post_review(pos: Position, now: datetime, db: Session) -> Optional[Notification]:
    """检查面试结束后是否需要复盘。"""
    if not pos.next_ddl:
        return None

    # 面试结束 > 2h
    elapsed = now - pos.next_ddl
    if elapsed < timedelta(hours=2):
        return None

    # 已有笔记就不提醒
    if pos.notes:
        return None

    title = f"{pos.company}-{pos.position}"
    return Notification(
        type="post_review",
        severity="info",
        title="面试复盘提醒",
        message=f"📝 {title} 的面试已结束，是否补充复盘笔记？",
        position_id=pos.id,
        position_title=title,
        created_at=now.isoformat(),
    )


def _check_dead_state(pos: Position, now: datetime, db: Session) -> Optional[Notification]:
    """检查是否停滞超过 7 天。"""
    # 找最近一次状态变更
    last_log = (
        db.query(StatusLog)
        .filter(
            StatusLog.position_id == pos.id,
            StatusLog.to_status == pos.status,
        )
        .order_by(StatusLog.created_at.desc())
        .first()
    )

    if not last_log:
        return None

    stagnant_days = (now - last_log.created_at).days
    if stagnant_days < 7:
        return None

    title = f"{pos.company}-{pos.position}"
    return Notification(
        type="dead_state",
        severity="warning",
        title="进度停滞警告",
        message=f"⚠️ {title} 在「{PipelineStatus(pos.status).label_cn}」阶段已停滞 {stagnant_days} 天，建议邮件 Follow",
        position_id=pos.id,
        position_title=title,
        created_at=now.isoformat(),
    )


def _fmt_diff(diff: timedelta) -> str:
    """人性化时间差。"""
    total_minutes = int(diff.total_seconds() / 60)
    if total_minutes < 60:
        return f"{total_minutes} 分钟"
    hours = total_minutes // 60
    minutes = total_minutes % 60
    if minutes == 0:
        return f"{hours} 小时"
    return f"{hours} 小时 {minutes} 分钟"


def _increment_count(result: ScanResult, ntype: str):
    if ntype == "pre_event":
        result.pre_event_count += 1
    elif ntype == "post_review":
        result.post_review_count += 1
    elif ntype == "dead_state":
        result.dead_state_count += 1
