"""Application configuration, loaded from environment / .env file."""
from __future__ import annotations

import os
from pathlib import Path

from pydantic_settings import BaseSettings


# 项目根目录 = 本文件 (backend/app/config.py) 的爷爷目录
# 使用绝对路径可以避免 SQLite 数据库路径因 CWD 不同而"跑丢"，
# 保证无论从 backend/ 还是从项目根启动 uvicorn，都指向同一个 db 文件。
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_DATA_DIR = _PROJECT_ROOT / "data"
_DATA_DIR.mkdir(parents=True, exist_ok=True)
_DEFAULT_SQLITE_PATH = _DATA_DIR / "smart_tracker.db"

# 允许通过 SQLITE_PATH 单独覆盖 SQLite 文件位置（比如 Render 挂载盘）
_SQLITE_PATH_OVERRIDE = os.environ.get("SQLITE_PATH")
if _SQLITE_PATH_OVERRIDE:
    _sqlite_url = f"sqlite:///{Path(_SQLITE_PATH_OVERRIDE).expanduser().resolve()}"
else:
    # SQLAlchemy 需要 sqlite:///<绝对路径>，POSIX 三斜线 + Windows 路径没关系
    _sqlite_url = f"sqlite:///{_DEFAULT_SQLITE_PATH.as_posix()}"


class Settings(BaseSettings):
    """Application configuration."""

    # 默认走本地绝对路径 SQLite。
    # 生产环境（Render）**强烈建议** 通过 DATABASE_URL 环境变量指向 PostgreSQL：
    #   postgresql://user:pass@host:5432/dbname
    # 否则 Render 免费 web service 每次冷启动都会清空文件系统 → 数据丢失。
    database_url: str = _sqlite_url

    debug: bool = True

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
