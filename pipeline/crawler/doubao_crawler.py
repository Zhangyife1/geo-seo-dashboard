"""
豆包爬虫 - 自动化查询字节跳动豆包
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
        self.base_url = "https://www.doubao.com"
    
    def login(self) -> bool:
        """豆包支持免登录使用"""
        try:
            page = self.browser.page
            time.sleep(2)
            # 检查输入框
            selectors = ['textarea', '[placeholder*="输入"]']
            for sel in selectors:
                if page.locator(sel).count() > 0:
                    return True
            return True  # 豆包通常可以直接使用
        except Exception as e:
            logger.error("[Doubao] Login check: %s", e)
            return True
    
    def send_query(self, query: str) -> bool:
        try:
            page = self.browser.page
            # 豆包的输入框
            input_box = page.locator('textarea').first
            if input_box.count() == 0:
                input_box = page.locator('[contenteditable="true"]').first
            
            if input_box.count() == 0:
                logger.error("[Doubao] Input not found")
                return False
            
            input_box.fill(query)
            time.sleep(0.5)
            page.keyboard.press("Enter")
            time.sleep(8)
            return True
        except Exception as e:
            logger.error("[Doubao] Send query: %s", e)
            return False
    
    def get_response_text(self) -> str:
        try:
            page = self.browser.page
            selectors = ['.message-content', '.answer-content', '[class*="markdown"]']
            for sel in selectors:
                els = page.locator(sel).all()
                if els:
                    return els[-1].inner_text()
            return page.inner_text('body')
        except Exception as e:
            logger.error("[Doubao] Get response: %s", e)
            return ""
