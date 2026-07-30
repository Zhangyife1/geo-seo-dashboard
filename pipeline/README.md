# GEO & SEO 量化数据管道

## 项目概述

本项目是一套完整的 **GEO (Generative Engine Optimization) 数据监测与量化系统**，针对 **嗖马 SomaAI** (`www.somaagent.com.cn`) 网站构建。系统通过自动化查询各大 AI 平台，结合 NLP 情感分析，实现对品牌在生成式引擎中的可见性、引用率、情感倾向等核心指标的实时追踪与可视化展示。

## 五大架构层次

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 5: 前端展示层 (Frontend Dashboard)                    │
│  - HTML + ECharts 可视化看板                                 │
│  - 每30秒自动从 API 拉取最新数据                              │
├─────────────────────────────────────────────────────────────┤
│  Layer 4: API 服务层 (FastAPI)                               │
│  - RESTful API 提供数据接口                                  │
│  - /kpis /platforms /trend /snapshots /dashboard/all         │
├─────────────────────────────────────────────────────────────┤
│  Layer 3: 数据存储层 (SQLite + SQLAlchemy)                   │
│  - CrawlTask: 抓取任务记录                                   │
│  - CitationRecord: NLP分析后的结构化引用记录                  │
│  - DailyMetrics: 每日聚合指标                                │
│  - PlatformSnapshot: 平台最新快照                            │
├─────────────────────────────────────────────────────────────┤
│  Layer 2: 数据处理层 (NLP Analyzer)                          │
│  - 品牌检测 (Brand Detection)                                │
│  - 情感分析 (Sentiment Analysis)                             │
│  - 引用排名估算 (Citation Rank)                              │
│  - 内容质量评估 (Content Quality)                            │
├─────────────────────────────────────────────────────────────┤
│  Layer 1: 数据采集层 (Playwright Crawlers)                   │
│  - DeepSeek 爬虫                                             │
│  - 豆包 爬虫                                                 │
│  - 文心一言 爬虫                                             │
│  - Kimi 爬虫                                                 │
│  - (ChatGPT/Perplexity 需登录，待扩展)                        │
└─────────────────────────────────────────────────────────────┘
```

## 项目结构

```
pipeline/
├── config.py                 # 全局配置（品牌、平台、查询词）
├── database.py               # 数据库模型与 CRUD 操作
├── requirements.txt          # Python 依赖
├── run_api.py               # API 服务启动脚本
├── run_crawler.py           # 爬虫调度脚本
├── crawler/                 # 数据采集层
│   ├── __init__.py
│   ├── browser_manager.py   # Playwright 浏览器管理
│   ├── base_crawler.py      # 爬虫抽象基类
│   ├── deepseek_crawler.py  # DeepSeek 平台爬虫
│   ├── doubao_crawler.py    # 豆包平台爬虫
│   ├── wenxin_crawler.py    # 文心一言爬虫
│   └── kimi_crawler.py      # Kimi 爬虫
├── processor/               # 数据处理层
│   ├── __init__.py
│   └── nlp_analyzer.py      # NLP 分析引擎
├── api/                     # API 服务层
│   ├── __init__.py
│   └── main.py              # FastAPI 主应用
├── data/                    # SQLite 数据库目录
│   └── geo_data.db
└── logs/                    # 日志目录
```

## 快速开始

### 1. 安装依赖

```bash
cd pipeline
pip install -r requirements.txt
playwright install chromium
```

### 2. 初始化数据库

```bash
python database.py
```

### 3. 启动 API 服务

```bash
python run_api.py
```

服务将启动在 `http://localhost:8000`

- API 文档: http://localhost:8000/docs
- 数据看板: 打开同级目录的 `geo-dashboard.html`

### 4. 注入演示数据（用于测试）

```bash
curl -X POST http://localhost:8000/api/v1/seed
```

或直接访问: http://localhost:8000/api/v1/seed

### 5. 运行爬虫（采集真实数据）

```bash
# 运行所有平台的所有查询词语
python run_crawler.py

# 指定平台和查询词测试
python run_crawler.py --platform deepseek --query "AI营销机器人"

# 显示浏览器窗口（调试用）
python run_crawler.py --platform deepseek --visible
```

## API 接口列表

| 接口 | 方法 | 描述 |
|------|------|------|
| `/` | GET | 服务状态 |
| `/api/v1/kpis` | GET | 聚合 KPI 指标 |
| `/api/v1/platforms` | GET | 所有平台最新指标 |
| `/api/v1/platforms/{platform}` | GET | 指定平台趋势数据 |
| `/api/v1/snapshots` | GET | 平台快照明细 |
| `/api/v1/mentions` | GET | 品牌提及汇总 |
| `/api/v1/tasks` | GET | 最近抓取任务 |
| `/api/v1/dashboard/all` | GET | 看板全量数据（一次性） |
| `/api/v1/seed` | POST | 注入演示数据 |

## 爬虫工作流程

```
1. BrowserManager 启动 Chromium（无头模式）
2. 导航到目标 AI 平台（DeepSeek/豆包/文心一言/Kimi）
3. 定位输入框，模拟人类输入查询词
4. 等待 AI 生成回答
5. 提取回答文本
6. NLPAnalyzer 进行分析：
   - 检测是否提及"嗖马/SomaAI"
   - 分析情感倾向（正面/负面/中性）
   - 估算引用排名
   - 检测推荐信号
7. 结果存入 SQLite 数据库
8. 聚合生成每日指标
```

## NLP 分析维度

| 维度 | 说明 |
|------|------|
| 品牌检测 | 通过正则+别名匹配检测品牌提及 |
| 情感分析 | 基于规则（关键词匹配）或 Transformers 模型 |
| 引用排名 | 通过品牌首次出现位置估算排名 1-10 |
| 推荐检测 | 识别"推荐""首选"等明确推荐表述 |
| 内容质量 | 检测统计数据、权威信号等 |

## 配置说明

编辑 `config.py` 可自定义：

- **BRAND_CONFIG**: 目标品牌信息
- **AI_PLATFORMS**: 监测的 AI 平台及启用状态
- **SEARCH_QUERIES**: 自动化查询的关键词列表
- **NLP_CONFIG**: NLP 分析参数
- **SCHEDULER_CONFIG**: 爬虫调度配置
- **API_CONFIG**: API 服务配置

## 注意事项

1. **Playwright 依赖**: 首次运行需执行 `playwright install chromium`
2. **平台登录**: ChatGPT 和 Perplexity 需要登录，当前配置为禁用状态
3. **反检测**: 爬虫已注入反检测脚本，但平台可能更新检测机制
4. **频率控制**: 建议遵守各平台的使用条款，合理设置查询间隔
5. **数据准确性**: 当前情感分析默认使用基于规则的 fallback 模式，如需更高精度可安装 transformers 模型

## 后续扩展

- [ ] 接入真实 ChatGPT API (OpenAI)
- [ ] 接入百度搜索指数/微信指数等外部数据源
- [ ] 增加 transformers 情感分析模型支持
- [ ] 添加用户认证和权限管理
- [ ] 支持导出 Excel/PDF 报告
