"""
浏览器管理器 - 基于 Playwright 的自动化浏览器控制
负责统一管理浏览器实例、页面上下文、代理、反检测等
"""

import logging
import random
import time
from typing import Optional, Dict, Any
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import SCHEDULER_CONFIG

logger = logging.getLogger("geo.crawler.browser")


class BrowserManager:
    """浏览器生命周期管理器"""
    
    def __init__(self, headless: bool = None):
        self.headless = headless if headless is not None else SCHEDULER_CONFIG["headless"]
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
    def start(self, proxy: Dict[str, str] = None) -> Page:
        """启动浏览器并返回 Page 对象"""
        logger.info("Starting browser (headless=%s)...", self.headless)
        
        self.playwright = sync_playwright().start()
        
        # 浏览器启动参数
        launch_args = {
            "headless": self.headless,
            "args": [
                "--disable-blink-features=AutomationControlled",
                "--disable-web-security",
                "--disable-features=IsolateOrigins,site-per-process",
            ]
        }
        
        if proxy:
            launch_args["proxy"] = proxy
        
        self.browser = self.playwright.chromium.launch(**launch_args)
        
        # 创建上下文 - 模拟真实浏览器指纹
        self.context = self.browser.new_context(
            viewport={"width": 1440, "height": 900},
            user_agent=self._get_random_ua(),
            locale="zh-CN",
            timezone_id="Asia/Shanghai",
            extra_http_headers={
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            }
        )
        
        # 注入反检测脚本
        self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            window.chrome = { runtime: {} };
        """)
        
        self.page = self.context.new_page()
        self.page.set_default_timeout(30000)
        self.page.set_default_navigation_timeout(30000)
        
        logger.info("Browser started successfully")
        return self.page
    
    def close(self):
        """关闭浏览器"""
        logger.info("Closing browser...")
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        logger.info("Browser closed")
    
    def safe_goto(self, url: str, wait_until: str = "networkidle") -> bool:
        """安全导航到页面"""
        try:
            logger.info("Navigating to: %s", url)
            self.page.goto(url, wait_until=wait_until)
            time.sleep(random.uniform(1, 2))
            return True
        except Exception as e:
            logger.error("Failed to navigate to %s: %s", url, str(e))
            return False
    
    def safe_click(self, selector: str, timeout: int = 10000) -> bool:
        """安全点击元素"""
        try:
            self.page.wait_for_selector(selector, timeout=timeout)
            self.page.click(selector)
            time.sleep(random.uniform(0.5, 1.5))
            return True
        except Exception as e:
            logger.error("Failed to click %s: %s", selector, str(e))
            return False
    
    def safe_fill(self, selector: str, text: str) -> bool:
        """安全输入文本（模拟人类打字）"""
        try:
            self.page.wait_for_selector(selector, timeout=10000)
            self.page.fill(selector, "")
            for char in text:
                self.page.type(selector, char, delay=random.randint(30, 120))
            time.sleep(random.uniform(0.3, 0.8))
            return True
        except Exception as e:
            logger.error("Failed to fill %s: %s", selector, str(e))
            return False
    
    def wait_for_response_contains(self, url_pattern: str, timeout: int = 30000) -> Optional[Dict]:
        """等待包含特定 URL 模式的网络响应"""
        try:
            with self.page.expect_response(lambda resp: url_pattern in resp.url, timeout=timeout) as resp_info:
                return resp_info.value.json()
        except Exception as e:
            logger.error("Wait for response failed: %s", str(e))
            return None
    
    def screenshot(self, path: str):
        """截图保存"""
        try:
            self.page.screenshot(path=path, full_page=True)
            logger.info("Screenshot saved: %s", path)
        except Exception as e:
            logger.error("Screenshot failed: %s", str(e))
    
    @staticmethod
    def _get_random_ua() -> str:
        """获取随机 User-Agent"""
        uas = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0",
        ]
        return random.choice(uas)
    
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
