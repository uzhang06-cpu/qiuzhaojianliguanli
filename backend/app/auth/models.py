from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    """用户表。"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True, comment="邮箱")
    password_hash = Column(String(255), nullable=False, comment="bcrypt 哈希")
    created_at = Column(DateTime, default=datetime.now, nullable=False)

    # 用户的求职数据
    positions = relationship("Position", back_populates="owner", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User #{self.id} {self.email}>"
