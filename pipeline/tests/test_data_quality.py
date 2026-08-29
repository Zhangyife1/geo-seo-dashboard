"""数据口径相关单测：真实平台 KPI、真实趋势构建、周报生成。"""

import os
from datetime import datetime, timedelta

from database import DailyMetricsDAO, get_db, init_db  # noqa: E402
from export_data import _build_trend  # noqa: E402
from generate_report import build_report  # noqa: E402


def _seed():
    init_db()
    today = datetime.utcnow().strftime("%Y-%m-%d")
    yesterday = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
    with get_db() as db:
        for date in (yesterday, today):
            DailyMetricsDAO.upsert(db, date, "deepseek", {
                "visibility_score": 40.0, "citation_rate": 30.0, "mention_count": 1,
                "avg_sentiment": 0.5, "referral_traffic": 100,
                "authority_score": 70.0, "freshness_score": 90.0,
            })
            DailyMetricsDAO.upsert(db, date, "kimi", {
                "visibility_score": 50.0, "citation_rate": 40.0, "mention_count": 1,
                "avg_sentiment": 0.6, "referral_traffic": 120,
                "authority_score": 75.0, "freshness_score": 92.0,
            })
            DailyMetricsDAO.upsert(db, date, "chatgpt", {
                "visibility_score": 99.0, "citation_rate": 99.0, "mention_count": 8,
                "avg_sentiment": 0.9, "referral_traffic": 999,
                "authority_score": 95.0, "freshness_score": 99.0,
            })


def test_kpis_real_only_excludes_demo():
    _seed()
    with get_db() as db:
        all_kpis = DailyMetricsDAO.get_aggregate_kpis(db)
        real_kpis = DailyMetricsDAO.get_aggregate_kpis(db, platforms=["deepseek", "kimi"])
        assert all_kpis["mention_count"] > real_kpis["mention_count"]
        assert real_kpis["mention_count"] == 2  # deepseek 1 + kimi 1


def test_build_trend_only_real_platforms():
    _seed()
    with get_db() as db:
        trend = _build_trend(db, ["deepseek", "kimi"], days=30)
        assert len(trend) == 2  # 昨天 + 今天
        assert all(t["total_mentions"] == 2 for t in trend)
        assert _build_trend(db, [], days=30) == []


def test_build_report_contains_quality_and_kpis():
    data = {
        "kpis": {
            "ai_visibility_index": 55.0, "citation_rate": 60.0, "mention_count": 10,
            "sentiment_score": 70.0, "referral_traffic": 500,
            "structural_health": 80.0, "record_date": "2026-08-05",
        },
        "kpis_real": {
            "ai_visibility_index": 45.0, "citation_rate": 35.0, "mention_count": 2,
            "sentiment_score": 60.0, "referral_traffic": 220,
            "structural_health": 72.0, "record_date": "2026-08-05",
        },
        "kpi_changes": {},
        "kpi_changes_real": {},
        "trend": [{
            "date": "2026-08-05", "avg_visibility": 45.0, "avg_citation_rate": 35.0,
            "total_mentions": 2, "avg_sentiment": 0.55, "total_traffic": 220,
        }],
        "trend_source": "real_platforms",
        "platforms": [],
        "snapshots": [],
        "exported_at": "2026-08-05T00:00:00",
        "data_quality": {
            "real_count": 2, "demo_count": 1,
            "total_platforms": 3, "has_real_data": True,
        },
    }
    md = build_report(data)
    assert "# GEO 周度运营报告" in md
    assert "真实平台口径" in md
    assert "真实采集 **2** 个平台（共 3），其余为预留演示数据" in md
    assert "模拟" not in md
