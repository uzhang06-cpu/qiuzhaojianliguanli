"""
JWT 依赖注入 — token 生成、验证、获取当前用户。

使用 hashlib 做密码哈希（避免 bcrypt/passlib 版本兼容问题）。
生产环境建议换用 bcrypt。
"""
from __future__ import annotations

import hashlib
import os
import secrets
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWTError
import jwt as pyjwt
from sqlalchemy.orm import Session

from app.auth.models import User
from app.database import get_db

# ── 配置 ────────────────────────────────────────────────────────────

SECRET_KEY = os.getenv("JWT_SECRET", "smarttracker-dev-secret-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7

bearer_scheme = HTTPBearer(auto_error=False)


# ── 密码工具（SHA-256 + 随机盐） ────────────────────────────────────


def hash_password(password: str) -> str:
    """返回格式: $sha256$salt$hash"""
    salt = secrets.token_hex(16)
    h = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"$sha256${salt}${h}"


def verify_password(plain: str, hashed: str) -> bool:
    try:
        _, algo, salt, expected = hashed.split("$", 3)
        if algo != "sha256":
            return False
        h = hashlib.sha256((salt + plain).encode()).hexdigest()
        return h == expected
    except (ValueError, AttributeError):
        return False


# ── JWT 工具 ─────────────────────────────────────────────────────────


def create_access_token(user_id: int) -> str:
    expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    payload = {"sub": str(user_id), "exp": expire}
    return pyjwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Optional[int]:
    """解析 token → user_id，失败返回 None。"""
    try:
        payload = pyjwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return int(payload["sub"])
    except (PyJWTError, ValueError, KeyError):
        return None


# ── FastAPI 依赖注入 ────────────────────────────────────────────────


def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """获取当前用户（未登录返回 None）。"""
    if credentials is None:
        return None
    user_id = decode_access_token(credentials.credentials)
    if user_id is None:
        return None
    return db.query(User).filter(User.id == user_id).first()


def get_current_user(
    user: Optional[User] = Depends(get_optional_user),
) -> User:
    """获取当前用户（未登录抛 401）。"""
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="请先登录",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
