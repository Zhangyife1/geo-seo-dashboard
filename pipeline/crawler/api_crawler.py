"""
API 爬虫 - 通过官方 API 采集 AI 平台回答
比浏览器自动化更可靠，不受反爬/登录墙影响

支持的 API:
- DeepSeek API (OpenAI 兼容)
- Moonshot/Kimi API (OpenAI 兼容)
- 百度千帆 API (文心一言)
- 火山引擎 API (豆包)
- OpenAI API (ChatGPT)
- 通用 OpenAI 兼容接口 (Perplexity 等)

API Key 通过环境变量配置:
- DEEPSEEK_API_KEY
- MOONSHOT_API_KEY
- QIANFAN_API_KEY + QIANFAN_SECRET_KEY
- VOLC_API_KEY
- OPENAI_API_KEY
- PERPLEXITY_API_KEY

使用方法:
    from crawler.api_crawler import APICrawler
    crawler = APICrawler("deepseek")
    result = crawler.crawl("AI营销工具推荐")
"""

import logging
import os
import time
import json
from typing import Dict, Any, Optional

logger = logging.getLogger("geo.crawler.api")

# 各平台 API 配置
API_CONFIGS = {
    "deepseek": {
        "base_url": "https://api.deepseek.com/v1",
        "model": "deepseek-chat",
        "api_key_env": "DEEPSEEK_API_KEY",
        "platform_name": "DeepSeek",
    },
    "kimi": {
        "base_url": "https://api.moonshot.cn/v1",
        # 不同账号/套餐可用模型不同，依次尝试；可用 KIMI_MODEL 指定首选
        # 实测当前账号 kimi-k2.6 可用，kimi-k3 返回 404
        "model": os.environ.get("KIMI_MODEL", "kimi-k2.6"),
        "fallback_models": [
            "kimi-k3",
            "kimi-k2.5",
            "moonshot-v1-32k",
            "moonshot-v1-128k",
            "moonshot-v1-8k",
        ],
        # kimi-k3 仅允许 temperature=1
        "temperature": 1.0,
        "api_key_env": "MOONSHOT_API_KEY",
        "platform_name": "Kimi",
    },
    "chatgpt": {
        "base_url": os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        "model": "gpt-4o-mini",
        "api_key_env": "OPENAI_API_KEY",
        "platform_name": "ChatGPT",
    },
    "perplexity": {
        "base_url": "https://api.perplexity.ai",
        "model": "llama-3.1-sonar-small-128k-online",
        "api_key_env": "PERPLEXITY_API_KEY",
        "platform_name": "Perplexity",
    },
    "doubao": {
        "base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "model": os.environ.get("DOUBAO_MODEL", "doubao-pro-32k"),
        "api_key_env": "VOLC_API_KEY",
        "platform_name": "豆包",
    },
    "wenxin": {
        "base_url": "https://qianfan.baidubce.com/v2",
        "model": "ernie-speed-128k",
        "api_key_env": "QIANFAN_API_KEY",
        "api_secret_env": "QIANFAN_SECRET_KEY",
        "platform_name": "文心一言",
    },
}


class APICrawler:
    """基于官方 API 的 AI 平台爬虫"""

    def __init__(self, platform: str):
        self.platform = platform
        self.config = API_CONFIGS.get(platform)
        if not self.config:
            raise ValueError(f"Platform '{platform}' not supported in API crawler")

        self.platform_name = self.config["platform_name"]
        self.api_key = os.environ.get(self.config["api_key_env"], "")
        self.base_url = self.config["base_url"]
        self.model = self.config["model"]

    def is_available(self) -> bool:
        """检查 API Key 是否已配置"""
        return bool(self.api_key)

    def crawl(self, query: str) -> Dict[str, Any]:
        """
        通过 API 发送查询并获取回答
        """
        result = {
            "success": False,
            "platform": self.platform,
            "platform_name": self.platform_name,
            "query": query,
            "response_text": "",
            "error": None,
            "attempts": 1,
            "method": "api",
        }

        if not self.is_available():
            result["error"] = f"API key not configured: {self.config['api_key_env']}"
            logger.warning("[%s] %s", self.platform, result["error"])
            return result

        try:
            # 构建 Prompt - 模拟用户在 AI 平台上的自然查询
            prompt = self._build_prompt(query)

            # 调用 API（模型不可用时按 fallback_models 依次尝试）
            models = [self.model] + list(self.config.get("fallback_models", []))
            response_text = ""
            last_error = None
            for model in models:
                try:
                    logger.info("[%s API] Trying model %s", self.platform, model)
                    candidate = self._call_api(prompt, model=model)
                    if candidate and len(candidate) > 10:
                        response_text = candidate
                        break
                except Exception as e:
                    last_error = e
                    err_text = str(e)
                    # 仅当模型不存在/无权限时继续尝试下一个模型
                    if "404" not in err_text and "Not found" not in err_text and "Permission denied" not in err_text:
                        break

            if response_text:
                result["success"] = True
                result["response_text"] = response_text
                logger.info(
                    "[%s API] Success | query: '%s' | response length: %d",
                    self.platform,
                    query,
                    len(response_text),
                )
            elif last_error is not None:
                result["error"] = str(last_error)
                logger.error("[%s API] Error for '%s': %s", self.platform, query, last_error)
            else:
                result["error"] = "Empty API response"

        except Exception as e:
            result["error"] = str(e)
            logger.error("[%s API] Error for '%s': %s", self.platform, query, str(e))

        return result

    def _build_prompt(self, query: str) -> str:
        """构建查询 Prompt"""
        return query

    def _call_api(self, prompt: str, model: str = None) -> str:
        """调用 OpenAI 兼容 API"""
        try:
            import requests
        except ImportError:
            raise RuntimeError("requests library required for API crawler")

        model = model or self.model
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": self.config.get("temperature", 0.7),
            "max_tokens": 2000,
        }

        url = f"{self.base_url}/chat/completions"

        # 重试逻辑
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=60,
                )

                if response.status_code == 429:
                    # 速率限制，等待后重试
                    wait = min(10 * (attempt + 1), 30)
                    logger.warning(
                        "[%s API] Rate limited, waiting %ds before retry %d/%d",
                        self.platform,
                        wait,
                        attempt + 1,
                        max_retries,
                    )
                    time.sleep(wait)
                    continue

                if response.status_code != 200:
                    logger.error(
                        "[%s API] HTTP %d: %s",
                        self.platform,
                        response.status_code,
                        response.text[:500],
                    )
                    # 配置类错误（模型名/Key/参数）重试也不会成功，直接抛出
                    if response.status_code in (400, 401, 403, 404, 422):
                        raise RuntimeError(f"API returned HTTP {response.status_code}: {response.text[:200]}")
                    if attempt < max_retries - 1:
                        time.sleep(3)
                        continue
                    raise RuntimeError(f"API returned HTTP {response.status_code}: {response.text[:200]}")

                data = response.json()

                # 解析 OpenAI 兼容响应格式
                if "choices" in data and len(data["choices"]) > 0:
                    return data["choices"][0]["message"]["content"]
                else:
                    logger.error("[%s API] Unexpected response: %s", self.platform, str(data)[:500])
                    raise RuntimeError(f"Unexpected API response format")

            except requests.exceptions.Timeout:
                logger.warning("[%s API] Timeout on attempt %d/%d", self.platform, attempt + 1, max_retries)
                if attempt < max_retries - 1:
                    time.sleep(5)
                    continue
                raise
            except requests.exceptions.ConnectionError as e:
                logger.warning("[%s API] Connection error: %s", self.platform, str(e))
                if attempt < max_retries - 1:
                    time.sleep(5)
                    continue
                raise

        raise RuntimeError(f"API call failed after {max_retries} retries")


def get_available_api_platforms() -> list:
    """获取所有已配置 API Key 的平台列表"""
    available = []
    for platform, config in API_CONFIGS.items():
        api_key = os.environ.get(config["api_key_env"], "")
        if api_key:
            available.append(platform)
    return available


def crawl_all_via_api(queries: list, platforms: list = None) -> list:
    """
    批量通过 API 采集所有平台数据
    返回所有成功采集的记录
    """
    if platforms is None:
        platforms = get_available_api_platforms()

    if not platforms:
        logger.warning("No API platforms available (no API keys configured)")
        return []

    all_results = []
    for platform in platforms:
        if platform not in API_CONFIGS:
            logger.warning("Platform '%s' not supported, skipping", platform)
            continue

        crawler = APICrawler(platform)
        if not crawler.is_available():
            logger.info("[%s] API key not configured, skipping", platform)
            continue

        logger.info(">>> [%s API] Starting crawl with %d queries", platform, len(queries))

        for query in queries:
            result = crawler.crawl(query)
            all_results.append(result)
            time.sleep(1)  # API 间延迟

        logger.info(
            ">>> [%s API] Done | Success: %d / %d",
            platform,
            sum(1 for r in all_results if r["platform"] == platform and r["success"]),
            len(queries),
        )

    return all_results
