"""
Perplexity 爬虫 - 自动化查询 Perplexity AI
注意: Perplexity 需要登录，浏览器模式在 CI 中大概率失败
建议通过 API 模式采集 (配置 PERPLEXITY_API_KEY)
"""
import logging
import time
from .base_crawler import BaseAICrawler

logger = logging.getLogger("geo.crawler.perplexity")


class PerplexityCrawler(BaseAICrawler):
    """Perplexity 平台爬虫"""

    def __init__(self, browser_manager):
        super().__init__(browser_manager)
        self.platform = "perplexity"
        self.platform_name = "Perplexity"
        self.base_url = "https://www.perplexity.ai"

    def login(self) -> bool:
        """Perplexity 支持免登录搜索一定次数"""
        try:
            page = self.browser.page
            time.sleep(3)

            # 检查是否存在登录提示
            login_indicators = [
                'text=Sign in',
                'text=Log in',
                'text=登录',
                'button:has-text("Sign in")',
            ]
            for sel in login_indicators:
                try:
                    if page.locator(sel).count() > 0:
                        logger.warning("[Perplexity] Login prompt detected, may still work without login")
                except Exception:
                    continue

            # 检查输入框
            input_selectors = [
                'textarea[placeholder*="Ask"]',
                'textarea[placeholder*="Search"]',
                'input[placeholder*="Ask"]',
                'input[placeholder*="Search"]',
                'textarea',
                'input[type="text"]',
            ]
            for sel in input_selectors:
                try:
                    if page.locator(sel).count() > 0:
                        logger.info("[Perplexity] Input found: %s", sel)
                        return True
                except Exception:
                    continue

            logger.warning("[Perplexity] No input found")
            return False
        except Exception as e:
            logger.error("[Perplexity] Login check: %s", e)
            return False

    def send_query(self, query: str) -> bool:
        try:
            page = self.browser.page
            input_selectors = [
                'textarea[placeholder*="Ask"]',
                'textarea[placeholder*="Search"]',
                'input[placeholder*="Ask"]',
                'input[placeholder*="Search"]',
                'textarea',
                'input[type="text"]',
            ]
            input_box = None
            for sel in input_selectors:
                try:
                    if page.locator(sel).count() > 0:
                        input_box = page.locator(sel).first
                        break
                except Exception:
                    continue

            if not input_box:
                logger.error("[Perplexity] Input not found")
                return False

            input_box.click()
            time.sleep(0.3)
            input_box.fill(query)
            time.sleep(0.5)

            # 尝试发送
            send_selectors = [
                'button[aria-label*="Submit"]',
                'button[aria-label*="Send"]',
                'button:has(svg):last-of-type',
                '[class*="submit"]',
            ]
            sent = False
            for sel in send_selectors:
                try:
                    btn = page.locator(sel).last
                    if btn.count() > 0:
                        btn.click()
                        sent = True
                        break
                except Exception:
                    continue

            if not sent:
                page.keyboard.press("Enter")

            logger.info("[Perplexity] Query sent: %s", query)
            return True
        except Exception as e:
            logger.error("[Perplexity] Send query: %s", e)
            return False

    def get_response_text(self) -> str:
        try:
            page = self.browser.page
            selectors = [
                '[class*="prose"]',
                '[class*="markdown"]',
                '[class*="answer"]',
                '[class*="response"]',
                '[class*="content"]',
            ]
            for sel in selectors:
                try:
                    els = page.locator(sel).all()
                    if els:
                        text = els[-1].inner_text()
                        if text and len(text) > 10:
                            logger.info("[Perplexity] Got response via %s, length: %d", sel, len(text))
                            return text
                except Exception:
                    continue
            return page.inner_text('body')
        except Exception as e:
            logger.error("[Perplexity] Get response: %s", e)
            return ""
