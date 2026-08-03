"""
DeepSeek 爬虫 - 自动化查询 DeepSeek Chat
增强版：多组选择器 + 智能等待 + 发送按钮点击
"""

import logging
import time
from typing import Dict, Any

from .base_crawler import BaseAICrawler

logger = logging.getLogger("geo.crawler.deepseek")


class DeepSeekCrawler(BaseAICrawler):
    """DeepSeek 平台爬虫"""

    def __init__(self, browser_manager):
        super().__init__(browser_manager)
        self.platform = "deepseek"
        self.platform_name = "DeepSeek"
        self.base_url = "https://chat.deepseek.com"

    def login(self) -> bool:
        """DeepSeek 支持免登录使用一定次数，检查是否可用"""
        try:
            page = self.browser.page
            time.sleep(2)

            # 可能需要点击"开始对话"按钮
            start_selectors = [
                'text=开始对话',
                'text=Start Chat',
                'button:has-text("开始")',
                'a:has-text("开始对话")',
            ]
            for sel in start_selectors:
                try:
                    btn = page.locator(sel).first
                    if btn.count() > 0:
                        btn.click()
                        time.sleep(2)
                        break
                except Exception:
                    continue

            # 检查是否存在输入框（多组选择器）
            input_selectors = [
                'textarea#chat-input',
                'textarea[placeholder*="发消息"]',
                'textarea[placeholder*="Message"]',
                'textarea[placeholder*="输入"]',
                'textarea[placeholder*="chat"]',
                'div[contenteditable="true"]',
                'textarea',
            ]
            for selector in input_selectors:
                try:
                    if page.locator(selector).count() > 0:
                        logger.info("[DeepSeek] Input box found: %s", selector)
                        return True
                except Exception:
                    continue

            logger.warning("[DeepSeek] Input box not found, may need login")
            return False
        except Exception as e:
            logger.error("[DeepSeek] Login check error: %s", str(e))
            return False

    def send_query(self, query: str) -> bool:
        """发送查询到 DeepSeek"""
        try:
            page = self.browser.page

            # 尝试定位输入框（多组选择器）
            input_selectors = [
                'textarea#chat-input',
                'textarea[placeholder*="发消息"]',
                'textarea[placeholder*="Message"]',
                'textarea[placeholder*="输入"]',
                'div[contenteditable="true"]',
                'textarea',
            ]

            input_box = None
            for selector in input_selectors:
                try:
                    if page.locator(selector).count() > 0:
                        input_box = page.locator(selector).first
                        break
                except Exception:
                    continue

            if not input_box:
                logger.error("[DeepSeek] Cannot find input box")
                return False

            # 输入查询
            input_box.click()
            time.sleep(0.3)
            input_box.fill(query)
            time.sleep(0.5)

            # 尝试点击发送按钮，如果找不到则按 Enter
            send_selectors = [
                'button[aria-label="发送"]',
                'button[aria-label="Send"]',
                'div[role="button"][aria-label*="send"]',
                'button:has(svg)',  # 带 SVG 图标的按钮
            ]
            sent = False
            for sel in send_selectors:
                try:
                    btn = page.locator(sel).last
                    if btn.count() > 0 and btn.is_enabled():
                        btn.click()
                        sent = True
                        break
                except Exception:
                    continue

            if not sent:
                page.keyboard.press("Enter")

            logger.info("[DeepSeek] Query sent: %s", query)
            return True

        except Exception as e:
            logger.error("[DeepSeek] Send query error: %s", str(e))
            return False

    def get_response_text(self) -> str:
        """获取 DeepSeek 的回答文本"""
        try:
            page = self.browser.page

            # DeepSeek 的回答选择器（多组）
            response_selectors = [
                '.ds-markdown',
                '.markdown-body',
                '[class*="message-content"]',
                '[class*="answer"]',
                '[class*="response"]',
                '[class*="markdown"]',
                '.chat-message:last-child [class*="content"]',
                '[class*="assistant"] [class*="content"]',
            ]

            for selector in response_selectors:
                try:
                    elements = page.locator(selector).all()
                    if elements:
                        # 取最后一个（最新的回答）
                        text = elements[-1].inner_text()
                        if text and len(text) > 10:
                            logger.info("[DeepSeek] Got response via %s, length: %d", selector, len(text))
                            return text
                except Exception:
                    continue

            # 兜底：获取页面全部文本
            full_text = page.inner_text('body')
            logger.warning("[DeepSeek] Using fallback body text, length: %d", len(full_text))
            return full_text

        except Exception as e:
            logger.error("[DeepSeek] Get response error: %s", str(e))
            return ""
