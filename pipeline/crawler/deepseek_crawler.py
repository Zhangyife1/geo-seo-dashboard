"""
DeepSeek 爬虫 - 自动化查询 DeepSeek Chat
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
            # 检查是否存在输入框
            input_selectors = [
                'textarea[placeholder*="发消息"]',
                'textarea[placeholder*="Message"]',
                'div[contenteditable="true"]',
                'textarea',
            ]
            for selector in input_selectors:
                if page.locator(selector).count() > 0:
                    logger.info("[DeepSeek] Input box found, ready to query")
                    return True
            
            # 可能需要点击"开始对话"
            start_btn = page.locator('text=开始对话').first
            if start_btn.count() > 0:
                start_btn.click()
                time.sleep(2)
                return True
            
            logger.warning("[DeepSeek] Input box not found, may need login")
            return False
        except Exception as e:
            logger.error("[DeepSeek] Login check error: %s", str(e))
            return False
    
    def send_query(self, query: str) -> bool:
        """发送查询到 DeepSeek"""
        try:
            page = self.browser.page
            
            # 尝试定位输入框
            input_selectors = [
                'textarea[placeholder*="发消息"]',
                'textarea[placeholder*="Message"]',
                'div[contenteditable="true"]',
                'textarea',
            ]
            
            input_box = None
            for selector in input_selectors:
                if page.locator(selector).count() > 0:
                    input_box = page.locator(selector).first
                    break
            
            if not input_box:
                logger.error("[DeepSeek] Cannot find input box")
                return False
            
            # 输入查询
            input_box.fill(query)
            time.sleep(0.5)
            
            # 发送 - 按 Enter
            page.keyboard.press("Enter")
            logger.info("[DeepSeek] Query sent: %s", query)
            
            # 等待回答生成 - 通过观察停止按钮消失
            time.sleep(8)
            return True
            
        except Exception as e:
            logger.error("[DeepSeek] Send query error: %s", str(e))
            return False
    
    def get_response_text(self) -> str:
        """获取 DeepSeek 的回答文本"""
        try:
            page = self.browser.page
            
            # DeepSeek 的回答通常在选择器 .ds-markdown 或 .markdown-body 中
            response_selectors = [
                '.ds-markdown',
                '.markdown-body',
                '[class*="message-content"]',
                '[class*="answer"]',
                '.chat-message:last-child .content',
            ]
            
            for selector in response_selectors:
                elements = page.locator(selector).all()
                if elements:
                    # 取最后一个（最新的回答）
                    text = elements[-1].inner_text()
                    if text and len(text) > 10:
                        logger.info("[DeepSeek] Got response, length: %d", len(text))
                        return text
            
            # 兜底：获取页面全部文本
            full_text = page.inner_text('body')
            logger.warning("[DeepSeek] Using fallback body text, length: %d", len(full_text))
            return full_text
            
        except Exception as e:
            logger.error("[DeepSeek] Get response error: %s", str(e))
            return ""
