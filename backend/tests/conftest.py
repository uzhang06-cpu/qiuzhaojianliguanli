"""
Pytest fixtures — 测试用内存数据库 + 测试客户端 + 自动登录。
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.auth.dependencies import create_access_token
from app.auth.models import User
from app.database import Base, get_db
from app.main import app

TEST_DATABASE_URL = "sqlite:///./test_smart_tracker.db"
_test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
_test_session_local = sessionmaker(autocommit=False, autoflush=False, bind=_test_engine)


@pytest.fixture(scope="function", autouse=True)
def _setup_db():
    """每个测试函数前重建表。"""
    Base.metadata.create_all(bind=_test_engine)
    yield
    Base.metadata.drop_all(bind=_test_engine)


def _override_get_db():
    db = _test_session_local()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client():
    """FastAPI TestClient，自动创建测试用户并附带 Bearer token。"""
    app.dependency_overrides[get_db] = _override_get_db

    # 在测试数据库中创建默认测试用户
    db = _test_session_local()
    from app.auth.dependencies import hash_password
    test_user = User(email="test@test.com", password_hash=hash_password("test123"))
    db.add(test_user)
    db.commit()
    db.refresh(test_user)
    db.close()

    token = create_access_token(test_user.id)

    with TestClient(app) as c:
        c.headers["Authorization"] = f"Bearer {token}"
        yield c

    app.dependency_overrides.clear()


@pytest.fixture
def db_session():
    """直接获取测试数据库会话。"""
    db = _test_session_local()
    try:
        yield db
    finally:
        db.close()
