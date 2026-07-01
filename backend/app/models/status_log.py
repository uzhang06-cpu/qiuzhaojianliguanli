from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class StatusLog(Base):
    """状态变更日志表 — 记录每一次状态流转，为后续分析提供数据资产。"""

    __tablename__ = "status_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    position_id = Column(
        Integer, ForeignKey("positions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    from_status = Column(String(32), nullable=False, comment="变更前状态")
    to_status = Column(String(32), nullable=False, comment="变更后状态")
    changed_by = Column(
        String(32), nullable=False, default="user", comment="变更者: user / system / agent"
    )
    remark = Column(Text, nullable=True, comment="变更备注")
    created_at = Column(DateTime, default=datetime.now, nullable=False, comment="变更时间")

    # 关联
    position = relationship("Position", back_populates="status_logs")

    def __repr__(self):
        return (
            f"<StatusLog(id={self.id}, position_id={self.position_id}, "
            f"{self.from_status} → {self.to_status})>"
        )
