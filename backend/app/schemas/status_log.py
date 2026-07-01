from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class StatusLogResponse(BaseModel):
    """状态变更日志响应体。"""
    id: int
    position_id: int
    from_status: str
    to_status: str
    changed_by: str
    remark: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
