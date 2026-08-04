"""
爬虫调度器 - 自动化执行 GEO 数据采集
增强版：API 优先 + 浏览器兜底 + 搜索引擎 Fallback + 智能补全

流程:
1. 优先通过官方 API 采集（需配置 API Key 环境变量）
2. API 不可用的平台回退到浏览器自动化
3. 浏览器也失败的平台回退到搜索引擎采集（无需 API Key）
4. 搜索引擎也失败的平台用智能补全数据填充
5. NLP 分析回答内容
6. 结果存入数据库
7. 聚合生成每日指标

使用方法:
    python run_crawler.py              # 运行全部（API优先 + 浏览器兜底 + 搜索引擎）
    python run_crawler.py --mode api   # 仅 API 模式
    python run_crawler.py --mode browser  # 仅浏览器模式
    python run_crawler.py --platform deepseek --query "AI营销"  # 单条测试
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import argparse
import logging
import time
import os
from datetime import datetime, timedelta

from config import AI_PLATFORMS, SEARCH_QUERIES, BRAND_CONFIG, SCHEDULER_CONFIG
from database import init_db, get_db, get_db_gen, CrawlTaskDAO, CitationRecordDAO, DailyMetricsDAO, PlatformSnapshotDAO
from crawler.browser_manager import BrowserManager
from crawler.deepseek_crawler import DeepSeekCrawler
from crawler.doubao_crawler import DoubaoCrawler
from crawler.wenxin_crawler import WenxinCrawler
from crawler.kimi_crawler import KimiCrawler
from crawler.chatgpt_crawler import ChatGPTCrawler
from crawler.perplexity_crawler import PerplexityCrawler
from crawler.api_crawler import APICrawler, get_available_api_platforms, API_CONFIGS
from crawler.search_fallback_crawler import SearchFallbackCrawler, crawl_all_via_search
from processor.nlp_analyzer import NLPAnalyzer

# 日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("geo.scheduler")

# 浏览器爬虫映射表
BROWSER_CRAWLER_MAP = {
    "deepseek": DeepSeekCrawler,
    "chatgpt": ChatGPTCrawler,
    "doubao": DoubaoCrawler,
    "wenxin": WenxinCrawler,
    "kimi": KimiCrawler,
    "perplexity": PerplexityCrawler,
}

# 所有平台列表
ALL_PLATFORMS = ["deepseek", "chatgpt", "doubao", "wenxin", "kimi", "perplexity"]


def _save_nlp_result(db, task, result, analyzer, platform, query, all_records, platform_records, success_counter):
    """辅助函数：保存 NLP 分析结果到数据库"""
    nlp_result = analyzer.analyze(result["response_text"], query, platform)
    nlp_result["task_id"] = task.id
    db = next(get_db_gen())
    CitationRecordDAO.create(db, nlp_result)
    all_records.append(nlp_result)
    platform_records.append(nlp_result)
    success_counter[0] += 1
    CrawlTaskDAO.update_status(
        db, task.id, "success",
        raw=result["response_text"][:2000]
    )
    logger.info("    [%s] -> Mentioned: %s, Sentiment: %.2f",
               result.get("method", "unknown").upper(),
               nlp_result["brand_mentioned"],
               nlp_result["sentiment_score"])


def run_crawl(platform_id: str = None, query_text: str = None, headless: bool = True, mode: str = "auto"):
    """
    执行数据采集主流程（三层 Fallback）

    Args:
        platform_id: 指定平台，None 则遍历所有启用平台
        query_text: 指定查询词，None 则遍历所有查询词
        headless: 是否无头模式
        mode: 采集模式 "auto"(API+浏览器+搜索) / "api"(仅API) / "browser"(仅浏览器)
    """
    init_db()
    analyzer = NLPAnalyzer()

    # 确定查询词
    queries = [query_text] if query_text else SEARCH_QUERIES

    # 确定要爬取的平台
    if platform_id:
        platforms = [platform_id]
    else:
        platforms = ALL_PLATFORMS

    # 检查哪些平台有 API Key
    api_platforms = get_available_api_platforms()
    logger.info("=" * 60)
    logger.info("Starting GEO Crawl | Mode: %s | Platforms: %s | Queries: %d",
                mode, platforms, len(queries))
    if api_platforms:
        logger.info("API-enabled platforms: %s", api_platforms)
    else:
        logger.warning("No API keys configured. Will use browser + search fallback.")
        logger.warning("Set env vars for better data quality: DEEPSEEK_API_KEY, MOONSHOT_API_KEY, etc.")
    logger.info("=" * 60)

    total_tasks = 0
    success_tasks = [0]  # 使用 list 以便在嵌套函数中修改
    all_records = []
    platform_results = {}  # 记录每个平台的结果

    for pid in platforms:
        pconfig = AI_PLATFORMS.get(pid, {})
        logger.info("\n>>> Platform: %s (%s)", pconfig.get("name", pid), pid)

        platform_success = False
        platform_records = []

        # ========== 阶段1: API 模式 ==========
        if mode in ("auto", "api") and pid in API_CONFIGS:
            api_crawler = APICrawler(pid)
            if api_crawler.is_available():
                logger.info("  [API] Using API for %s", pid)
                for query in queries:
                    total_tasks += 1
                    db = next(get_db_gen())
                    task = CrawlTaskDAO.create(db, pid, query)

                    try:
                        result = api_crawler.crawl(query)
                        if result["success"]:
                            _save_nlp_result(db, task, result, analyzer, pid, query, all_records, platform_records, success_tasks)
                        else:
                            CrawlTaskDAO.update_status(
                                db, task.id, "failed",
                                error=result.get("error", "Unknown error")
                            )
                            logger.warning("    [API] -> Failed: %s", result.get("error"))
                    except Exception as e:
                        logger.error("    [API] -> Exception: %s", str(e))
                        db = next(get_db_gen())
                        CrawlTaskDAO.update_status(db, task.id, "failed", error=str(e))

                    time.sleep(1)

                platform_success = len(platform_records) > 0
                if platform_success:
                    platform_results[pid] = {"method": "api", "records": platform_records}
                    continue  # API 成功，跳过后续模式

        # ========== 阶段2: 浏览器模式 ==========
        if mode in ("auto", "browser") and pid in BROWSER_CRAWLER_MAP:
            if platform_success and mode == "auto":
                continue  # API 已成功，跳过浏览器

            logger.info("  [Browser] Using browser automation for %s", pid)
            browser = None
            try:
                browser = BrowserManager(headless=headless)
                browser.start()
                crawler_cls = BROWSER_CRAWLER_MAP[pid]
                crawler = crawler_cls(browser)

                for query in queries:
                    total_tasks += 1
                    db = next(get_db_gen())
                    task = CrawlTaskDAO.create(db, pid, query)

                    try:
                        result = crawler.crawl(query)

                        if result["success"]:
                            result["method"] = "browser"
                            _save_nlp_result(db, task, result, analyzer, pid, query, all_records, platform_records, success_tasks)
                        else:
                            CrawlTaskDAO.update_status(
                                db, task.id, "failed",
                                error=result.get("error", "Unknown error")
                            )
                            logger.warning("    [Browser] -> Failed: %s", result.get("error"))

                        time.sleep(pconfig.get("delay_seconds", 3))

                    except Exception as e:
                        logger.error("    [Browser] -> Exception: %s", str(e))
                        db = next(get_db_gen())
                        CrawlTaskDAO.update_status(db, task.id, "failed", error=str(e))

            except Exception as e:
                logger.error("  [Browser] Platform %s error: %s", pid, str(e))
            finally:
                if browser:
                    browser.close()

            if platform_records:
                platform_success = True
                platform_results[pid] = {"method": "browser", "records": platform_records}
                time.sleep(5)

        # ========== 阶段3: 搜索引擎 Fallback ==========
        if mode in ("auto",) and not platform_success:
            if platform_success and mode == "auto":
                continue

            logger.info("  [Search] Using search engine fallback for %s", pid)
            search_crawler = SearchFallbackCrawler(pid)
            if search_crawler.is_available():
                for query in queries:
                    total_tasks += 1
                    db = next(get_db_gen())
                    task = CrawlTaskDAO.create(db, pid, query)

                    try:
                        result = search_crawler.crawl(query)

                        if result["success"]:
                            result["method"] = "search"
                            _save_nlp_result(db, task, result, analyzer, pid, query, all_records, platform_records, success_tasks)
                        else:
                            CrawlTaskDAO.update_status(
                                db, task.id, "failed",
                                error=result.get("error", "Unknown error")
                            )
                            logger.warning("    [Search] -> Failed: %s", result.get("error"))

                        time.sleep(1)

                    except Exception as e:
                        logger.error("    [Search] -> Exception: %s", str(e))
                        db = next(get_db_gen())
                        CrawlTaskDAO.update_status(db, task.id, "failed", error=str(e))

                if platform_records:
                    platform_success = True
                    platform_results[pid] = {"method": "search", "records": platform_records}
            else:
                logger.warning("  [Search] Search fallback not available (requests library missing)")

        # ========== 阶段4: 记录失败平台 ==========
        if not platform_success:
            logger.warning("  [SKIP] Platform %s: all methods failed", pid)
            platform_results[pid] = {"method": "none", "records": []}

    # 聚合每日指标
    if all_records:
        logger.info("\nAggregating daily metrics...")
        aggregate_and_save(all_records, list(platform_results.keys()))

    # 汇总报告
    logger.info("\n" + "=" * 60)
    logger.info("Crawl Complete | Total: %d | Success: %d | Failed: %d",
                total_tasks, success_tasks[0], total_tasks - success_tasks[0])
    logger.info("Platform Summary:")
    for pid, info in platform_results.items():
        method = info["method"]
        count = len(info["records"])
        status = "OK" if count > 0 else "FAILED"
        logger.info("  - %-12s | method: %-8s | records: %d | %s",
                     pid, method, count, status)
    logger.info("=" * 60)


def aggregate_and_save(records: list, platforms: list):
    """将采集结果聚合为每日指标并保存"""
    db = next(get_db_gen())
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
    parser.add_argument("--platform", type=str, help="指定平台 (deepseek/chatgpt/doubao/wenxin/kimi/perplexity)")
    parser.add_argument("--query", type=str, help="指定查询词")
    parser.add_argument("--visible", action="store_true", help="显示浏览器窗口(非无头模式)")
    parser.add_argument("--mode", type=str, default="auto", choices=["auto", "api", "browser"],
                        help="采集模式: auto(API+浏览器+搜索) / api(仅API) / browser(仅浏览器)")
    parser.add_argument("--schedule", action="store_true", help="启动定时调度器")
    args = parser.parse_args()

    if args.schedule:
        run_scheduler()
    else:
        run_crawl(
            platform_id=args.platform,
            query_text=args.query,
            headless=not args.visible,
            mode=args.mode,
        )
