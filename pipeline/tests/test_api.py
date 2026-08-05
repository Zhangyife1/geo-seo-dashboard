"""
API 接口单元测试
运行: cd pipeline && python -m pytest tests/test_api.py -v
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


class TestHealthEndpoint:
    def test_healthz(self):
        """测试健康检查端点"""
        response = client.get("/healthz")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "timestamp" in data


class TestDashboardAPI:
    def test_dashboard_all(self):
        """测试看板聚合接口"""
        response = client.get("/api/v1/dashboard/all")
        assert response.status_code == 200
        data = response.json()
        assert "kpis" in data
        assert "platforms" in data
        assert "snapshots" in data
    
    def test_kpis(self):
        """测试KPI接口"""
        response = client.get("/api/v1/kpis")
        assert response.status_code in (200, 404)  # 404 if no data yet
    
    def test_platforms(self):
        """测试平台接口"""
        response = client.get("/api/v1/platforms")
        assert response.status_code in (200, 404)
    
    def test_snapshots(self):
        """测试快照接口"""
        response = client.get("/api/v1/snapshots")
        assert response.status_code in (200, 404)


class TestSeedAuth:
    def test_seed_without_auth(self):
        """测试未授权访问 seed 接口"""
        response = client.post("/api/v1/seed")
        # 应该返回 403
        assert response.status_code == 403
    
    def test_seed_with_wrong_auth(self):
        """测试错误密钥访问 seed 接口"""
        response = client.post("/api/v1/seed", headers={"X-Admin-Key": "wrong"})
        assert response.status_code == 403


class TestTrendAPI:
    def test_trend_default(self):
        """测试趋势接口默认参数"""
        response = client.get("/api/v1/trend")
        assert response.status_code == 200
        data = response.json()
        assert "trend" in data
        assert "days" in data
