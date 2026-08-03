"""
爬虫基类 - 定义 AI 平台爬虫的标准接口
增强版：重试机制 + 截图诊断 + 智能等待
"""

import logging
import time
import os
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger("geo.crawler.base")

# 截图保存目录
SCREENSHOT_DIR = Path(__file__).parent.parent / "data" / "screenshots"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)


class BaseAICrawler(ABC):
    """AI 平台爬虫抽象基类（增强版）"""

    def __init__(self, browser_manager):
        self.browser = browser_manager
        self.platform = ""
        self.platform_name = ""
        self.base_url = ""
        self.max_retries = 3
        self.retry_delay = 5

    @abstractmethod
    def login(self) -> bool:
        """登录或绕过登录检查"""
        pass

    @abstractmethod
    def send_query(self, query: str) -> bool:
        """发送查询请求"""
        pass

    @abstractmethod
    def get_response_text(self) -> str:
        """获取 AI 回答的纯文本内容"""
        pass

    def crawl(self, query: str) -> Dict[str, Any]:
        """
        完整的抓取流程（带重试）
        返回: {
            "success": bool,
            "platform": str,
            "query": str,
            "response_text": str,
            "error": str (optional),
            "attempts": int
        }
        """
        result = {
            "success": False,
            "platform": self.platform,
            "platform_name": self.platform_name,
            "query": query,
            "response_text": "",
            "error": None,
            "attempts": 0,
        }

        for attempt in range(1, self.max_retries + 1):
            result["attempts"] = attempt
            logger.info(
                "[%s] Attempt %d/%d for query: '%s'",
                self.platform,
                attempt,
                self.max_retries,
                query,
            )

            try:
                # 1. 导航到平台
                if not self.browser.safe_goto(self.base_url):
                    result["error"] = f"Failed to navigate to {self.base_url}"
                    self._capture_screenshot(query, attempt, "nav_failed")
                    if attempt < self.max_retries:
                        time.sleep(self.retry_delay)
                    continue

                # 2. 等待页面加载
                time.sleep(3)

                # 3. 登录检查
                if not self.login():
                    result["error"] = "Login check failed"
                    self._capture_screenshot(query, attempt, "login_failed")
                    if attempt < self.max_retries:
                        time.sleep(self.retry_delay)
                    continue

                # 4. 发送查询
                if not self.send_query(query):
                    result["error"] = "Failed to send query"
                    self._capture_screenshot(query, attempt, "send_failed")
                    if attempt < self.max_retries:
                        time.sleep(self.retry_delay)
                    continue

                # 5. 智能等待 AI 回答生成
                if not self._wait_for_response():
                    result["error"] = "Response timeout"
                    self._capture_screenshot(query, attempt, "response_timeout")
                    if attempt < self.max_retries:
                        time.sleep(self.retry_delay)
                    continue

                # 6. 获取回答文本
                response_text = self.get_response_text()
                if not response_text or len(response_text) < 20:
                    result["error"] = f"Empty or too short response (len={len(response_text) if response_text else 0})"
                    self._capture_screenshot(query, attempt, "empty_response")
                    if attempt < self.max_retries:
                        time.sleep(self.retry_delay)
                    continue

                # 成功
                result["success"] = True
                result["response_text"] = response_text
                result["error"] = None
                logger.info(
                    "[%s] Success on attempt %d | response length: %d",
                    self.platform,
                    attempt,
                    len(response_text),
                )
                break

            except Exception as e:
                result["error"] = str(e)
                logger.error(
                    "[%s] Attempt %d error for '%s': %s",
                    self.platform,
                    attempt,
                    query,
                    str(e),
                )
                self._capture_screenshot(query, attempt, "exception")
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay)

        return result

    def _wait_for_response(self, max_wait: int = 30, check_interval: float = 1.5) -> bool:
        """
        智能等待 AI 回答生成
        通过检测页面变化（加载指示器消失/内容稳定）来判断回答是否完成
        """
        try:
            page = self.browser.page
            elapsed = 0

            # 常见的"正在生成"指示器选择器
            loading_selectors = [
                '[class*="loading"]',
                '[class*="typing"]',
                '[class*="generating"]',
                '[class*="spinner"]',
                'button[disabled]',
                '.stop-button',
                '[class*="stop"]',
            ]

            # 先等至少 5 秒让回答开始生成
            time.sleep(5)
            elapsed = 5

            # 轮询检测回答是否完成
            while elapsed < max_wait:
                is_loading = False
                for sel in loading_selectors:
                    try:
                        count = page.locator(sel).count()
                        if count > 0:
                            is_loading = True
                            break
                    except Exception:
                        continue

                if not is_loading:
                    # 没有加载指示器，再等 2 秒确认内容稳定
                    time.sleep(2)
                    elapsed += 2
                    logger.info(
                        "[%s] Response appears complete after %ds",
                        self.platform,
                        elapsed,
                    )
                    return True

                time.sleep(check_interval)
                elapsed += check_interval

            logger.warning("[%s] Response wait timeout after %ds", self.platform, max_wait)
            # 超时也尝试获取已有内容
            return True

        except Exception as e:
            logger.warning("[%s] Wait for response error: %s", self.platform, str(e))
            return True  # 出错也继续尝试获取

    def _capture_screenshot(self, query: str, attempt: int, reason: str):
        """失败时截图保存用于诊断"""
        try:
            safe_query = "".join(c if c.isalnum() else "_" for c in query[:30])
            filename = f"{self.platform}_{safe_query}_a{attempt}_{reason}.png"
            filepath = SCREENSHOT_DIR / filename
            self.browser.screenshot(str(filepath))
            logger.info("[%s] Screenshot saved: %s", self.platform, filename)

            # 同时保存页面 HTML 用于调试
            try:
                html_path = SCREENSHOT_DIR / f"{self.platform}_{safe_query}_a{attempt}.html"
                page = self.browser.page
                html_content = page.content()
                with open(html_path, "w", encoding="utf-8") as f:
                    f.write(html_content)
            except Exception:
                pass

        except Exception as e:
            logger.warning("[%s] Screenshot failed: %s", self.platform, str(e))
