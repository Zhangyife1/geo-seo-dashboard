"""
API Key 连通性测试脚本
本地运行: cd pipeline && python test_api_keys.py

功能:
1. 检查哪些 API Key 环境变量已配置
2. 对每个已配置的平台发送测试请求
3. 验证 API 返回是否正常
4. 检查 NLP 分析器能否从真实回答中检测品牌

用法:
    # 测试所有已配置的平台
    python test_api_keys.py

    # 测试特定平台
    python test_api_keys.py --platform deepseek

    # 使用 .env 文件加载密钥
    python test_api_keys.py --env .env
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import os
import argparse
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("geo.test")

# 加载 .env 文件
def load_env_file(env_path: str):
    """从 .env 文件加载环境变量"""
    p = Path(env_path)
    if not p.exists():
        return
    with open(p, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and value:
                    os.environ.setdefault(key, value)
                    logger.info("  Loaded %s from %s", key, env_path)


def test_single_platform(platform: str) -> dict:
    """测试单个平台的 API 连通性"""
    from crawler.api_crawler import APICrawler, API_CONFIGS

    config = API_CONFIGS.get(platform)
    if not config:
        return {"platform": platform, "status": "error", "message": f"Unknown platform: {platform}"}

    key_env = config["api_key_env"]
    api_key = os.environ.get(key_env, "")

    print(f"\n{'='*50}")
    print(f"Platform: {platform} ({config['platform_name']})")
    print(f"  API Key env: {key_env}")
    print(f"  API Key set: {'YES' if api_key else 'NO'}")
    print(f"  Base URL: {config['base_url']}")
    print(f"  Model: {config['model']}")

    if not api_key:
        print(f"  Status: SKIP (no API key)")
        return {"platform": platform, "status": "skip", "message": "No API key configured"}

    # 创建 crawler 并测试
    crawler = APICrawler(platform)
    if not crawler.is_available():
        print(f"  Status: FAIL (is_available() returned False)")
        return {"platform": platform, "status": "fail", "message": "is_available() returned False"}

    # 发送测试查询
    test_query = "AI营销工具推荐"
    print(f"  Test query: '{test_query}'")
    print(f"  Calling API...")

    result = crawler.crawl(test_query)

    if result["success"]:
        response_text = result["response_text"]
        print(f"  Response length: {len(response_text)} chars")
        print(f"  Response preview: {response_text[:200]}...")

        # 检查 NLP 分析
        from processor.nlp_analyzer import NLPAnalyzer
        analyzer = NLPAnalyzer()
        nlp_result = analyzer.analyze(response_text, test_query, platform)

        print(f"  NLP Analysis:")
        print(f"    brand_mentioned: {nlp_result['brand_mentioned']}")
        print(f"    brand_mention_count: {nlp_result['brand_mention_count']}")
        print(f"    sentiment_score: {nlp_result['sentiment_score']:.2f}")
        print(f"    sentiment_label: {nlp_result['sentiment_label']}")
        print(f"    data_source: api")
        print(f"  Status: SUCCESS")

        return {
            "platform": platform,
            "status": "success",
            "response_length": len(response_text),
            "brand_mentioned": nlp_result["brand_mentioned"],
            "sentiment": nlp_result["sentiment_score"],
        }
    else:
        print(f"  Error: {result.get('error', 'Unknown')}")
        print(f"  Status: FAIL")
        return {"platform": platform, "status": "fail", "message": result.get("error", "Unknown")}


def main():
    parser = argparse.ArgumentParser(description="Test API key connectivity")
    parser.add_argument("--platform", type=str, help="Test specific platform only")
    parser.add_argument("--env", type=str, default=".env", help="Path to .env file")
    args = parser.parse_args()

    # 加载 .env
    if args.env:
        load_env_file(args.env)

    # 确定要测试的平台
    from crawler.api_crawler import API_CONFIGS

    if args.platform:
        platforms = [args.platform]
    else:
        platforms = list(API_CONFIGS.keys())

    print("\n" + "=" * 50)
    print("GEO Dashboard API Key Connectivity Test")
    print("=" * 50)

    # 检查环境变量
    print("\n--- Environment Variable Check ---")
    all_keys = [c["api_key_env"] for c in API_CONFIGS.values()]
    if "QIANFAN_SECRET_KEY" in [c.get("api_secret_env", "") for c in API_CONFIGS.values()]:
        all_keys.append("QIANFAN_SECRET_KEY")

    configured = []
    for key in all_keys:
        val = os.environ.get(key, "")
        if val:
            configured.append(key)
            print(f"  {key}: SET (length={len(val)})")
        else:
            print(f"  {key}: NOT SET")

    if not configured:
        print("\n  No API keys found!")
        print("  Options:")
        print("    1. Create a .env file in pipeline/ directory with your keys")
        print("    2. Set environment variables: export DEEPSEEK_API_KEY=your_key")
        print("    3. For GitHub Actions: add keys in Settings -> Secrets -> Actions")
        print("\n  Example .env file content:")
        print("    DEEPSEEK_API_KEY=sk-your-key-here")
        print("    MOONSHOT_API_KEY=sk-your-key-here")
        return

    print(f"\n  {len(configured)} key(s) configured: {configured}")

    # 测试每个平台
    print("\n--- Platform API Test ---")
    results = []
    for platform in platforms:
        result = test_single_platform(platform)
        results.append(result)

    # 汇总
    print("\n" + "=" * 50)
    print("Summary")
    print("=" * 50)
    for r in results:
        status_icon = {"success": "[OK]", "fail": "[FAIL]", "skip": "[SKIP]", "error": "[ERR]"}.get(r["status"], "[?]")
        msg = r.get("message", "")
        brand = f" | brand_mentioned={r['brand_mentioned']}" if "brand_mentioned" in r else ""
        print(f"  {status_icon} {r['platform']:12s}{brand} {msg}")

    success_count = sum(1 for r in results if r["status"] == "success")
    print(f"\n  {success_count}/{len(results)} platforms working")


if __name__ == "__main__":
    main()
