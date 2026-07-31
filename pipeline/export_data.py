"""
GEO 数据导出工具
将 SQLite 数据库中的聚合数据导出为 JSON 文件
供 GitHub Actions 定时提交，供 Render 部署时直接读取

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

from database import init_db, get_db, DailyMetricsDAO, PlatformSnapshotDAO, DailyMetrics

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("geo.export")


PLATFORMS = ["deepseek", "chatgpt", "doubao", "wenxin", "kimi", "perplexity"]
PLATFORM_NAMES = ["DeepSeek", "ChatGPT", "豆包", "文心一言", "Kimi", "Perplexity"]
BASE_VISIBILITY = [92, 78, 85, 71, 66, 58]


def ensure_demo_data(db):
    """如果数据库为空，注入演示数据"""
    count = db.query(DailyMetrics).count()
    if count > 0:
        return False  # 已有数据，不需要注入

    logger.info("数据库为空，注入演示数据...")

    for day_offset in range(30, -1, -1):
        date_str = (datetime.utcnow() - timedelta(days=day_offset)).strftime("%Y-%m-%d")
        for idx, platform in enumerate(PLATFORMS):
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

    for idx, platform in enumerate(PLATFORMS):
        snapshot = {
            "platform_name": PLATFORM_NAMES[idx],
            "visibility_score": BASE_VISIBILITY[idx],
            "citation_count": [42, 38, 35, 28, 22, 18][idx],
            "citation_rank": [3, 5, 4, 7, 9, 12][idx],
            "sentiment_score": [0.91, 0.85, 0.76, 0.72, 0.68, 0.55][idx],
            "referral_traffic": [1245, 982, 756, 543, 412, 289][idx],
            "authority_level": ["A+", "A", "A", "B+", "B+", "B"][idx],
            "data_freshness": "实时" if idx < 3 else "24h",
            "status": "优秀" if idx < 3 else "良好" if idx < 5 else "待优化",
        }
        PlatformSnapshotDAO.upsert(db, platform, snapshot)

    logger.info("演示数据注入完成: 30天 x 6平台")
    return True


def export_to_json() -> Path:
    """导出数据库中的聚合数据为 JSON 文件（空数据时自动注入演示数据）"""
    init_db()

    with get_db() as db:
        ensure_demo_data(db)
        kpis = DailyMetricsDAO.get_aggregate_kpis(db)
        platforms = DailyMetricsDAO.get_latest_all(db)
        snapshots = PlatformSnapshotDAO.get_all(db)

    data = {
        "kpis": kpis or {},
        "platforms": platforms or [],
        "snapshots": snapshots or [],
        "exported_at": datetime.utcnow().isoformat(),
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

    return output_path


if __name__ == "__main__":
    export_to_json()
