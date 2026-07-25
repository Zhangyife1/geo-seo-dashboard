"""注入演示数据脚本"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from datetime import datetime, timedelta
import random
from database import init_db, get_db, DailyMetricsDAO, PlatformSnapshotDAO

init_db()

with get_db() as db:
    platforms = ["deepseek", "chatgpt", "doubao", "wenxin", "kimi", "perplexity"]
    platform_names = ["DeepSeek", "ChatGPT", "豆包", "文心一言", "Kimi", "Perplexity"]
    
    for day_offset in range(30, -1, -1):
        date_str = (datetime.utcnow() - timedelta(days=day_offset)).strftime("%Y-%m-%d")
        for idx, platform in enumerate(platforms):
            base = [92, 78, 85, 71, 66, 58][idx]
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
    
    print("Demo data seeded successfully!")
