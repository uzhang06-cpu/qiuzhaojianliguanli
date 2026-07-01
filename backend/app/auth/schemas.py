from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    """注册请求。"""
    email: str = Field(..., min_length=5, max_length=255, description="邮箱")
    password: str = Field(..., min_length=6, max_length=128, description="密码")


class LoginRequest(BaseModel):
    """登录请求。"""
    email: str = Field(..., description="邮箱")
    password: str = Field(..., description="密码")


class TokenResponse(BaseModel):
    """登录成功返回。"""
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"


class UserOut(BaseModel):
    """用户公开信息。"""
    id: int
    email: str
    created_at: datetime

    class Config:
        from_attributes = True
