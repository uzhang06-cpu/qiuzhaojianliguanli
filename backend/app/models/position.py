from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class Position(Base):
    """求职岗位主表 — 记录一条求职线索的完整生命周期。"""

    __tablename__ = "positions"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 用户隔离
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True, comment="所属用户",
    )

    company = Column(String(200), nullable=False, comment="公司名称")
    position = Column(String(200), nullable=False, comment="岗位名称")

    # 管线状态
    status = Column(
        String(32),
        nullable=False,
        default="interested",
        index=True,
        comment="当前 Pipeline 状态",
    )

    # 扩展信息
    base_location = Column(String(200), nullable=True, comment="Base 地")
    salary_range = Column(String(100), nullable=True, comment="薪资范围")
    job_description = Column(Text, nullable=True, comment="原始 JD 文本")

    # 时间信息
    next_ddl = Column(DateTime, nullable=True, comment="最近待办时间")
    interview_link = Column(String(500), nullable=True, comment="面试链接")
    interview_platform = Column(String(100), nullable=True, comment="面试平台")

    # 复盘
    notes = Column(Text, nullable=True, comment="复盘笔记")

    # 元信息
    created_at = Column(DateTime, default=datetime.now, nullable=False, comment="创建时间")
    updated_at = Column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
        nullable=False,
        comment="更新时间",
    )
    is_active = Column(Boolean, default=True, nullable=False, comment="软删除标记")

    # 关联
    status_logs = relationship(
        "StatusLog",
        back_populates="position",
        order_by="StatusLog.created_at.desc()",
        cascade="all, delete-orphan",
    )
    owner = relationship("User", back_populates="positions")

    def __repr__(self):
        return f"<Position(id={self.id}, user={self.user_id}, {self.company})>"
