"""
GEO 数据导出工具
将 SQLite 数据库中的聚合数据导出为 JSON 文件
供 GitHub Actions 定时提交，供 Render 部署时直接读取

增强功能:
- 数据来源标记（real/demo）
- 智能补全缺失平台
- 数据质量报告

用法:
    cd pipeline
    python export_data.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import json
import logging
import random
from datetime import datetime, timedelta

from database import init_db, get_db, DailyMetricsDAO, PlatformSnapshotDAO, DailyMetrics, PlatformSnapshot, CitationRecord

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("geo.export")


PLATFORMS = ["deepseek", "chatgpt", "doubao", "wenxin", "kimi", "perplexity"]
PLATFORM_NAMES = ["DeepSeek", "ChatGPT", "豆包", "文心一言", "Kimi", "Perplexity"]
BASE_VISIBILITY = [92, 78, 85, 71, 66, 58]
BASE_CITATION_COUNT = [42, 38, 35, 28, 22, 18]
BASE_CITATION_RANK = [3, 5, 4, 7, 9, 12]
BASE_SENTIMENT = [0.91, 0.85, 0.76, 0.72, 0.68, 0.55]
BASE_REFERRAL = [1245, 982, 756, 543, 412, 289]
BASE_AUTHORITY = ["A+", "A", "A", "B+", "B+", "B"]


def seed_demo_for_platform(db, platform: str, idx: int):
    """为单个平台注入演示数据（30天历史 + 快照）"""
    today = datetime.utcnow().strftime("%Y-%m-%d")

    # 30天历史数据
    for day_offset in range(30, -1, -1):
        date_str = (datetime.utcnow() - timedelta(days=day_offset)).strftime("%Y-%m-%d")
        base = BASE_VISIBILITY[idx]
        growth = (30 - day_offset) * 0.5
        noise = random.uniform(-2, 2)
        metrics = {
            "visibility_score": round(min(100, base + growth + noise), 1),
            "citation_rate": round(min(100, base * 0.7 + growth * 0.5 + noise), 1),
            "mention_count": random.randint(2, 8),
            "avg_sentiment": round(random.uniform(0.3, 0.9), 3),
            "referral_traffic": random.randint(200, 1500),
            "authority_score": round(random.uniform(60, 95), 1),
            "freshness_score": round(random.uniform(85, 100), 1),
        }
        DailyMetricsDAO.upsert(db, date_str, platform, metrics)

    # 快照
    snapshot = {
        "platform_name": PLATFORM_NAMES[idx],
        "visibility_score": BASE_VISIBILITY[idx],
        "citation_count": BASE_CITATION_COUNT[idx],
        "citation_rank": BASE_CITATION_RANK[idx],
        "sentiment_score": BASE_SENTIMENT[idx],
        "referral_traffic": BASE_REFERRAL[idx],
        "authority_level": BASE_AUTHORITY[idx],
        "data_freshness": "实时" if idx < 3 else "24h",
        "status": "优秀" if idx < 3 else "良好" if idx < 5 else "待优化",
    }
    PlatformSnapshotDAO.upsert(db, platform, snapshot)


def ensure_all_platforms_have_data(db):
    """
    确保所有6个平台都有数据，缺失的用演示数据补全

    判定逻辑（修正版 v2）:
    - real: 有 CitationRecord 且 data_source 为 api/browser（真实 API/浏览器采集，无论是否提及品牌）
    - simulated: 有 CitationRecord 但 data_source 为 simulated/search/unknown（模拟/搜索引擎兜底）
    - demo: 无任何 CitationRecord（完全未采集，用种子数据补全）
    """
    filled = []
    real_platforms = []
    simulated_platforms = []

    for idx, platform in enumerate(PLATFORMS):
        # 查询该平台的所有引用记录
        citations = db.query(CitationRecord).filter(
            CitationRecord.platform == platform
        ).all()

        # 检查是否有真实采集记录（API/浏览器，无论是否提及品牌）
        has_real_data = any(
            c.data_source in ("api", "browser")
            for c in citations
        )

        # 检查是否有有效品牌提及（用于日志展示）
        has_real_mention = any(
            c.brand_mentioned and c.data_source in ("api", "browser")
            for c in citations
        )

        # 检查是否有模拟/搜索数据
        has_simulated = any(
            c.data_source in ("simulated", "search", "unknown")
            for c in citations
        )

        # 检查 DailyMetrics
        metric_count = db.query(DailyMetrics).filter(
            DailyMetrics.platform == platform
        ).count()

        # 检查 PlatformSnapshot
        snapshot = db.query(PlatformSnapshot).filter(
            PlatformSnapshot.platform == platform
        ).first()

        if has_real_data:
            real_platforms.append(platform)
            mention_status = "有提及" if has_real_mention else "无提及(品牌可见性为零)"
            logger.info("平台 [%s] 真实API数据(%s), 记录数: %d",
                       PLATFORM_NAMES[idx], mention_status, len(citations))
            # 有真实数据但缺快照，补全
            if not snapshot:
                logger.info("平台 [%s] 有真实数据但缺快照，补全快照...", PLATFORM_NAMES[idx])
                snapshot = {
                    "platform_name": PLATFORM_NAMES[idx],
                    "visibility_score": BASE_VISIBILITY[idx],
                    "citation_count": BASE_CITATION_COUNT[idx],
                    "citation_rank": BASE_CITATION_RANK[idx],
                    "sentiment_score": BASE_SENTIMENT[idx],
                    "referral_traffic": BASE_REFERRAL[idx],
                    "authority_level": BASE_AUTHORITY[idx],
                    "data_freshness": "实时",
                    "status": "优秀" if idx < 3 else "良好" if idx < 5 else "待优化",
                }
                PlatformSnapshotDAO.upsert(db, platform, snapshot)
        elif has_simulated or metric_count > 0:
            simulated_platforms.append(platform)
            # 有模拟数据但缺快照
            if not snapshot:
                logger.info("平台 [%s] 有模拟数据，补全快照...", PLATFORM_NAMES[idx])
                seed_demo_for_platform(db, platform, idx)
                filled.append(platform)
        else:
            logger.info("平台 [%s] 完全无数据，注入演示数据...", PLATFORM_NAMES[idx])
            seed_demo_for_platform(db, platform, idx)
            filled.append(platform)

    if filled:
        logger.info("已为 %d 个平台补全演示数据: %s", len(filled), filled)
    if real_platforms:
        logger.info("有真实数据的平台: %s", real_platforms)
    if simulated_platforms:
        logger.info("使用模拟数据的平台: %s", simulated_platforms)
    if not filled and not simulated_platforms:
        logger.info("所有6个平台均有数据，无需补全")

    return filled, real_platforms, simulated_platforms


def _build_trend(db, platforms: list, days: int = 30) -> list:
    """构建趋势数据：仅基于指定平台（真实平台口径），避免模拟/演示历史污染趋势图。"""
    from sqlalchemy import func
    if not platforms:
        return []
    since = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
    rows = (
        db.query(
            DailyMetrics.date,
            func.avg(DailyMetrics.visibility_score).label("avg_visibility"),
            func.avg(DailyMetrics.citation_rate).label("avg_citation_rate"),
            func.sum(DailyMetrics.mention_count).label("total_mentions"),
            func.avg(DailyMetrics.avg_sentiment).label("avg_sentiment"),
            func.sum(DailyMetrics.referral_traffic).label("total_traffic"),
        )
        .filter(
            DailyMetrics.platform.in_(platforms),
            DailyMetrics.date >= since,
        )
        .group_by(DailyMetrics.date)
        .order_by(DailyMetrics.date.asc())
        .all()
    )
    return [
        {
            "date": row.date,
            "avg_visibility": round(float(row.avg_visibility or 0), 1),
            "avg_citation_rate": round(float(row.avg_citation_rate or 0), 1),
            "total_mentions": int(row.total_mentions or 0),
            "avg_sentiment": round(float(row.avg_sentiment or 0), 3),
            "total_traffic": int(row.total_traffic or 0),
        }
        for row in rows
    ]


def export_to_json() -> Path:
    """导出数据库中的聚合数据为 JSON 文件"""
    init_db()

    with get_db() as db:
        # 1. 确保所有6个平台都有数据（缺失的用演示数据补全）
        # 返回: (demo_platforms, real_platforms, simulated_platforms)
        demo_platforms, real_platforms, simulated_platforms = ensure_all_platforms_have_data(db)

        # 2. 导出聚合数据
        kpis = DailyMetricsDAO.get_aggregate_kpis(db)
        kpis_real = (
            DailyMetricsDAO.get_aggregate_kpis(db, platforms=real_platforms)
            if real_platforms
            else {}
        )
        platforms = DailyMetricsDAO.get_latest_all(db)
        snapshots = PlatformSnapshotDAO.get_all(db)

        # 3. 计算真实 KPI 变化（基于历史数据，而非硬编码）
        kpi_changes = _calculate_kpi_changes(db)
        kpi_changes_real = (
            _calculate_kpi_changes(db, platforms=real_platforms)
            if real_platforms
            else {}
        )

        # 4. 构建真实平台趋势（仅真实平台，避免模拟历史污染）
        trend = _build_trend(db, real_platforms, days=30)

    # 4. 为每个平台标记数据来源 (real / simulated / demo)
    for p in platforms:
        if p["platform"] in real_platforms:
            p["data_source"] = "real"
        elif p["platform"] in simulated_platforms:
            p["data_source"] = "simulated"
        else:
            p["data_source"] = "demo"

    for s in snapshots:
        if s["platform"] in real_platforms:
            s["data_source"] = "real"
        elif s["platform"] in simulated_platforms:
            s["data_source"] = "simulated"
        else:
            s["data_source"] = "demo"

    data = {
        "kpis": kpis or {},
        "kpis_real": kpis_real or {},
        "kpi_changes": kpi_changes,
        "kpi_changes_real": kpi_changes_real,
        "trend": trend,
        "trend_source": "real_platforms" if real_platforms else "none",
        "platforms": platforms or [],
        "snapshots": snapshots or [],
        "exported_at": datetime.utcnow().isoformat(),
        "data_quality": {
            "real_platforms": real_platforms,
            "simulated_platforms": simulated_platforms,
            "demo_platforms": demo_platforms,
            "real_count": len(real_platforms),
            "simulated_count": len(simulated_platforms),
            "demo_count": len(demo_platforms),
            "total_platforms": len(PLATFORMS),
            "has_real_data": len(real_platforms) > 0,
        },
    }

    output_dir = Path(__file__).parent / "data"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "dashboard_data.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    logger.info(f"数据已导出: {output_path}")
    logger.info(f"  - KPIs: {len(data['kpis'])} 项")
    logger.info(f"  - Platforms: {len(data['platforms'])} 个")
    logger.info(f"  - Snapshots: {len(data['snapshots'])} 个")
    logger.info(f"  - Real data: {len(real_platforms)} 个平台")
    logger.info(f"  - Simulated data: {len(simulated_platforms)} 个平台")
    logger.info(f"  - Demo data: {len(demo_platforms)} 个平台")

    return output_path


def _calculate_kpi_changes(db, platforms: list = None) -> dict:
    """基于历史数据计算 KPI 环比变化（而非硬编码）"""
    from sqlalchemy import func, desc
    try:
        # 获取最近7天和前7天的数据对比
        today = datetime.utcnow().strftime("%Y-%m-%d")
        week_ago = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")
        two_weeks_ago = (datetime.utcnow() - timedelta(days=14)).strftime("%Y-%m-%d")

        # 最近7天平均
        recent_query = db.query(
            func.avg(DailyMetrics.visibility_score).label('avg_vis'),
            func.avg(DailyMetrics.citation_rate).label('avg_cit'),
            func.sum(DailyMetrics.mention_count).label('sum_mention'),
            func.avg(DailyMetrics.avg_sentiment).label('avg_sent'),
            func.sum(DailyMetrics.referral_traffic).label('sum_traffic'),
            func.avg(DailyMetrics.authority_score).label('avg_auth'),
        ).filter(
            DailyMetrics.date >= week_ago,
            DailyMetrics.date <= today,
        )
        if platforms:
            recent_query = recent_query.filter(DailyMetrics.platform.in_(platforms))
        recent = recent_query.first()

        # 前7天平均
        previous_query = db.query(
            func.avg(DailyMetrics.visibility_score).label('avg_vis'),
            func.avg(DailyMetrics.citation_rate).label('avg_cit'),
            func.sum(DailyMetrics.mention_count).label('sum_mention'),
            func.avg(DailyMetrics.avg_sentiment).label('avg_sent'),
            func.sum(DailyMetrics.referral_traffic).label('sum_traffic'),
            func.avg(DailyMetrics.authority_score).label('avg_auth'),
        ).filter(
            DailyMetrics.date >= two_weeks_ago,
            DailyMetrics.date < week_ago,
        )
        if platforms:
            previous_query = previous_query.filter(DailyMetrics.platform.in_(platforms))
        previous = previous_query.first()

        if not recent or not previous:
            return {}

        def calc_change(curr, prev):
            if not prev or prev == 0:
                return 0
            return round(((curr - prev) / prev) * 100, 1)

        return {
            "visibility_change": calc_change(float(recent.avg_vis or 0), float(previous.avg_vis or 0)),
            "citation_change": calc_change(float(recent.avg_cit or 0), float(previous.avg_cit or 0)),
            "mention_change": int((recent.sum_mention or 0) - (previous.sum_mention or 0)),
            "sentiment_change": calc_change(float(recent.avg_sent or 0), float(previous.avg_sent or 0)),
            "traffic_change": calc_change(int(recent.sum_traffic or 0), int(previous.sum_traffic or 0)),
            "health_change": calc_change(float(recent.avg_auth or 0), float(previous.avg_auth or 0)),
            "comparison_period": f"{two_weeks_ago} ~ {today}",
        }
    except Exception as e:
        logger.warning("计算KPI环比失败: %s", e)
        return {}


if __name__ == "__main__":
    export_to_json()
