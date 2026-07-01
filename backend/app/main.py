"""
SmartTracker — 智能求职管理系统后端入口。

FastAPI 应用实例，注册路由与生命周期钩子。
生产环境同时托管前端静态文件（合一部署）。
"""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.agent.router import router as agent_router
from app.auth.router import router as auth_router
from app.database import Base, engine
from app.routers import notifications, positions, status_logs


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动时自动建表。"""
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
