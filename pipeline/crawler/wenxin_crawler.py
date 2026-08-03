"""
文心一言爬虫 - 增强版
多组选择器 + 发送按钮 + 智能等待
"""
import logging, time
from .base_crawler import BaseAICrawler
logger = logging.getLogger("geo.crawler.wenxin")

class WenxinCrawler(BaseAICrawler):
    def __init__(self, browser_manager):
        super().__init__(browser_manager)
        self.platform = "wenxin"
        self.platform_name = "文心一言"
        self.base_url = "https://yiyan.baidu.com"

    def login(self) -> bool:
        try:
            page = self.browser.page
            time.sleep(3)
            # 多组输入框选择器
            selectors = [
                'textarea[placeholder*="输入"]',
                'textarea[placeholder*="问"]',
                'div[contenteditable="true"]',
                'textarea',
            ]
            for sel in selectors:
                try:
                    if page.locator(sel).count() > 0:
                        logger.info("[Wenxin] Input found: %s", sel)
                        return True
                except Exception:
                    continue
            logger.warning("[Wenxin] No input found, trying anyway")
            return True
        except Exception as e:
            logger.error("[Wenxin] %s", e)
            return True

    def send_query(self, query: str) -> bool:
        try:
            page = self.browser.page
            input_selectors = [
                'textarea[placeholder*="输入"]',
                'textarea[placeholder*="问"]',
                'div[contenteditable="true"]',
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
                logger.error("[Wenxin] Input not found")
                return False

            input_box.click()
            time.sleep(0.3)
            input_box.fill(query)
            time.sleep(0.5)

            # 尝试发送按钮
            send_selectors = [
                'button[aria-label*="发送"]',
                'button[aria-label*="Send"]',
                '[class*="send"]',
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

            logger.info("[Wenxin] Query sent: %s", query)
            return True
        except Exception as e:
            logger.error("[Wenxin] %s", e)
            return False

    def get_response_text(self) -> str:
        try:
            page = self.browser.page
            selectors = [
                '[class*="markdown"]',
                '[class*="answer"]',
                '[class*="message-content"]',
                '[class*="response"]',
                '[class*="assistant"]',
                '[class*="content"]:not([class*="input"])',
            ]
            for sel in selectors:
                try:
                    els = page.locator(sel).all()
                    if els:
                        text = els[-1].inner_text()
                        if text and len(text) > 10:
                            logger.info("[Wenxin] Got response via %s, length: %d", sel, len(text))
                            return text
                except Exception:
                    continue
            return page.inner_text('body')
        except Exception as e:
            logger.error("[Wenxin] %s", e)
            return ""
