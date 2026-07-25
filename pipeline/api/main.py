"""
FastAPI 接口服务
提供 GEO & SEO 数据的 RESTful API

启动方式:
    uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
    或: python run_api.py

接口文档:
    http://localhost:8000/docs  (Swagger UI)
    http://localhost:8000/redoc (ReDoc)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from config import API_CONFIG, BRAND_CONFIG
from database import (
    init_db, get_db, get_db_gen,
    DailyMetricsDAO, PlatformSnapshotDAO, 
    CitationRecordDAO, CrawlTaskDAO
)

# 项目路径
PROJECT_ROOT = Path(__file__).parent.parent.parent  # geo-dashboard/
DASHBOARD_DIR = PROJECT_ROOT  # 看板文件所在目录

# 初始化数据库
init_db()

# 日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("geo.api")

# FastAPI 应用
app = FastAPI(
    title=API_CONFIG["title"],
    version=API_CONFIG["version"],
    description=f"""
    GEO & SEO 量化数据 API
    
    品牌: {BRAND_CONFIG['name']}
    域名: {BRAND_CONFIG['domain']}
    
    提供以下数据接口:
    - KPI 聚合指标
    - 各平台详细数据
    - 趋势数据
    - 平台快照
    - 引用明细
    """
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=API_CONFIG["cors_origins"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== 静态文件 & 看板页面 ====================

# 挂载静态资源目录（看板引用的 assets/）
_assets_dir = DASHBOARD_DIR / "assets"
if _assets_dir.is_dir():
    app.mount("/assets", StaticFiles(directory=str(_assets_dir)), name="assets")


@app.get("/", tags=["Dashboard"], response_class=HTMLResponse)
def serve_dashboard():
    """部署模式：返回看板 HTML 页面"""
    html_path = DASHBOARD_DIR / "geo-dashboard.html"
    if html_path.exists():
        return FileResponse(str(html_path), media_type="text/html; charset=utf-8")
    return HTMLResponse(content="<h1>Dashboard file not found</h1>", status_code=404)


@app.get("/api", tags=["Root"])
def api_root():
    """API 根路径 - 返回服务状态"""
    return {
        "service": "GEO & SEO Data API",
        "version": API_CONFIG["version"],
        "brand": BRAND_CONFIG["name"],
        "domain": BRAND_CONFIG["domain"],
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
        "docs": "/docs"
    }


# ==================== Pydantic 模型 ====================

class KPIResponse(BaseModel):
    ai_visibility_index: float = Field(..., description="AI可见性指数 0-100")
    citation_rate: float = Field(..., description="AI引用率 %")
    mention_count: int = Field(..., description="品牌提及次数")
    sentiment_score: float = Field(..., description="情感评分 0-100")
    referral_traffic: int = Field(..., description="AI引荐流量估算")
    structural_health: float = Field(..., description="结构化数据健康度")
    record_date: str = Field(..., description="数据日期")


class PlatformMetrics(BaseModel):
    platform: str
    platform_name: str
    visibility_score: float
    citation_rate: float
    mention_count: int
    avg_sentiment: float
    referral_traffic: int
    authority_score: float
    freshness_score: float
    date: str


class TrendPoint(BaseModel):
    date: str
    visibility_score: float
    citation_rate: float
    mention_count: int
    avg_sentiment: float
    referral_traffic: int


class PlatformSnapshot(BaseModel):
    platform: str
    platform_name: str
    visibility_score: float
    citation_count: int
    citation_rank: Optional[int]
    sentiment_score: float
    referral_traffic: int
    authority_level: str
    data_freshness: str
    status: str
    last_updated: Optional[str]


class CrawlTaskItem(BaseModel):
    id: int
    platform: str
    query: str
    status: str
    created_at: datetime


# ==================== API 路由 ====================




@app.get("/api/v1/kpis", response_model=KPIResponse, tags=["KPI"])
def get_kpis():
    """
    获取聚合 KPI 指标
    
    返回看板顶部6个核心指标的聚合值:
    - AI可见性指数
    - AI引用率
    - 品牌提及频率
    - 情感好感度
    - AI引荐流量
    - 结构化数据健康度
    """
    db = next(get_db_gen())
    kpis = DailyMetricsDAO.get_aggregate_kpis(db)
    
    if not kpis:
        raise HTTPException(status_code=404, detail="暂无数据，请先运行爬虫采集")
    
    return KPIResponse(**kpis)


@app.get("/api/v1/platforms", response_model=List[PlatformMetrics], tags=["Platforms"])
def get_platform_metrics():
    """
    获取所有 AI 平台的最新指标
    
    返回各平台（DeepSeek/ChatGPT/豆包等）的最新量化数据
    """
    db = next(get_db_gen())
    data = DailyMetricsDAO.get_latest_all(db)
    return [PlatformMetrics(**item) for item in data]


@app.get("/api/v1/platforms/{platform}", response_model=List[TrendPoint], tags=["Platforms"])
def get_platform_trend(
    platform: str,
    days: int = Query(30, ge=7, le=365, description="查询天数范围")
):
    """
    获取指定平台的历史趋势数据
    
    - **platform**: 平台标识 (deepseek/chatgpt/doubao/wenxin/kimi/perplexity)
    - **days**: 回溯天数 (7-365)
    
    返回时间序列数据，用于绘制趋势图
    """
    db = next(get_db_gen())
    data = DailyMetricsDAO.get_trend(db, platform, days)
    
    if not data:
        raise HTTPException(status_code=404, detail=f"平台 '{platform}' 暂无数据")
    
    return [TrendPoint(**item) for item in data]


@app.get("/api/v1/snapshots", response_model=List[PlatformSnapshot], tags=["Snapshots"])
def get_platform_snapshots():
    """
    获取各平台快照数据
    
    用于看板底部的平台明细表格
    """
    db = next(get_db_gen())
    data = PlatformSnapshotDAO.get_all(db)
    return [PlatformSnapshot(**item) for item in data]


@app.get("/api/v1/mentions", tags=["Mentions"])
def get_mentions_summary(days: int = Query(30, ge=1, le=90)):
    """
    获取品牌提及汇总
    
    返回各平台在指定天数内的提及统计
    """
    db = next(get_db_gen())
    return CitationRecordDAO.get_mentions_summary(db, days)


@app.get("/api/v1/tasks", response_model=List[CrawlTaskItem], tags=["Tasks"])
def get_recent_tasks(hours: int = Query(24, ge=1, le=168)):
    """
    获取最近的抓取任务列表
    """
    db = next(get_db_gen())
    tasks = CrawlTaskDAO.get_recent(db, hours)
    return [
        CrawlTaskItem(
            id=t.id,
            platform=t.platform,
            query=t.query,
            status=t.status,
            created_at=t.started_at
        )
        for t in tasks
    ]


@app.post("/api/v1/seed", tags=["Admin"])
def seed_demo_data():
    """
    注入演示数据（用于测试）
    
    如果没有真实爬虫数据，调用此接口生成模拟数据填充数据库
    """
    from database import DailyMetricsDAO, PlatformSnapshotDAO
    import random
    
    with get_db() as db:
        platforms = ["deepseek", "chatgpt", "doubao", "wenxin", "kimi", "perplexity"]
        platform_names = ["DeepSeek", "ChatGPT", "豆包", "文心一言", "Kimi", "Perplexity"]
        
        # 生成近30天的数据
        for day_offset in range(30, -1, -1):
            date_str = (datetime.utcnow() - __import__('datetime').timedelta(days=day_offset)).strftime("%Y-%m-%d")
            
            for idx, platform in enumerate(platforms):
                base_visibility = [92, 78, 85, 71, 66, 58][idx]
                growth = (30 - day_offset) * 0.5  # 随时间增长
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
        
        # 生成快照
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
        
        return {"message": "Demo data seeded successfully", "days": 30, "platforms": platforms}


@app.get("/api/v1/dashboard/all", tags=["Dashboard"])
def get_dashboard_all():
    """
    获取看板所需的所有数据（一次性接口）
    
    用于前端看板初始加载时减少请求次数
    """
    db = next(get_db_gen())
    
    return {
        "kpis": DailyMetricsDAO.get_aggregate_kpis(db),
        "platforms": DailyMetricsDAO.get_latest_all(db),
        "snapshots": PlatformSnapshotDAO.get_all(db),
        "updated_at": datetime.utcnow().isoformat()
    }


# ==================== 启动入口 ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=API_CONFIG["host"],
        port=API_CONFIG["port"]
    )
