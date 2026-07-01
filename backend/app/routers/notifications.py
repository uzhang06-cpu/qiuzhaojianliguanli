"""通知 API — 轮询触发引擎并返回通知列表。"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.engine.scheduler import Notification, ScanResult, scan

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=ScanResult)
def get_notifications(db: Session = Depends(get_db)):
    """
    获取当前所有需要触发的通知。

    每次请求都会执行一次全量扫描，保证返回实时结果。
    客户端应定期轮询此接口（建议间隔 30s-60s）。
    """
    return scan(db)
