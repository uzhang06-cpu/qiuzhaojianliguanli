"""
Phase 5 — Scheduler 引擎测试。
"""
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.engine.scheduler import Notification, scan
from app.models import Position, StatusLog


class TestPreEvent:
    """临期强提醒测试。"""

    def _create(self, client: TestClient, next_ddl: str):
        return client.post("/api/positions", json={
            "company": "字节跳动", "position": "前端",
            "status": "human_interview", "next_ddl": next_ddl,
        }).json()

    def test_under_2h_danger(self, client: TestClient, db_session: Session):
        ddl = (datetime.now() + timedelta(hours=1)).isoformat()
        pos = self._create(client, ddl)
        result = scan(db_session)
        danger = [n for n in result.notifications if n.severity == "danger" and n.position_id == pos["id"]]
        assert len(danger) == 1

    def test_under_24h_warning(self, client: TestClient, db_session: Session):
        ddl = (datetime.now() + timedelta(hours=12)).isoformat()
        pos = self._create(client, ddl)
        result = scan(db_session)
        warn = [n for n in result.notifications if n.severity == "warning" and n.position_id == pos["id"]]
        assert len(warn) == 1

    def test_far_ddl_no_notification(self, client: TestClient, db_session: Session):
        ddl = (datetime.now() + timedelta(hours=48)).isoformat()
        pos = self._create(client, ddl)
        result = scan(db_session)
        for_pos = [n for n in result.notifications if n.position_id == pos["id"]]
        assert len(for_pos) == 0


class TestPostReview:
    """复盘提醒测试。"""

    def _create(self, client: TestClient, next_ddl: str, notes=None):
        return client.post("/api/positions", json={
            "company": "字节跳动", "position": "前端",
            "status": "human_interview", "next_ddl": next_ddl,
            "notes": notes,
        }).json()

    def test_needs_review(self, client: TestClient, db_session: Session):
        ddl = (datetime.now() - timedelta(hours=4)).isoformat()
        pos = self._create(client, ddl)
        result = scan(db_session)
        review = [n for n in result.notifications if n.type == "post_review" and n.position_id == pos["id"]]
        assert len(review) == 1

    def test_skip_if_noted(self, client: TestClient, db_session: Session):
        ddl = (datetime.now() - timedelta(hours=4)).isoformat()
        pos = self._create(client, ddl, notes="已复盘")
        result = scan(db_session)
        found = [n for n in result.notifications if n.position_id == pos["id"]]
        assert len(found) == 0

    def test_skip_if_recent(self, client: TestClient, db_session: Session):
        ddl = (datetime.now() - timedelta(minutes=30)).isoformat()
        pos = self._create(client, ddl)
        result = scan(db_session)
        found = [n for n in result.notifications if n.position_id == pos["id"] and n.type == "post_review"]
        assert len(found) == 0


class TestDeadState:
    """僵尸状态唤醒测试。"""

    def _create_stagnant(self, client: TestClient, db_session: Session, days: int):
        # 先用默认状态创建（status=interested），创建日志是新的但不影响
        pos = client.post("/api/positions", json={
            "company": "字节跳动", "position": "前端",
        }).json()
        # 直接调状态变更到 applied，再改日志时间为过去
        client.post(f"/api/positions/{pos['id']}/status", json={
            "status": "applied", "changed_by": "test",
        })
        # 把最近一条 to_status=applied 的日志时间改为 days 天前
        latest = (
            db_session.query(StatusLog)
            .filter(StatusLog.position_id == pos["id"], StatusLog.to_status == "applied")
            .order_by(StatusLog.created_at.desc())
            .first()
        )
        if latest:
            latest.created_at = datetime.now() - timedelta(days=days)
            db_session.commit()
        return pos

    def test_stagnant_over_7_days(self, client: TestClient, db_session: Session):
        pos = self._create_stagnant(client, db_session, 10)
        result = scan(db_session)
        dead = [n for n in result.notifications if n.type == "dead_state" and n.position_id == pos["id"]]
        assert len(dead) == 1

    def test_recent_no_notification(self, client: TestClient, db_session: Session):
        pos = self._create_stagnant(client, db_session, 2)
        result = scan(db_session)
        dead = [n for n in result.notifications if n.type == "dead_state" and n.position_id == pos["id"]]
        assert len(dead) == 0


class TestNotificationsAPI:
    """通知 API 端点测试。"""

    def test_get_notifications(self, client: TestClient, db_session: Session):
        ddl = (datetime.now() + timedelta(hours=1)).isoformat()
        client.post("/api/positions", json={
            "company": "字节", "position": "前端",
            "status": "human_interview", "next_ddl": ddl,
        })
        resp = client.get("/api/notifications")
        assert resp.status_code == 200
        data = resp.json()
        assert "notifications" in data
        assert data["total_positions"] >= 1
        assert len(data["notifications"]) >= 1

    def test_empty(self, client: TestClient, db_session: Session):
        resp = client.get("/api/notifications")
        assert resp.status_code == 200
        assert resp.json()["total_positions"] == 0
