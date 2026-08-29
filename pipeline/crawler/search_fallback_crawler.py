"""
搜索引擎 Fallback 爬虫（已停用）

历史版本会在 API / 浏览器采集失败时生成“模拟数据”，导致看板上出现虚假的量化结果。
按产品决策，自 2026-08-29 起：
- 不再生成任何模拟数据；
- 采集只认官方 API 与浏览器真实采集两种方式；
- 真实数据不足的平台，在导出阶段统一用“预留演示数据”补全看板。

本模块仅保留接口与 CI 环境检测函数，供旧代码兼容引用。
"""

import os


def _is_ci_environment() -> bool:
    """检测是否运行在 CI（GitHub Actions）环境。"""
    return (
        os.environ.get("CI", "").lower() in ("1", "true", "yes")
        or os.environ.get("GITHUB_ACTIONS", "").lower() == "true"
    )


class SearchFallbackCrawler:
    """占位类：搜索引擎/模拟兜底已停用，任何调用都返回失败。"""

    def __init__(self, platform: str):
        self.platform = platform
        self.platform_name = platform

    def is_available(self) -> bool:
        return False

    def crawl(self, query: str) -> dict:
        return {
            "platform": self.platform,
            "platform_name": self.platform_name,
            "query": query,
            "success": False,
            "method": "none",
            "error": "搜索/模拟兜底已停用：真实数据不足时由导出阶段使用预留演示数据补全",
        }


def crawl_all_via_search(queries: list, platforms: list = None) -> list:
    """占位函数：已停用，返回空列表。"""
    return []
