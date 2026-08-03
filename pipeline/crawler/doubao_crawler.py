"""
豆包爬虫 - 自动化查询字节跳动豆包
增强版：多组选择器 + 发送按钮 + 智能等待
"""
import logging
import time
from .base_crawler import BaseAICrawler

logger = logging.getLogger("geo.crawler.doubao")


class DoubaoCrawler(BaseAICrawler):
    """豆包平台爬虫"""

    def __init__(self, browser_manager):
        super().__init__(browser_manager)
        self.platform = "doubao"
        self.platform_name = "豆包"
        self.base_url = "https://www.doubao.com/chat"

    def login(self) -> bool:
        """豆包支持免登录使用"""
        try:
            page = self.browser.page
            time.sleep(3)

            # 检查输入框（多组选择器）
            selectors = [
                'textarea[placeholder*="输入"]',
                'textarea[placeholder*="消息"]',
                'textarea[placeholder*="ask"]',
                'div[contenteditable="true"]',
                'textarea',
            ]
            for sel in selectors:
                try:
                    if page.locator(sel).count() > 0:
                        logger.info("[Doubao] Input found: %s", sel)
                        return True
                except Exception:
                    continue

            # 豆包通常可以直接使用
            logger.warning("[Doubao] No input found, trying anyway")
            return True
        except Exception as e:
            logger.error("[Doubao] Login check: %s", e)
            return True

    def send_query(self, query: str) -> bool:
        try:
            page = self.browser.page

            # 多组输入框选择器
            input_selectors = [
                'textarea[placeholder*="输入"]',
                'textarea[placeholder*="消息"]',
                'textarea[placeholder*="ask"]',
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
                logger.error("[Doubao] Input not found")
                return False

            input_box.click()
            time.sleep(0.3)
            input_box.fill(query)
            time.sleep(0.5)

            # 尝试点击发送按钮
            send_selectors = [
                'button[aria-label*="发送"]',
                'button[aria-label*="Send"]',
                'button:has(svg):last-of-type',
                '[class*="send"]',
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

            logger.info("[Doubao] Query sent: %s", query)
            return True
        except Exception as e:
            logger.error("[Doubao] Send query: %s", e)
            return False

    def get_response_text(self) -> str:
        try:
            page = self.browser.page
            # 多组回答选择器
            selectors = [
                '[class*="message-content"]',
                '[class*="answer-content"]',
                '[class*="markdown"]',
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
                            logger.info("[Doubao] Got response via %s, length: %d", sel, len(text))
                            return text
                except Exception:
                    continue
            return page.inner_text('body')
        except Exception as e:
            logger.error("[Doubao] Get response: %s", e)
            return ""
