"""
爬虫基类 - 定义 AI 平台爬虫的标准接口
"""

import logging
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

logger = logging.getLogger("geo.crawler.base")


class BaseAICrawler(ABC):
    """AI 平台爬虫抽象基类"""
    
    def __init__(self, browser_manager):
        self.browser = browser_manager
        self.platform = ""
        self.platform_name = ""
        self.base_url = ""
        
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
        完整的抓取流程
        返回: {
            "success": bool,
            "platform": str,
            "query": str,
            "response_text": str,
            "error": str (optional)
        }
        """
        result = {
            "success": False,
            "platform": self.platform,
            "platform_name": self.platform_name,
            "query": query,
            "response_text": "",
            "error": None
        }
        
        try:
            # 1. 导航到平台
            if not self.browser.safe_goto(self.base_url):
                result["error"] = f"Failed to navigate to {self.base_url}"
                return result
            
            # 2. 等待页面加载/登录检查
            time.sleep(2)
            if not self.login():
                result["error"] = "Login check failed"
                return result
            
            # 3. 发送查询
            if not self.send_query(query):
                result["error"] = "Failed to send query"
                return result
            
            # 4. 等待 AI 回答生成
            time.sleep(5)
            
            # 5. 获取回答文本
            response_text = self.get_response_text()
            if not response_text:
                result["error"] = "Empty response"
                return result
            
            result["success"] = True
            result["response_text"] = response_text
            logger.info("[%s] Crawled query: '%s' -> response length: %d", 
                       self.platform, query, len(response_text))
            
        except Exception as e:
            result["error"] = str(e)
            logger.error("[%s] Crawl error for '%s': %s", self.platform, query, str(e))
        
        return result
