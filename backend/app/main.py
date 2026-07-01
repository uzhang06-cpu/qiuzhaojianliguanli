"""
SmartTracker — 智能求职管理系统后端入口。

FastAPI 应用实例，注册路由与生命周期钩子。
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.agent.router import router as agent_router
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

# CORS — 允许前端开发服务器跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应收紧
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(positions.router)
app.include_router(status_logs.router)
app.include_router(notifications.router)
app.include_router(agent_router)


@app.get("/health")
def health_check():
    """健康检查端点。"""
    return {"status": "ok", "version": "0.1.0"}
