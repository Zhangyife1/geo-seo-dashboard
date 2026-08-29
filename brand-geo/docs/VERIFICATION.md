# 如何验证品牌开始被 AI 提及

## 1. 最直接：看 GEO 看板

1. 打开 https://geo-seo-dashboard.onrender.com/
2. 查看顶部横幅：目标是让“真实采集”平台数尽可能多；无真实采集的平台会显示为预留演示数据
3. 查看 `kpis_real.mention_count` / `citation_rate`：只要真实回答里出现“嗖马/SomaAI”，数值就会 > 0
4. 看每个平台的提及数和情感分，确认没有负面内容被引用

## 2. 手动触发一次爬虫

每次发布新内容并提交收录后，手动运行一次：

```bash
cd pipeline
python test_api_keys.py
```

或直接在 GitHub Actions 页面触发「Daily GEO Data Crawl」的 `Run workflow`。

## 3. 检查官网收录状态

```bash
cd geo-seo-dashboard
python brand-geo/scripts/check_index_status.py
```

输出示例：

```text
robots.txt        OK
sitemap.xml       OK (66 posts, 26 pages)
bing site:        FOUND 12 URLs from somaagent.com.cn
```

如果 `bing site:` 显示 0，说明内容还没被收录，继续等 1-2 周并重复提交。

## 4. 预期时间线

- 发布内容 + 提交收录后：3-7 天，搜索引擎开始收录
- 2-4 周：联网检索型模型（Kimi、Perplexity、ChatGPT 联网）开始引用官网
- 1-3 个月：训练数据型模型（DeepSeek、豆包、文心一言）对品牌的认知度逐步提升

## 5. 判断标准

| 指标 | 含义 | 目标 |
|------|------|------|
| `real_count` | 真实采集平台数 | 6/6 |
| `mention_count` | 真实回答中提到品牌次数 | > 0 且持续增长 |
| `citation_rate` | 提及品牌的回答占比 | 从 0% 逐步提升 |
| `sentiment_score` | 情感分 | ≥ 60（需同步处理负面投诉） |
