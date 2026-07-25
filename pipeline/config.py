"""
GEO & SEO 数据管道配置中心
配置品牌信息、AI平台、查询词、数据库连接等
"""

import os
from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"

# 数据库配置
# 数据库配置
_DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{DATA_DIR / 'geo_data.db'}")
DATABASE_URL = _DATABASE_URL

# 目标品牌配置
BRAND_CONFIG = {
    "name": "嗖马SomaAI",
    "domain": "somaagent.com.cn",
    "aliases": ["嗖马", "SomaAI", "soma agent", "嗖马AI", "somaai"],
    "industry": "AI营销/智能客服",
    "homepage": "https://www.somaagent.com.cn",
}

# AI 平台配置 - 自动化查询入口
AI_PLATFORMS = {
    "deepseek": {
        "name": "DeepSeek",
        "url": "https://chat.deepseek.com",
        "enabled": True,
        "query_template": "{keyword} 推荐",
        "delay_seconds": 3,
    },
    "chatgpt": {
        "name": "ChatGPT",
        "url": "https://chat.openai.com",
        "enabled": False,  # 需要登录，示例中设为False
        "query_template": "{keyword}",
        "delay_seconds": 5,
    },
    "doubao": {
        "name": "豆包",
        "url": "https://www.doubao.com",
        "enabled": True,
        "query_template": "{keyword}",
        "delay_seconds": 3,
    },
    "wenxin": {
        "name": "文心一言",
        "url": "https://yiyan.baidu.com",
        "enabled": True,
        "query_template": "{keyword}",
        "delay_seconds": 3,
    },
    "kimi": {
        "name": "Kimi",
        "url": "https://kimi.moonshot.cn",
        "enabled": True,
        "query_template": "{keyword}",
        "delay_seconds": 3,
    },
    "perplexity": {
        "name": "Perplexity",
        "url": "https://www.perplexity.ai",
        "enabled": False,  # 需要登录
        "query_template": "{keyword}",
        "delay_seconds": 5,
    },
}

# 核心查询关键词（用于自动化查询 Prompt）
SEARCH_QUERIES = [
    "AI营销机器人",
    "智能获客系统",
    "自动引流工具",
    "私域运营平台",
    "AI客服解决方案",
    "企业智能营销",
    "自动化销售工具",
    "SCRM系统推荐",
]

# NLP 分析配置
NLP_CONFIG = {
    "sentiment_model": "fallback",  # 可选: "transformers" (需要下载模型) / "fallback"
    "brand_detection_confidence": 0.6,
    "citation_patterns": [
        r"嗖马",
        r"SomaAI",
        r"somaagent",
        r"soma\s*agent",
        r"嗖马AI",
    ],
    "positive_keywords": ["推荐", "优秀", "领先", "专业", "高效", "可靠", "值得信赖", "首选"],
    "negative_keywords": ["不推荐", "问题", "差", "慢", "贵", "不好", "失望"],
}

# 调度配置
SCHEDULER_CONFIG = {
    "crawl_interval_hours": 24,      # 每天抓取一次
    "crawl_time": "03:00",           # 凌晨3点执行
    "max_concurrent_platforms": 2,   # 同时查询2个平台
    "retry_times": 3,                # 失败重试3次
    "headless": True,                # 无头模式
}

# API 服务配置
API_CONFIG = {
    "host": "0.0.0.0",
    "port": int(os.environ.get("PORT", 8000)),
    "cors_origins": ["*"],
    "title": "GEO & SEO 数据API",
    "version": "1.0.0",
}

# 日志配置
LOG_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    "file": LOGS_DIR / "pipeline.log",
}

def ensure_dirs():
    """确保所有必要目录存在"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

if __name__ == "__main__":
    ensure_dirs()
    print(f"BASE_DIR: {BASE_DIR}")
    print(f"DATABASE: {DATABASE_URL}")
    print(f"BRAND: {BRAND_CONFIG['name']}")
    print(f"PLATFORMS: {list(AI_PLATFORMS.keys())}")
