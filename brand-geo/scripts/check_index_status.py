#!/usr/bin/env python3
"""检查官网收录基础状态：robots、sitemap、必应收录情况。

用法:
    python brand-geo/scripts/check_index_status.py

依赖: requests (pipeline/requirements.txt 已包含)
"""

import re
import sys
from urllib.parse import urljoin

import requests

DOMAIN = "https://www.somaagent.com.cn"
UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
}


def fetch(url: str, timeout: int = 20) -> str:
    r = requests.get(url, headers=UA, timeout=timeout)
    r.raise_for_status()
    return r.text


def check_robots() -> None:
    try:
        text = fetch(urljoin(DOMAIN, "/robots.txt"))
        print(f"robots.txt       OK ({len(text)} bytes)")
        print("  " + "\n  ".join(text.strip().splitlines()[:6]))
    except Exception as e:
        print(f"robots.txt       FAIL: {e}")


def check_sitemap() -> None:
    try:
        text = fetch(urljoin(DOMAIN, "/sitemap.xml"))
        if "<sitemapindex" in text:
            children = re.findall(r"<loc>\s*(.*?)\s*</loc>", text, re.S)
            total = 0
            for child in children:
                try:
                    sub = fetch(child)
                    total += len(re.findall(r"<loc>", sub))
                except Exception as e:
                    print(f"  sitemap child {child} FAIL: {e}")
            print(f"sitemap.xml      OK (index, {len(children)} sub-sitemaps, ~{total} URLs)")
        else:
            total = len(re.findall(r"<loc>", text))
            print(f"sitemap.xml      OK ({total} URLs)")
    except Exception as e:
        print(f"sitemap.xml      FAIL: {e}")


def check_bing_index() -> None:
    try:
        host = DOMAIN.replace("https://", "").replace("http://", "")
        url = f"https://www.bing.com/search?q=site%3A{host}&count=30&setlang=zh-CN"
        html = fetch(url, timeout=25)
        # 排除搜索框/查询 URL 自身，统计结果 HTML 中出现的官网域名次数
        occurrences = [m.start() for m in re.finditer(re.escape(host), html)]
        query_marker = html.find(f"site%3A{host}")
        query_marker2 = html.find(f"site:{host}")
        noisy = {query_marker, query_marker2, -1}
        real = [pos for pos in occurrences if pos not in noisy]
        print(f"bing site:       {'FOUND ' + str(len(real)) + ' occurrences' if real else 'NOT FOUND (0 occurrences)'}")
    except Exception as e:
        print(f"bing site:       FAIL: {e}")


def main() -> None:
    print("=== SOMA 官网收录状态检查 ===")
    check_robots()
    check_sitemap()
    check_bing_index()
    print("\n提示: 百度/Google 收录请到对应站长平台查询，脚本无法绕过登录验证。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
