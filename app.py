"""
GEO & ​SEO 可视化看板 - 云平台部署入口

部署后的访问方式:
  看板: https://<your-app>.onrender.com/
  API:  https://<your-app>.onrender.com/api/v1/...
  文档: https://<your-app>.onrender.com/docs

本地运行:
  cd geo-dashboard
  uvicorn app:app --host 0.0.0.0 --port 8000 --reload
"""

import os
import sys
import logging
from pathlib import Path

# 确保可以找到 pipeline 模块
PIPELINE_DIR = Path(__file__).parent / "pipeline"
sys.path.insert(0, str(PIPELINE_DIR))

from api.main import app  # noqa: E402
from database import DailyMetricsDAO, PlatformSnapshotDAO, get_db, DailyMetrics  # noqa: E402

logger = logging.getLogger("geo.deploy")


@app.on_event("startup")
async def auto_seed_if_empty():
    """
    部署时自动检测: 如果数据库为空，自动注入演示数据
    确保看板打开后有数据可见
    """
    try:
        with get_db() as db:
            count = db.query(DailyMetrics).count()
            if count == 0:
                logger.info("数据库为空，自动注入演示数据...")
                import random
                from datetime import datetime, timedelta

                platforms = ["deepseek", "chatgpt", "doubao", "wenxin", "kimi", "perplexity"]
                platform_names = ["DeepSeek", "ChatGPT", "豆包", "文心一言", "Kimi", "Perplexity"]

                for day_offset in range(30, -1, -1):
                    date_str = (datetime.utcnow() - timedelta(days=day_offset)).strftime("%Y-%m-%d")
                    for idx, platform in enumerate(platforms):
                        base_visibility = [92, 78, 85, 71, 66, 58][idx]
                        growth = (30 - day_offset) * 0.5
                        noise = random.uniform(-2, 2)
                        metrics = {
                            "visibility_score": round(min(100, base_visibility + growth + noise), 1),
                            "citation_rate": round(min(100, base_visibility * 0.7 + growth * 0.5 + noise), 1),
                            "mention_count": random.randint(2, 8),
                            "avg_sentiment": round(random.uniform(0.3, 0.9), 3),
                            "referral_traffic": random.randint(200, 1500),
                            "authority_score": round(random.uniform(60, 95), 1),
                            "freshness_score": round(random.uniform(85, 100), 1),
                        }
                        DailyMetricsDAO.upsert(db, date_str, platform, metrics)

                for idx, platform in enumerate(platforms):
                    snapshot = {
                        "platform_name": platform_names[idx],
                        "visibility_score": [92, 78, 85, 71, 66, 58][idx],
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
    except Exception as e:
        logger.warning("自动注入失败 (可能已有数据): %s", e)


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)
