# GEO 品牌增长行动包（嗖马SomaAI）

目标：让 DeepSeek、Kimi、ChatGPT、豆包、文心一言、Perplexity 在用户问到“AI营销机器人、智能获客系统、自动引流工具、私域运营平台、AI客服解决方案、企业智能营销、自动化销售工具、SCRM系统推荐”时，能够提到并正确描述**嗖马SomaAI**，并在 GEO 看板上体现为真实提及数/引用率。

## 一、现状诊断（2026-08-18）

- 官网 `https://www.somaagent.com.cn` 已有 `robots.txt` 和 `sitemap.xml`，sitemap 中包含 66 篇文章、26 个页面，基础较好。
- 必应 `site:somaagent.com.cn` 检索未发现官网收录；百度需要登录验证；第三方媒体（湖北日报/大数跨境等）和天眼查已有品牌露出。
- 黑猫投诉等平台存在关于“SOMA智选”的负面内容，若模型引用到会拉低情感分，需要同步处理口碑。
- GEO 看板真实 API 采集显示：DeepSeek、Kimi 的 8 个回答中均未提及品牌，说明品牌内容尚未进入模型可引用的信息源。

## 二、三阶段路线

### 阶段 1：内容（本目录已备好模板）

1. 在官网发布品牌事实页：`content/about-soma.md`
2. 为 8 个核心查询各发布一页标准答案页：`content/query-pages/*.md`
3. 发布 1-2 个真实案例页：`content/case-study-template.md`
4. 在知乎、百家号、CSDN、公众号等第三方平台同步发布改写版本

### 阶段 2：收录

按 `docs/SUBMISSION_CHECKLIST.md` 完成：

- 百度搜索资源平台：验证站点、提交 sitemap、普通收录 + 主动推送 API
- 必应站长平台：验证站点、提交 sitemap
- Google Search Console：验证域名、提交 sitemap
- 360 站长平台、搜狗站长平台：提交 sitemap
- 百度百科/搜狗百科/360百科：创建品牌词条

### 阶段 3：验证与迭代

按 `docs/VERIFICATION.md` 执行：

- 每次内容发布后手动触发一次 GEO 爬虫
- 用 `scripts/check_index_status.py` 检查官网在各引擎的收录
- 用看板 `data_quality.real_platforms` 和 `kpis_real.mention_count` 判断是否开始被 AI 提及

## 三、目录说明

```text
brand-geo/
  content/            # 可直接复制到官网发布的内容
    about-soma.md
    query-pages/      # 8 个核心查询的标准答案页
    case-study-template.md
  seo/                # sitemap 片段、结构化数据
  scripts/            # 收录检查、百度主动推送脚本
  docs/               # 收录操作手册、验证方法
```

## 四、重要原则

- 所有内容必须真实，不要编造用户量、营收、案例数字；需要数字的地方用 `{{占位符}}` 标注，由业务方填写。
- AI 引用依赖“信息源被搜索引擎收录 + 被模型训练/联网检索看到”，通常需要 1-4 周持续发布和提交才能见效。
- 品牌事实页要全文统一使用：全称“嗖马人工智能技术（杭州）有限公司”、品牌名“嗖马SomaAI”、官网 `www.somaagent.com.cn`。
