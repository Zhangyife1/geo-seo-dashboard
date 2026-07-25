"""
文心一言爬虫
"""
import logging, time
from .base_crawler import BaseAICrawler
logger = logging.getLogger("geo.crawler.wenxin")

class WenxinCrawler(BaseAICrawler):
    def __init__(self, browser_manager):
        super().__init__(browser_manager)
        self.platform = "wenxin"; self.platform_name = "文心一言"; self.base_url = "https://yiyan.baidu.com"
    def login(self) -> bool:
        try:
            time.sleep(2)
            return True
        except Exception as e:
            logger.error("[Wenxin] %s", e); return True
    def send_query(self, query: str) -> bool:
        try:
            p = self.browser.page
            for sel in ['textarea', '[placeholder*="输入"]', '[contenteditable="true"]']:
                if p.locator(sel).count() > 0:
                    p.locator(sel).first.fill(query); time.sleep(0.5)
                    p.keyboard.press("Enter"); time.sleep(8); return True
            return False
        except Exception as e:
            logger.error("[Wenxin] %s", e); return False
    def get_response_text(self) -> str:
        try:
            p = self.browser.page
            for sel in ['.markdown-body', '[class*="answer"]', '.message-content']:
                els = p.locator(sel).all()
                if els: return els[-1].inner_text()
            return p.inner_text('body')
        except Exception as e:
            logger.error("[Wenxin] %s", e); return ""
