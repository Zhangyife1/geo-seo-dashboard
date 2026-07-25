"""
数据存储层 - SQLite 数据库模型与操作
使用 SQLAlchemy ORM 管理 GEO 数据
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from contextlib import contextmanager

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from config import DATABASE_URL, ensure_dirs

# 初始化目录
ensure_dirs()

# 日志
logger = logging.getLogger("geo.database")

# SQLAlchemy 基础
Base = declarative_base()
engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ==================== 数据模型 ====================

class CrawlTask(Base):
    """抓取任务记录"""
    __tablename__ = "crawl_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String(50), index=True, comment="AI平台标识")
    platform_name = Column(String(100), comment="平台显示名称")
    query = Column(Text, comment="查询关键词")
    status = Column(String(20), default="pending", comment="pending/running/success/failed")
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    raw_response = Column(Text, nullable=True, comment="原始AI响应文本")


class CitationRecord(Base):
    """品牌引用记录 - NLP分析后的结构化数据"""
    __tablename__ = "citation_records"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, index=True, comment="关联任务ID")
    platform = Column(String(50), index=True)
    query = Column(Text)
    
    # 品牌检测
    brand_mentioned = Column(Boolean, default=False, comment="是否提及品牌")
    brand_mention_count = Column(Integer, default=0, comment="提及次数")
    brand_context = Column(Text, nullable=True, comment="提及上下文片段")
    
    # 引用分析
    citation_rank = Column(Integer, nullable=True, comment="引用排名(在回答中的位置)")
    is_recommended = Column(Boolean, default=False, comment="是否被推荐")
    
    # 情感分析
    sentiment_score = Column(Float, default=0.0, comment="情感分数 -1~1")
    sentiment_label = Column(String(20), default="neutral", comment="positive/negative/neutral")
    positive_keywords = Column(Text, nullable=True)
    negative_keywords = Column(Text, nullable=True)
    
    # 内容质量
    content_length = Column(Integer, default=0)
    has_statistics = Column(Boolean, default=False)
    has_authority_signal = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class DailyMetrics(Base):
    """每日聚合指标 - 看板直接读取"""
    __tablename__ = "daily_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(String(10), index=True, comment="YYYY-MM-DD")
    platform = Column(String(50), index=True)
    
    # GEO 核心指标
    visibility_score = Column(Float, default=0.0, comment="可见性评分 0-100")
    citation_rate = Column(Float, default=0.0, comment="引用率 %")
    mention_count = Column(Integer, default=0, comment="提及次数")
    avg_sentiment = Column(Float, default=0.0, comment="平均情感分")
    referral_traffic = Column(Integer, default=0, comment="估算引荐流量")
    
    # 信度指标
    authority_score = Column(Float, default=0.0)
    freshness_score = Column(Float, default=0.0)
    
    # SEO 基础指标
    domain_authority = Column(Float, nullable=True)
    keyword_rank = Column(Float, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PlatformSnapshot(Base):
    """平台快照 - 最近一次各平台状态"""
    __tablename__ = "platform_snapshots"
    
    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String(50), unique=True, index=True)
    platform_name = Column(String(100))
    
    visibility_score = Column(Float, default=0.0)
    citation_count = Column(Integer, default=0)
    citation_rank = Column(Integer, nullable=True)
    sentiment_score = Column(Float, default=0.0)
    referral_traffic = Column(Integer, default=0)
    authority_level = Column(String(10), default="C")
    data_freshness = Column(String(20), default="unknown")
    status = Column(String(20), default="unknown")
    
    last_updated = Column(DateTime, default=datetime.utcnow)


# ==================== 数据库初始化 ====================

def init_db():
    """创建所有表"""
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized: %s", DATABASE_URL)


@contextmanager
def get_db():
    """数据库会话上下文管理器 - 用于 with 语句"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_gen():
    """数据库会话纯生成器 - 用于 next() 调用（FastAPI端点）"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ==================== CRUD 操作 ====================

class CrawlTaskDAO:
    """抓取任务数据访问对象"""
    
    @staticmethod
    def create(db: Session, platform: str, query: str) -> CrawlTask:
        task = CrawlTask(
            platform=platform,
            platform_name=platform,
            query=query,
            status="pending"
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        return task
    
    @staticmethod
    def update_status(db: Session, task_id: int, status: str, error: str = None, raw: str = None):
        task = db.query(CrawlTask).filter(CrawlTask.id == task_id).first()
        if task:
            task.status = status
            if status in ("success", "failed"):
                task.completed_at = datetime.utcnow()
            if error:
                task.error_message = error
            if raw:
                task.raw_response = raw
            db.commit()
    
    @staticmethod
    def get_recent(db: Session, hours: int = 24) -> List[CrawlTask]:
        since = datetime.utcnow() - timedelta(hours=hours)
        return db.query(CrawlTask).filter(CrawlTask.started_at >= since).order_by(CrawlTask.started_at.desc()).all()


class CitationRecordDAO:
    """引用记录数据访问对象"""
    
    @staticmethod
    def create(db: Session, data: Dict[str, Any]) -> CitationRecord:
        record = CitationRecord(**data)
        db.add(record)
        db.commit()
        db.refresh(record)
        return record
    
    @staticmethod
    def get_by_platform(db: Session, platform: str, days: int = 7) -> List[CitationRecord]:
        since = datetime.utcnow() - timedelta(days=days)
        return db.query(CitationRecord).filter(
            CitationRecord.platform == platform,
            CitationRecord.created_at >= since
        ).order_by(CitationRecord.created_at.desc()).all()
    
    @staticmethod
    def get_mentions_summary(db: Session, days: int = 30) -> List[Dict]:
        """获取各平台提及汇总"""
        since = datetime.utcnow() - timedelta(days=days)
        results = db.query(
            CitationRecord.platform,
            func.count(CitationRecord.id).label("total"),
            func.sum(CitationRecord.brand_mentioned.cast(Integer)).label("mentioned"),
            func.avg(CitationRecord.sentiment_score).label("avg_sentiment")
        ).filter(CitationRecord.created_at >= since).group_by(CitationRecord.platform).all()
        
        return [
            {
                "platform": r.platform,
                "total_queries": r.total,
                "mention_count": int(r.mentioned or 0),
                "avg_sentiment": round(float(r.avg_sentiment or 0), 3)
            }
            for r in results
        ]


class DailyMetricsDAO:
    """每日指标数据访问对象"""
    
    @staticmethod
    def upsert(db: Session, date: str, platform: str, metrics: Dict[str, Any]):
        """更新或插入每日指标"""
        existing = db.query(DailyMetrics).filter(
            DailyMetrics.date == date,
            DailyMetrics.platform == platform
        ).first()
        
        if existing:
            for key, value in metrics.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            existing.updated_at = datetime.utcnow()
        else:
            data = {"date": date, "platform": platform, **metrics}
            existing = DailyMetrics(**data)
            db.add(existing)
        
        db.commit()
    
    @staticmethod
    def get_trend(db: Session, platform: str, days: int = 30) -> List[Dict]:
        """获取趋势数据"""
        since = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
        results = db.query(DailyMetrics).filter(
            DailyMetrics.platform == platform,
            DailyMetrics.date >= since
        ).order_by(DailyMetrics.date.asc()).all()
        
        return [
            {
                "date": r.date,
                "visibility_score": r.visibility_score,
                "citation_rate": r.citation_rate,
                "mention_count": r.mention_count,
                "avg_sentiment": r.avg_sentiment,
                "referral_traffic": r.referral_traffic,
            }
            for r in results
        ]
    
    @staticmethod
    def get_latest_all(db: Session) -> List[Dict]:
        """获取所有平台最新指标"""
        subq = db.query(
            DailyMetrics.platform,
            func.max(DailyMetrics.date).label("max_date")
        ).group_by(DailyMetrics.platform).subquery()
        
        results = db.query(DailyMetrics).join(
            subq,
            (DailyMetrics.platform == subq.c.platform) & (DailyMetrics.date == subq.c.max_date)
        ).all()
        
        platform_name_map = {
            "deepseek": "DeepSeek", "chatgpt": "ChatGPT", "doubao": "豆包",
            "wenxin": "文心一言", "kimi": "Kimi", "perplexity": "Perplexity",
        }
        return [{
            "platform": r.platform,
            "platform_name": platform_name_map.get(r.platform, r.platform),
            "date": r.date,
            "visibility_score": r.visibility_score,
            "citation_rate": r.citation_rate,
            "mention_count": r.mention_count,
            "avg_sentiment": r.avg_sentiment,
            "referral_traffic": r.referral_traffic,
            "authority_score": r.authority_score,
            "freshness_score": r.freshness_score,
        } for r in results]
    
    @staticmethod
    def get_aggregate_kpis(db: Session) -> Dict[str, Any]:
        """获取聚合后的看板KPI"""
        today = datetime.utcnow().strftime("%Y-%m-%d")
        
        # 今日所有平台汇总
        today_records = db.query(DailyMetrics).filter(DailyMetrics.date == today).all()
        
        if not today_records:
            # 如果没有今日数据，取最新日期
            latest_date = db.query(func.max(DailyMetrics.date)).scalar()
            if latest_date:
                today_records = db.query(DailyMetrics).filter(DailyMetrics.date == latest_date).all()
        
        if not today_records:
            return {}
        
        total_mentions = sum(r.mention_count for r in today_records)
        avg_visibility = sum(r.visibility_score for r in today_records) / len(today_records)
        avg_citation = sum(r.citation_rate for r in today_records) / len(today_records)
        avg_sentiment = sum(r.avg_sentiment for r in today_records) / len(today_records)
        total_referral = sum(r.referral_traffic for r in today_records)
        
        return {
            "ai_visibility_index": round(avg_visibility, 1),
            "citation_rate": round(avg_citation, 1),
            "mention_count": total_mentions,
            "sentiment_score": round((avg_sentiment + 1) * 50, 1),  # 转换到 0-100
            "referral_traffic": total_referral,
            "structural_health": round(sum(r.authority_score for r in today_records) / len(today_records), 1),
            "record_date": today_records[0].date if today_records else today,
        }


class PlatformSnapshotDAO:
    """平台快照数据访问对象"""
    
    @staticmethod
    def upsert(db: Session, platform: str, data: Dict[str, Any]):
        snapshot = db.query(PlatformSnapshot).filter(PlatformSnapshot.platform == platform).first()
        if snapshot:
            for key, value in data.items():
                if hasattr(snapshot, key):
                    setattr(snapshot, key, value)
            snapshot.last_updated = datetime.utcnow()
        else:
            data["platform"] = platform
            data["last_updated"] = datetime.utcnow()
            snapshot = PlatformSnapshot(**data)
            db.add(snapshot)
        db.commit()
    
    @staticmethod
    def get_all(db: Session) -> List[Dict]:
        snapshots = db.query(PlatformSnapshot).order_by(PlatformSnapshot.visibility_score.desc()).all()
        return [{
            "platform": s.platform,
            "platform_name": s.platform_name,
            "visibility_score": s.visibility_score,
            "citation_count": s.citation_count,
            "citation_rank": s.citation_rank,
            "sentiment_score": s.sentiment_score,
            "referral_traffic": s.referral_traffic,
            "authority_level": s.authority_level,
            "data_freshness": s.data_freshness,
            "status": s.status,
            "last_updated": s.last_updated.isoformat() if s.last_updated else None,
        } for s in snapshots]


# ==================== 初始化入口 ====================

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully!")
    print(f"Tables: {Base.metadata.tables.keys()}")
