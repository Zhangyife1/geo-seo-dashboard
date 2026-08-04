"""
ChatGPT 爬虫 - 自动化查询 OpenAI ChatGPT
注意: ChatGPT 需要登录，浏览器模式在 CI 中大概率失败
建议通过 API 模式采集 (配置 OPENAI_API_KEY)
"""
import logging
import time
from .base_crawler import BaseAICrawler

logger = logging.getLogger("geo.crawler.chatgpt")


class ChatGPTCrawler(BaseAICrawler):
    """ChatGPT 平台爬虫"""

    def __init__(self, browser_manager):
        super().__init__(browser_manager)
        self.platform = "chatgpt"
        self.platform_name = "ChatGPT"
        self.base_url = "https://chat.openai.com"

    def login(self) -> bool:
        """ChatGPT 需要登录，检查是否已登录"""
        try:
            page = self.browser.page
            time.sleep(3)

            # 检查是否存在登录提示
            login_indicators = [
                'text=Log in',
                'text=登录',
                'text=Sign up',
                'button:has-text("Log in")',
            ]
            for sel in login_indicators:
                try:
                    if page.locator(sel).count() > 0:
                        logger.warning("[ChatGPT] Login required, browser mode will likely fail in CI")
                        return False
                except Exception:
                    continue

            # 检查输入框
            input_selectors = [
                'textarea[placeholder*="Message"]',
                'textarea[placeholder*="Send a message"]',
                'textarea#prompt-textarea',
                'textarea',
            ]
            for sel in input_selectors:
                try:
                    if page.locator(sel).count() > 0:
                        logger.info("[ChatGPT] Input found: %s", sel)
                        return True
                except Exception:
                    continue

            logger.warning("[ChatGPT] No input found, may need login")
            return False
        except Exception as e:
            logger.error("[ChatGPT] Login check: %s", e)
            return False

    def send_query(self, query: str) -> bool:
        try:
            page = self.browser.page
            input_selectors = [
                'textarea[placeholder*="Message"]',
                'textarea[placeholder*="Send a message"]',
                'textarea#prompt-textarea',
                'textarea',
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
                logger.error("[ChatGPT] Input not found")
                return False

            input_box.click()
            time.sleep(0.3)
            input_box.fill(query)
            time.sleep(0.5)

            # 尝试发送
            send_selectors = [
                'button[data-testid="send-button"]',
                'button[aria-label*="Send"]',
                'button:has(svg):last-of-type',
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

            logger.info("[ChatGPT] Query sent: %s", query)
            return True
        except Exception as e:
            logger.error("[ChatGPT] Send query: %s", e)
            return False

    def get_response_text(self) -> str:
        try:
            page = self.browser.page
            selectors = [
                '[class*="markdown"]',
                '[class*="prose"]',
                '[data-testid*="conversation-turn"] [class*="markdown"]',
                '[class*="message-content"]',
                '[class*="response"]',
            ]
            for sel in selectors:
                try:
                    els = page.locator(sel).all()
                    if els:
                        text = els[-1].inner_text()
                        if text and len(text) > 10:
                            logger.info("[ChatGPT] Got response via %s, length: %d", sel, len(text))
                            return text
                except Exception:
                    continue
            return page.inner_text('body')
        except Exception as e:
            logger.error("[ChatGPT] Get response: %s", e)
            return ""
