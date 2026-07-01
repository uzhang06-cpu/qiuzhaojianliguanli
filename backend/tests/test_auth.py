"""Auth 端点测试 — 注册 / 登录 / 鉴权 / 数据隔离。"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.auth.dependencies import hash_password, create_access_token, decode_access_token
from app.auth.models import User


class TestAuthUnit:
    """密码 + JWT 单元测试。"""

    def test_hash_and_verify(self):
        hashed = hash_password("hello123")
        assert hashed.startswith("$sha256$")
        from app.auth.dependencies import verify_password
        assert verify_password("hello123", hashed) is True
        assert verify_password("wrong", hashed) is False

    def test_jwt_roundtrip(self):
        token = create_access_token(42)
        user_id = decode_access_token(token)
        assert user_id == 42

    def test_jwt_invalid(self):
        assert decode_access_token("invalid-token") is None


class TestAuthAPI:
    """Auth API 端点测试。"""

    def test_register(self, client: TestClient):
        resp = client.post("/auth/register", json={
            "email": "new@user.com",
            "password": "pass123",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert "access_token" in data
        assert data["user"]["email"] == "new@user.com"

    def test_register_duplicate(self, client: TestClient):
        client.post("/auth/register", json={"email": "dup@test.com", "password": "pass123"})
        resp = client.post("/auth/register", json={"email": "dup@test.com", "password": "pass456"})
        assert resp.status_code == 409

    def test_login(self, client: TestClient):
        # 先注册
        email, pwd = "login@test.com", "mypassword"
        client.post("/auth/register", json={"email": email, "password": pwd})

        # 再登录
        resp = client.post("/auth/login", json={"email": email, "password": pwd})
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["user"]["email"] == email

    def test_login_wrong_password(self, client: TestClient):
        client.post("/auth/register", json={"email": "fail@test.com", "password": "correct"})
        resp = client.post("/auth/login", json={"email": "fail@test.com", "password": "wrong"})
        assert resp.status_code == 401

    def test_me_requires_auth(self, client: TestClient):
        """未登录访问 /auth/me 应返回 401。"""
        # 创建一个不带 token 的请求
        from app.database import get_db, Base
        from app.main import app
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        _engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=_engine)
        _session = sessionmaker(bind=_engine)

        def _override():
            db = _session()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = _override
        c = TestClient(app)
        resp = c.get("/auth/me")
        assert resp.status_code == 401
        app.dependency_overrides.clear()

    def test_me_returns_user(self, client: TestClient):
        resp = client.get("/auth/me")
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "test@test.com"
