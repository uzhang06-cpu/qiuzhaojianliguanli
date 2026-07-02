"""
SmartTracker — 智能求职管理系统后端入口。

FastAPI 应用实例，注册路由与生命周期钩子。
生产环境同时托管前端静态文件（合一部署）。
"""
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# 配置日志输出（确保 traceback 可见）
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

# 导入所有模型确保 Base.metadata.create_all 能建所有表
import app.agent.memory.models  # noqa: F401 — agent_conversations + agent_corrections
import app.auth.models  # noqa: F401 — users

from app.agent.router import router as agent_router
from app.auth.router import router as auth_router
from app.config import settings
from app.database import Base, engine
from app.routers import notifications, positions, status_logs


logger = logging.getLogger("smart_tracker")


def _log_database_status() -> None:
    """启动时明确打印当前使用的数据库连接，方便定位"数据存不住"这类问题。"""
    url = settings.database_url
    if url.startswith("sqlite"):
        # sqlite:///absolute/path/to/db  或  sqlite:///./relative
        db_path = url.replace("sqlite:///", "", 1)
        try:
            resolved = Path(db_path).resolve()
        except Exception:
            resolved = db_path
        exists = Path(db_path).exists() if isinstance(db_path, str) else False
        logger.info("📁 DB: SQLite @ %s (existing=%s)", resolved, exists)
        # 部署环境用 SQLite 会因容器重启清盘丢数据 —— 大声警告
        if os.environ.get("RENDER") or os.environ.get("PORT"):
            logger.warning(
                "⚠️  生产环境检测到 SQLite。Render 免费 web service 每次冷启动"
                "会清空文件系统 → 用户注册的账号会全部丢失。请在环境变量里"
                "配置 DATABASE_URL 指向 PostgreSQL（Supabase / Neon 有永久免费额度）。"
            )
    else:
        # 打印时脱敏 password
        import re
        safe = re.sub(r"://([^:]+):[^@]+@", r"://\1:****@", url)
        logger.info("📁 DB: %s", safe)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动时自动建表。"""
    _log_database_status()
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="SmartTracker API",
    description="智能求职管理系统后端 API",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API 路由（统一加 /api 前缀，配合前端客户端路径） ──────────────
api = APIRouter(prefix="/api")
api.include_router(positions.router)
api.include_router(status_logs.router)
api.include_router(notifications.router)
api.include_router(agent_router)
api.include_router(auth_router)
app.include_router(api)


@app.get("/health")
def health_check():
    return {"status": "ok", "version": "0.1.0"}


# ── 生产环境：托管前端静态文件 ──────────────────────────────────────
_frontend_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if _frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(_frontend_dist), html=True), name="frontend")
