"""
爬虫调度器 - 自动化执行 GEO 数据采集
流程:
1. 遍历所有启用的 AI 平台
2. 对每个平台执行所有查询词
3. NLP 分析回答内容
4. 结果存入数据库
5. 聚合生成每日指标

使用方法:
    python run_crawler.py              # 运行全部查询
    python run_crawler.py --platform deepseek --query "AI营销"  # 单条测试
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import argparse
import logging
import time
from datetime import datetime, timedelta

from config import AI_PLATFORMS, SEARCH_QUERIES, BRAND_CONFIG, SCHEDULER_CONFIG
from database import init_db, get_db, CrawlTaskDAO, CitationRecordDAO, DailyMetricsDAO, PlatformSnapshotDAO
from crawler.browser_manager import BrowserManager
from crawler.deepseek_crawler import DeepSeekCrawler
from crawler.doubao_crawler import DoubaoCrawler
from crawler.wenxin_crawler import WenxinCrawler
from crawler.kimi_crawler import KimiCrawler
from processor.nlp_analyzer import NLPAnalyzer

# 日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("geo.scheduler")

# 爬虫映射表
CRAWLER_MAP = {
    "deepseek": DeepSeekCrawler,
    "doubao": DoubaoCrawler,
    "wenxin": WenxinCrawler,
    "kimi": KimiCrawler,
}


def run_crawl(platform_id: str = None, query_text: str = None, headless: bool = True):
    """
    执行数据采集主流程
    
    Args:
        platform_id: 指定平台，None 则遍历所有启用平台
        query_text: 指定查询词，None 则遍历所有查询词
        headless: 是否无头模式
    """
    init_db()
    analyzer = NLPAnalyzer()
    
    # 确定要爬取的平台
    platforms = {platform_id: AI_PLATFORMS[platform_id]} if platform_id else {
        k: v for k, v in AI_PLATFORMS.items() if v.get("enabled", False)
    }
    
    if not platforms:
        logger.error("No platforms enabled for crawling")
        return
    
    # 确定查询词
    queries = [query_text] if query_text else SEARCH_QUERIES
    
    logger.info("=" * 60)
    logger.info("Starting GEO Crawl | Platforms: %s | Queries: %d", 
                list(platforms.keys()), len(queries))
    logger.info("=" * 60)
    
    total_tasks = 0
    success_tasks = 0
    all_records = []  # 收集所有记录用于聚合
    
    for pid, pconfig in platforms.items():
        logger.info("\n>>> Platform: %s (%s)", pconfig["name"], pid)
        
        if pid not in CRAWLER_MAP:
            logger.warning("Crawler not implemented for %s, skipping", pid)
            continue
        
        browser = None
        try:
            browser = BrowserManager(headless=headless)
            page = browser.start()
            crawler_cls = CRAWLER_MAP[pid]
            crawler = crawler_cls(browser)
            
            for query in queries:
                total_tasks += 1
                logger.info("  Query: %s", query)
                
                # 创建任务记录
                db = next(get_db())
                task = CrawlTaskDAO.create(db, pid, query)
                
                try:
                    # 执行抓取
                    result = crawler.crawl(query)
                    
                    if result["success"]:
                        # NLP 分析
                        nlp_result = analyzer.analyze(
                            result["response_text"], 
                            query, 
                            pid
                        )
                        nlp_result["task_id"] = task.id
                        
                        # 保存分析结果
                        db = next(get_db())
                        CitationRecordDAO.create(db, nlp_result)
                        
                        all_records.append(nlp_result)
                        success_tasks += 1
                        
                        CrawlTaskDAO.update_status(
                            db, task.id, "success", 
                            raw=result["response_text"][:2000]
                        )
                        logger.info("    -> Mentioned: %s, Sentiment: %.2f",
                                   nlp_result["brand_mentioned"], 
                                   nlp_result["sentiment_score"])
                    else:
                        CrawlTaskDAO.update_status(
                            db, task.id, "failed", 
                            error=result.get("error", "Unknown error")
                        )
                        logger.warning("    -> Failed: %s", result.get("error"))
                    
                    # 平台间延迟
                    time.sleep(pconfig.get("delay_seconds", 3))
                    
                except Exception as e:
                    logger.error("    -> Exception: %s", str(e))
                    db = next(get_db())
                    CrawlTaskDAO.update_status(db, task.id, "failed", error=str(e))
            
        except Exception as e:
            logger.error("Platform %s error: %s", pid, str(e))
        finally:
            if browser:
                browser.close()
        
        # 平台间延迟
        time.sleep(5)
    
    # 聚合每日指标
    if all_records:
        logger.info("\nAggregating daily metrics...")
        aggregate_and_save(all_records, list(platforms.keys()))
    
    logger.info("\n" + "=" * 60)
    logger.info("Crawl Complete | Total: %d | Success: %d | Failed: %d",
                total_tasks, success_tasks, total_tasks - success_tasks)
    logger.info("=" * 60)


def aggregate_and_save(records: list, platforms: list):
    """将采集结果聚合为每日指标并保存"""
    db = next(get_db())
    today = datetime.utcnow().strftime("%Y-%m-%d")
    analyzer = NLPAnalyzer()
    
    # 按平台分组聚合
    platform_records = {p: [] for p in platforms}
    for r in records:
        p = r.get("platform")
        if p in platform_records:
            platform_records[p].append(r)
    
    for platform, precords in platform_records.items():
        if not precords:
            continue
        
        metrics = analyzer.calculate_daily_metrics(precords)
        if metrics:
            DailyMetricsDAO.upsert(db, today, platform, metrics)
            logger.info("  [%s] Visibility: %.1f, Citations: %.1f%%",
                       platform, metrics["visibility_score"], metrics["citation_rate"])
            
            # 更新平台快照
            snapshot = {
                "platform_name": AI_PLATFORMS.get(platform, {}).get("name", platform),
                "visibility_score": metrics["visibility_score"],
                "citation_count": sum(1 for r in precords if r.get("brand_mentioned")),
                "sentiment_score": metrics["avg_sentiment"],
                "referral_traffic": metrics["referral_traffic"],
                "authority_level": "A" if metrics["authority_score"] > 70 else "B",
                "data_freshness": "实时",
                "status": "优秀" if metrics["visibility_score"] > 80 else "良好" if metrics["visibility_score"] > 60 else "待优化",
            }
            PlatformSnapshotDAO.upsert(db, platform, snapshot)


def run_scheduler():
    """定时调度器 - 每天执行一次"""
    import schedule
    
    crawl_time = SCHEDULER_CONFIG["crawl_time"]
    logger.info("Scheduler started. Daily crawl at %s", crawl_time)
    
    schedule.every().day.at(crawl_time).do(run_crawl)
    
    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GEO Data Crawler")
    parser.add_argument("--platform", type=str, help="指定平台 (deepseek/doubao/wenxin/kimi)")
    parser.add_argument("--query", type=str, help="指定查询词")
    parser.add_argument("--visible", action="store_true", help="显示浏览器窗口(非无头模式)")
    parser.add_argument("--schedule", action="store_true", help="启动定时调度器")
    args = parser.parse_args()
    
    if args.schedule:
        run_scheduler()
    else:
        run_crawl(
            platform_id=args.platform,
            query_text=args.query,
            headless=not args.visible
        )
