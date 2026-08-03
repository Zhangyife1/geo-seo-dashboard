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
    """确保所有6个平台都有数据，缺失的用演示数据补全"""
    filled = []
    real_platforms = []

    for idx, platform in enumerate(PLATFORMS):
        # 检查是否有真实引用记录
        citation_count = db.query(CitationRecord).filter(
            CitationRecord.platform == platform
        ).count()

        # 检查 DailyMetrics 是否有该平台数据
        metric_count = db.query(DailyMetrics).filter(
            DailyMetrics.platform == platform
        ).count()

        # 检查 PlatformSnapshot 是否有该平台快照
        snapshot = db.query(PlatformSnapshot).filter(
            PlatformSnapshot.platform == platform
        ).first()

        if citation_count > 0 or metric_count > 0:
            real_platforms.append(platform)
            # 即使有真实数据，如果缺少快照也补全
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
        elif metric_count == 0 or not snapshot:
            logger.info("平台 [%s] 缺少数据，注入演示数据...", PLATFORM_NAMES[idx])
            seed_demo_for_platform(db, platform, idx)
            filled.append(platform)

    if filled:
        logger.info("已为 %d 个平台补全演示数据: %s", len(filled), filled)
    if real_platforms:
        logger.info("有真实数据的平台: %s", real_platforms)
    if not filled:
        logger.info("所有6个平台均有数据，无需补全")

    return filled, real_platforms


def export_to_json() -> Path:
    """导出数据库中的聚合数据为 JSON 文件"""
    init_db()

    with get_db() as db:
        # 1. 确保所有6个平台都有数据（缺失的用演示数据补全）
        filled_platforms, real_platforms = ensure_all_platforms_have_data(db)

        # 2. 导出聚合数据
        kpis = DailyMetricsDAO.get_aggregate_kpis(db)
        platforms = DailyMetricsDAO.get_latest_all(db)
        snapshots = PlatformSnapshotDAO.get_all(db)

    # 3. 为每个平台标记数据来源
    for p in platforms:
        p["data_source"] = "real" if p["platform"] in real_platforms else "demo"

    for s in snapshots:
        s["data_source"] = "real" if s["platform"] in real_platforms else "demo"

    data = {
        "kpis": kpis or {},
        "platforms": platforms or [],
        "snapshots": snapshots or [],
        "exported_at": datetime.utcnow().isoformat(),
        "data_quality": {
            "real_platforms": real_platforms,
            "demo_platforms": filled_platforms,
            "real_count": len(real_platforms),
            "demo_count": len(filled_platforms),
            "total_platforms": len(PLATFORMS),
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
    logger.info(f"  - Demo data: {len(filled_platforms)} 个平台")

    return output_path


if __name__ == "__main__":
    export_to_json()
