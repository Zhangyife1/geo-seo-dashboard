"""
搜索引擎 Fallback 爬虫
当 API 和浏览器自动化都失败时，通过免费搜索引擎采集数据
无需任何 API Key，适合 CI/CD 环境

原理：
1. 在搜索引擎中搜索 "{query} 推荐" 等关键词
2. 分析搜索结果中是否提及目标品牌
3. 提取排名、提及位置、情感倾向
4. 生成模拟的 AI 回答文本用于 NLP 分析

支持的搜索引擎：
- DuckDuckGo HTML (无需 API Key，免费)
- Bing (备用)
"""

import logging
import time
import random
import re
from typing import Dict, Any, List, Optional
from urllib.parse import quote

logger = logging.getLogger("geo.crawler.search")


try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    logger.warning("requests library not available, search fallback disabled")


class SearchFallbackCrawler:
    """
    搜索引擎 Fallback 爬虫
    无需 API Key，通过搜索引擎结果估算品牌 GEO 可见性
    """

    def __init__(self, platform: str):
        self.platform = platform
        self.platform_name = self._get_platform_name(platform)
        self.session = None
        if REQUESTS_AVAILABLE:
            self.session = requests.Session()
            self.session.headers.update({
                "User-Agent": self._get_random_ua(),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Accept-Encoding": "gzip, deflate",
                "DNT": "1",
                "Connection": "keep-alive",
            })

    def _get_platform_name(self, platform: str) -> str:
        names = {
            "deepseek": "DeepSeek",
            "chatgpt": "ChatGPT",
            "doubao": "豆包",
            "wenxin": "文心一言",
            "kimi": "Kimi",
            "perplexity": "Perplexity",
        }
        return names.get(platform, platform)

    def _get_random_ua(self) -> str:
        uas = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        ]
        return random.choice(uas)

    def is_available(self) -> bool:
        """检查是否可用"""
        return REQUESTS_AVAILABLE

    def crawl(self, query: str) -> Dict[str, Any]:
        """
        通过搜索引擎采集数据
        """
        result = {
            "success": False,
            "platform": self.platform,
            "platform_name": self.platform_name,
            "query": query,
            "response_text": "",
            "error": None,
            "attempts": 1,
            "method": "search_fallback",
        }

        if not self.is_available():
            result["error"] = "requests library not available"
            return result

        try:
            # 构建搜索查询
            search_queries = [
                f"{query} 推荐",
                f"{query} 哪家好",
                f"{query} 排名",
            ]

            all_results = []
            for sq in search_queries:
                try:
                    sr = self._search_duckduckgo(sq)
                    if sr:
                        all_results.extend(sr)
                    time.sleep(random.uniform(1, 2))
                except Exception as e:
                    logger.warning("[%s Search] Query '%s' failed: %s", self.platform, sq, str(e))
                    continue

            if not all_results:
                result["error"] = "No search results found"
                return result

            # 分析搜索结果，生成模拟的 AI 回答文本
            response_text = self._build_response_from_search(all_results, query)

            if response_text and len(response_text) > 50:
                result["success"] = True
                result["response_text"] = response_text
                logger.info(
                    "[%s Search] Success | query: '%s' | results: %d | response length: %d",
                    self.platform, query, len(all_results), len(response_text)
                )
            else:
                result["error"] = "Empty response from search results"

        except Exception as e:
            result["error"] = str(e)
            logger.error("[%s Search] Error for '%s': %s", self.platform, query, str(e))

        return result

    def _search_duckduckgo(self, query: str) -> List[Dict[str, str]]:
        """
        使用 DuckDuckGo HTML 搜索（无需 API Key）
        """
        url = f"https://html.duckduckgo.com/html/?q={quote(query)}"

        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            html = response.text

            results = []
            # 解析 DuckDuckGo HTML 结果
            # 结果项通常在 class="result" 的 div 中
            result_blocks = re.findall(
                r'<div class="result[^"]*"[^>]*>.*?<a[^>]*class="result__a"[^>]*href="([^"]*)"[^>]*>(.*?)</a>.*?<a[^>]*class="result__snippet"[^>]*>(.*?)</a>.*?</div>',
                html,
                re.DOTALL | re.IGNORECASE
            )

            if not result_blocks:
                # 尝试更宽松的匹配
                result_blocks = re.findall(
                    r'<a[^>]*href="([^"]*)"[^>]*class="result[^"]*"[^>]*>.*?<a[^>]*>(.*?)</a>.*?<a[^>]*class="result[^"]*"[^>]*>(.*?)</a>',
                    html,
                    re.DOTALL | re.IGNORECASE
                )

            for link, title, snippet in result_blocks[:10]:
                # 清理 HTML 标签
                title_clean = re.sub(r'<[^>]+>', '', title).strip()
                snippet_clean = re.sub(r'<[^>]+>', '', snippet).strip()
                if title_clean and snippet_clean:
                    results.append({
                        "title": title_clean,
                        "snippet": snippet_clean,
                        "link": link,
                    })

            # 如果上面没匹配到，尝试更简单的模式
            if not results:
                snippets = re.findall(
                    r'<a[^>]*class="result__snippet"[^>]*>(.*?)</a>',
                    html,
                    re.DOTALL | re.IGNORECASE
                )
                titles = re.findall(
                    r'<a[^>]*class="result__a"[^>]*>(.*?)</a>',
                    html,
                    re.DOTALL | re.IGNORECASE
                )
                for i, (title, snippet) in enumerate(zip(titles, snippets)):
                    title_clean = re.sub(r'<[^>]+>', '', title).strip()
                    snippet_clean = re.sub(r'<[^>]+>', '', snippet).strip()
                    if title_clean and snippet_clean:
                        results.append({
                            "title": title_clean,
                            "snippet": snippet_clean,
                            "link": "",
                        })

            logger.info("[%s Search] DuckDuckGo found %d results for '%s'",
                       self.platform, len(results), query)
            return results

        except Exception as e:
            logger.warning("[%s Search] DuckDuckGo error: %s", self.platform, str(e))
            return []

    def _build_response_from_search(self, results: List[Dict[str, str]], query: str) -> str:
        """
        将搜索结果转换为模拟的 AI 回答文本
        这样 NLP 分析器可以正常处理
        """
        # 品牌关键词
        brand_keywords = ["嗖马", "SomaAI", "somaagent", "soma agent", "嗖马AI"]
        positive_keywords = ["推荐", "优秀", "领先", "专业", "高效", "可靠", "首选", "值得信赖"]

        # 检查搜索结果中是否提及品牌
        brand_mentioned = False
        brand_contexts = []
        positive_found = []

        for i, r in enumerate(results):
            text = f"{r['title']} {r['snippet']}"
            text_lower = text.lower()

            for bk in brand_keywords:
                if bk.lower() in text_lower:
                    brand_mentioned = True
                    brand_contexts.append(f"结果{i+1}: {r['title']}\n{r['snippet']}")

            for pk in positive_keywords:
                if pk in text:
                    positive_found.append(pk)

        # 构建模拟的 AI 回答
        lines = [
            f"关于「{query}」的搜索结果分析：",
            "",
            f"通过搜索引擎分析，共获取 {len(results)} 条相关结果。",
            "",
        ]

        if brand_mentioned:
            lines.append("在搜索结果中发现品牌相关提及：")
            lines.append("")
            for ctx in brand_contexts[:3]:
                lines.append(ctx)
                lines.append("")
            lines.append("品牌在该关键词搜索中具有一定可见性。")
        else:
            lines.append("在搜索结果中未直接发现品牌提及。")
            lines.append("建议优化 SEO 和 GEO 策略以提升可见性。")

        lines.append("")
        lines.append("搜索结果摘要：")
        for i, r in enumerate(results[:5]):
            lines.append(f"{i+1}. {r['title']}")
            lines.append(f"   {r['snippet']}")
            lines.append("")

        if positive_found:
            lines.append(f"正面关键词出现: {', '.join(set(positive_found))}")

        return "\n".join(lines)


def crawl_all_via_search(queries: list, platforms: list = None) -> list:
    """
    批量通过搜索引擎采集所有平台数据
    """
    if platforms is None:
        platforms = ["deepseek", "chatgpt", "doubao", "wenxin", "kimi", "perplexity"]

    all_results = []
    for platform in platforms:
        crawler = SearchFallbackCrawler(platform)
        if not crawler.is_available():
            continue

        logger.info(">>> [%s Search] Starting fallback crawl with %d queries", platform, len(queries))

        for query in queries:
            result = crawler.crawl(query)
            all_results.append(result)
            time.sleep(random.uniform(1, 3))

        success_count = sum(1 for r in all_results if r["platform"] == platform and r["success"])
        logger.info(">>> [%s Search] Done | Success: %d / %d", platform, success_count, len(queries))

    return all_results
