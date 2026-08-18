#!/usr/bin/env python3
"""百度普通收录-快速收录 API 主动推送。

用法:
    export BAIDU_PUSH_TOKEN=你的token
    python brand-geo/scripts/baidu_push.py https://www.somaagent.com.cn/geo/ai-marketing-robot/
    python brand-geo/scripts/baidu_push.py --file urls.txt
"""

import argparse
import json
import os
import sys

import requests

API = "https://www.baidu.com/linksubmit?token={token}"


def main() -> int:
    parser = argparse.ArgumentParser(description="百度主动推送 URL")
    parser.add_argument("urls", nargs="*", help="要推送的 URL")
    parser.add_argument("--file", help="每行一个 URL 的文件")
    args = parser.parse_args()

    token = os.environ.get("BAIDU_PUSH_TOKEN", "").strip()
    if not token:
        print("错误: 未设置 BAIDU_PUSH_TOKEN。请先在百度搜索资源平台-普通收录-快速收录-API提交获取 token。")
        return 1

    urls = list(args.urls)
    if args.file:
        with open(args.file, encoding="utf-8") as f:
            urls.extend(line.strip() for line in f if line.strip())

    if not urls:
        print("错误: 没有要推送的 URL")
        return 1

    r = requests.post(
        API.format(token=token),
        data="\n".join(urls),
        headers={"Content-Type": "text/plain"},
        timeout=30,
    )
    print(r.text)
    try:
        data = r.json()
        if data.get("success"):
            print(f"推送成功: {data.get('success')} 条")
            return 0
    except json.JSONDecodeError:
        pass
    return 1 if r.status_code != 200 else 0


if __name__ == "__main__":
    sys.exit(main())
