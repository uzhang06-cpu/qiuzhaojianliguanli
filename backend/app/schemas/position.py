from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.engine.pipeline import PipelineStatus


# ── Request Schemas ─────────────────────────────────────────────────


class PositionCreate(BaseModel):
    """创建岗位的请求体。"""
    company: str = Field(..., min_length=1, max_length=200, description="公司名称")
    position: str = Field(..., min_length=1, max_length=200, description="岗位名称")
    status: PipelineStatus = Field(default=PipelineStatus.INTERESTED, description="管线状态")
    base_location: Optional[str] = Field(None, max_length=200, description="Base 地")
    salary_range: Optional[str] = Field(None, max_length=100, description="薪资范围")
    job_description: Optional[str] = Field(None, description="原始 JD 文本")
    next_ddl: Optional[datetime] = Field(None, description="最近待办时间")
    interview_link: Optional[str] = Field(None, max_length=500, description="面试链接")
    interview_platform: Optional[str] = Field(None, max_length=100, description="面试平台")
    notes: Optional[str] = Field(None, description="复盘笔记")
    changed_by: str = Field(default="user", description="变更者标识")


class PositionUpdate(BaseModel):
    """更新岗位信息的请求体。"""
    company: Optional[str] = Field(None, min_length=1, max_length=200)
    position: Optional[str] = Field(None, min_length=1, max_length=200)
    base_location: Optional[str] = Field(None, max_length=200)
    salary_range: Optional[str] = Field(None, max_length=100)
    job_description: Optional[str] = Field(None)
    next_ddl: Optional[datetime] = Field(None)
    interview_link: Optional[str] = Field(None, max_length=500)
    interview_platform: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = Field(None)


class PositionStatusUpdate(BaseModel):
    """状态变更请求体。"""
    status: PipelineStatus = Field(..., description="目标状态")
    changed_by: str = Field(default="user", description="变更者标识")
    remark: Optional[str] = Field(None, description="变更备注")


# ── Response Schemas ────────────────────────────────────────────────


class PositionResponse(BaseModel):
    """岗位响应体。"""
    id: int
    company: str
    position: str
    status: str
    status_label: str = ""
    base_location: Optional[str] = None
    salary_range: Optional[str] = None
    job_description: Optional[str] = None
    next_ddl: Optional[datetime] = None
    interview_link: Optional[str] = None
    interview_platform: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    is_active: bool

    model_config = {"from_attributes": True}

    def model_post_init(self, __context) -> None:
        """自动填充 status_label。"""
        try:
            status_enum = PipelineStatus(self.status)
            self.status_label = status_enum.label_cn
        except ValueError:
            self.status_label = self.status
