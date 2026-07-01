"""
CRUD API 集成测试。

覆盖范围：
  - 创建岗位 + 自动写初始状态日志
  - 查询列表（含筛选/搜索/排序）
  - 查询单个
  - 更新岗位信息
  - 状态变更（合法/非法）
  - 状态变更自动写日志
  - 软删除
"""
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient


def _make_position_data(**overrides) -> dict:
    """构造默认的岗位数据。"""
    data = {
        "company": "字节跳动",
        "position": "前端开发工程师",
        "status": "interested",
        "base_location": "北京",
        "salary_range": "30k-50k",
        "job_description": "负责抖音电商前端开发",
    }
    data.update(overrides)
    return data


class TestCreatePosition:
    """创建岗位测试。"""

    def test_create_basic(self, client: TestClient):
        resp = client.post("/api/positions", json=_make_position_data())
        assert resp.status_code == 201
        data = resp.json()
        assert data["company"] == "字节跳动"
        assert data["position"] == "前端开发工程师"
        assert data["status"] == "interested"
        assert data["status_label"] == "意向待投"
        assert data["is_active"] is True
        assert "id" in data

    def test_create_with_ddl(self, client: TestClient):
        ddl = datetime.now() + timedelta(days=7)
        resp = client.post(
            "/api/positions",
            json=_make_position_data(
                status="human_interview",
                next_ddl=ddl.isoformat(),
                interview_link="https://meeting.tencent.com/123",
                interview_platform="腾讯会议",
            ),
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "human_interview"
        assert data["status_label"] == "人工面试"
        assert data["interview_platform"] == "腾讯会议"

    def test_create_auto_logs_status(self, client: TestClient):
        """创建岗位时应该自动写入初始状态日志。"""
        resp = client.post("/api/positions", json=_make_position_data())
        assert resp.status_code == 201
        pos_id = resp.json()["id"]

        log_resp = client.get(f"/api/status-logs?position_id={pos_id}")
        assert log_resp.status_code == 200
        logs = log_resp.json()
        assert len(logs) >= 1
        assert logs[0]["to_status"] == "interested"
        assert logs[0]["from_status"] == ""


class TestListPositions:
    """岗位列表查询测试。"""

    def _create_seed_data(self, client: TestClient):
        """创建种子数据用于筛选/排序测试。"""
        seeds = [
            _make_position_data(company="字节跳动", status="interested"),
            _make_position_data(company="阿里巴巴", status="applied"),
            _make_position_data(company="腾讯", status="human_interview"),
            _make_position_data(company="美团", status="assessment"),
        ]
        for s in seeds:
            client.post("/api/positions", json=s)

    def test_list_all(self, client: TestClient):
        self._create_seed_data(client)
        resp = client.get("/api/positions")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 4

    def test_filter_by_status(self, client: TestClient):
        self._create_seed_data(client)
        resp = client.get("/api/positions?status=applied")
        data = resp.json()
        assert len(data) == 1
        assert data[0]["company"] == "阿里巴巴"

    def test_search_by_keyword(self, client: TestClient):
        self._create_seed_data(client)
        resp = client.get("/api/positions?keyword=字节")
        data = resp.json()
        assert len(data) == 1
        assert data[0]["company"] == "字节跳动"

    def test_sort_by_company_asc(self, client: TestClient):
        self._create_seed_data(client)
        resp = client.get("/api/positions?sort_by=company&sort_dir=asc")
        data = resp.json()
        companies = [p["company"] for p in data]
        assert companies == sorted(companies)


class TestGetPosition:
    """单个岗位查询测试。"""

    def test_get_by_id(self, client: TestClient):
        create_resp = client.post("/api/positions", json=_make_position_data())
        pos_id = create_resp.json()["id"]

        resp = client.get(f"/api/positions/{pos_id}")
        assert resp.status_code == 200
        assert resp.json()["company"] == "字节跳动"

    def test_get_not_found(self, client: TestClient):
        resp = client.get("/api/positions/99999")
        assert resp.status_code == 404


class TestUpdatePosition:
    """岗位信息更新测试。"""

    def test_update_fields(self, client: TestClient):
        create_resp = client.post("/api/positions", json=_make_position_data())
        pos_id = create_resp.json()["id"]

        resp = client.patch(
            f"/api/positions/{pos_id}",
            json={"salary_range": "35k-55k", "base_location": "上海"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["salary_range"] == "35k-55k"
        assert data["base_location"] == "上海"
        assert data["company"] == "字节跳动"  # 未变更字段保持不变


class TestStatusTransition:
    """状态变更测试。"""

    def _create_position(self, client: TestClient, status: str = "interested"):
        resp = client.post("/api/positions", json=_make_position_data(status=status))
        return resp.json()["id"]

    def test_forward_transition(self, client: TestClient):
        pos_id = self._create_position(client)
        resp = client.post(
            f"/api/positions/{pos_id}/status",
            json={"status": "applied", "changed_by": "user"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "applied"
        assert resp.json()["status_label"] == "已投递"

    def test_skip_state_forward(self, client: TestClient):
        """应该允许跳过中间状态向前。"""
        pos_id = self._create_position(client)
        resp = client.post(
            f"/api/positions/{pos_id}/status",
            json={"status": "human_interview", "changed_by": "user"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "human_interview"

    def test_backward_transition(self, client: TestClient):
        pos_id = self._create_position(client, status="applied")
        resp = client.post(
            f"/api/positions/{pos_id}/status",
            json={"status": "interested", "changed_by": "user"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "interested"

    def test_disallowed_transition(self, client: TestClient):
        """offer_evaluation 不能直接回到 applied。"""
        pos_id = self._create_position(client, status="offer_evaluation")
        resp = client.post(
            f"/api/positions/{pos_id}/status",
            json={"status": "applied", "changed_by": "user"},
        )
        assert resp.status_code == 400

    def test_transition_writes_log(self, client: TestClient):
        """状态变更后应自动写入日志。"""
        pos_id = self._create_position(client)
        client.post(
            f"/api/positions/{pos_id}/status",
            json={"status": "applied", "changed_by": "user", "remark": "已投递简历"},
        )

        log_resp = client.get(f"/api/status-logs?position_id={pos_id}")
        logs = log_resp.json()
        # 至少有一条创建日志 + 一条变更日志
        assert len(logs) >= 2
        # 最新的日志应该是 applied
        assert logs[0]["to_status"] == "applied"
        assert logs[0]["from_status"] == "interested"

    def test_self_loop(self, client: TestClient):
        """同状态重入（更新面试时间）应该允许。"""
        pos_id = self._create_position(client, status="human_interview")
        resp = client.post(
            f"/api/positions/{pos_id}/status",
            json={"status": "human_interview", "changed_by": "user"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "human_interview"


class TestDeletePosition:
    """软删除测试。"""

    def test_soft_delete(self, client: TestClient):
        create_resp = client.post("/api/positions", json=_make_position_data())
        pos_id = create_resp.json()["id"]

        resp = client.delete(f"/api/positions/{pos_id}")
        assert resp.status_code == 200

        # 活跃列表中不应出现
        list_resp = client.get("/api/positions?is_active=true")
        assert all(p["is_active"] for p in list_resp.json())

    def test_delete_not_found(self, client: TestClient):
        resp = client.delete("/api/positions/99999")
        assert resp.status_code == 404
