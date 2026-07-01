"""Pytest fixtures — 测试用内存数据库 + 测试客户端。"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app

# 使用内存 SQLite 进行测试
TEST_DATABASE_URL = "sqlite:///./test_smart_tracker.db"
_test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
_test_session_local = sessionmaker(autocommit=False, autoflush=False, bind=_test_engine)


@pytest.fixture(scope="function", autouse=True)
def _setup_db():
    """每个测试函数前重建表，保持隔离。"""
    Base.metadata.create_all(bind=_test_engine)
    yield
    Base.metadata.drop_all(bind=_test_engine)


def _override_get_db():
    """用测试数据库替换生产数据库。"""
    db = _test_session_local()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client():
    """FastAPI TestClient 实例，使用测试数据库。"""
    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def db_session():
    """直接获取测试数据库会话（用于 scheduler 测试等需要直接查数据库的场景）。"""
    db = _test_session_local()
    try:
        yield db
    finally:
        db.close()
