"""检查数据库内容"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from database import init_db, get_db, DailyMetricsDAO, PlatformSnapshotDAO
init_db()

with get_db() as db:
    print("=== DailyMetrics ===")
    metrics = DailyMetricsDAO.get_latest_all(db)
    for m in metrics:
        print(m)
    
    print("\n=== PlatformSnapshots ===")
    snapshots = PlatformSnapshotDAO.get_all(db)
    for s in snapshots:
        print(s)
    
    print("\n=== KPIs ===")
    kpis = DailyMetricsDAO.get_aggregate_kpis(db)
    print(kpis)
