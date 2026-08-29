# GEO & SEO 可视化看板

> 针对 **SomaAI** (www.somaagent.com.cn) 的生成式引擎优化 (GEO) 成果量化看板，实时监测品牌在 DeepSeek、ChatGPT、豆包、文心一言、Kimi、Perplexity 等 AI 平台的可见性、引用率、情感倾向等核心指标。

**在线演示**: 部署后访问你的 Render URL 即可查看 网址为：https://geo-seo-dashboard.onrender.com/

---

## 架构简介

本项目采用前后端一体化部署，单个服务同时提供:
- 看板页面 (`/`)
- RESTful API (`/api/v1/...`)
- Swagger 文档 (`/docs`)

**数据流架构**:

```
GitHub Actions (每天定时)          GitHub 仓库              Render (在线服务)
┌──────────────────┐              ┌────────────┐           ┌──────────────┐
│ 1. 运行爬虫采集   │  ──push──>   │ JSON 数据   │  ──deploy─> │ API 读取 JSON │
│ 2. 导出为 JSON   │              │ dashboard   │           │ 看板实时展示  │
│ 3. 提交到仓库    │              │ _data.json  │           │               │
└──────────────────┘              └────────────┘           └──────────────┘
```

- **GitHub Actions**: 每天自动运行爬虫，将采集结果导出为 `pipeline/data/dashboard_data.json` 并提交
- **GitHub 仓库**: 存储 JSON 数据文件，每次更新触发 Render 自动重新部署
- **Render**: 读取 JSON 文件展示看板，无需运行爬虫和 SQLite

---

## 项目结构

```
geo-dashboard/
├── app.py                          # 部署入口 (Render/本地运行)
├── requirements.txt                 # Python 依赖
├── render.yaml                     # Render 部署配置
├── .gitignore
├── geo-dashboard.html              # 看板前端
├── assets/                          # 看板静态资源
│   └── charts.js
├── pipeline/                        # 数据管道
│   ├── config.py                    # 全局配置
│   ├── database.py                  # 数据库模型
│   ├── api/main.py                  # FastAPI 应用 (支持 JSON + SQLite 双数据源)
│   ├── export_data.py              # 数据导出工具 (SQLite → JSON)
│   ├── crawler/                     # 数据采集层
│   └── processor/                   # NLP 处理层
│   └── data/
│       └── dashboard_data.json     # 看板数据源 (GitHub Actions 定时更新)
└── .github/workflows/
    └── crawl.yml                   # GitHub Actions 定时爬虫工作流
```

---

## 快速部署到 Render （已部署）

他人打开该链接即可看到完整的看板，API 自动连接，数据每 30 秒刷新。

---

## 自动化数据更新 (GitHub Actions)

### 工作原理

| 环节 | 说明 |
|------|------|
| **触发条件** | 每天 UTC 03:00（北京时间 11:00）自动触发，或手动点击 Run workflow |
| **执行环境** | GitHub 提供的 Ubuntu 虚拟机 |
| **执行步骤** | 安装依赖 → 安装 Playwright → 运行爬虫 → 导出 JSON → 提交到仓库 |
| **数据持久化** | JSON 文件随代码一起提交到 Git，Render 部署时自动获取最新数据 |
| **失败处理** | 爬虫失败不会中断工作流，仍会导出已有的数据库数据 |

### 启用 GitHub Actions

首次推送代码后，GitHub Actions 工作流会自动生效。你可以在仓库页面的 **Actions** 标签查看运行记录。

**注意**: GitHub Actions 的 `schedule` 触发器在首次推送后可能需要等待一段时间才会生效（通常 1-2 小时）。你可以立即手动触发一次测试：

1. 打开仓库 → Actions → Daily GEO Data Crawl
2. 点击 **Run workflow** → **Run workflow**
3. 等待执行完成，检查 `pipeline/data/dashboard_data.json` 是否更新

### 工作流配置

`.github/workflows/crawl.yml` 中的关键配置:

```yaml
on:
  schedule:
    - cron: '0 3 * * *'      # 每天 UTC 03:00 = 北京时间 11:00
  workflow_dispatch:          # 支持手动触发
```
如需调整采集频率，修改 cron 表达式即可。

---

## 数据流向说明

### 部署模式 (Render 线上)

```
用户打开看板 → FastAPI 读取 pipeline/data/dashboard_data.json
                → 返回 JSON 中的 kpis + platforms + snapshots
                → 看板展示
```

- **数据源**: JSON 文件（由 GitHub Actions 定时更新）
- **优点**: 无需运行爬虫，启动快，数据持久
- **缺点**: 数据更新依赖 GitHub Actions 定时任务（每天一次）

### 本地开发模式

```
本地运行爬虫 → 数据存入 SQLite → 导出 JSON（可选）
                → 或 FastAPI 直接读取 SQLite
                → 看板展示
```

- **数据源**: SQLite 数据库（实时写入）
- **适用场景**: 本地调试、测试新爬虫逻辑

---

## 本地运行

### 方式 A: 使用 JSON 数据源（模拟部署环境）

```bash
cd geo-dashboard
pip install -r requirements.txt
python app.py
# 访问 http://localhost:8000
```

### 方式 B: 使用 SQLite + 爬虫（完整功能）

```bash
cd geo-dashboard/pipeline
pip install -r requirements.txt
playwright install chromium

# 注入演示数据
python export_data.py --with-demo

# 启动 API
python run_api.py
# 访问 http://localhost:8000

# 运行爬虫采集真实数据
python run_crawler.py
```

---

## 手动导出数据

本地运行爬虫后，手动导出数据为 JSON:

```bash
cd pipeline
python export_data.py
# 输出: pipeline/data/dashboard_data.json
```

然后提交到 GitHub，Render 会自动重新部署:

```bash
git add pipeline/data/dashboard_data.json
git commit -m "Update GEO data"
git push
```

---

## API 接口

| 接口 | 描述 |
|------|------|
| `/` | 看板页面 |
| `/api/v1/kpis` | 聚合 KPI 指标 |
| `/api/v1/platforms` | 所有平台最新指标 |
| `/api/v1/snapshots` | 平台快照明细 |
| `/api/v1/dashboard/all` | 看板全量数据 |
| `/docs` | Swagger 文档 |

---

## 数据口径与真实性

看板区分三种数据来源，并在页面横幅与明细表中标注：

| 来源 | 含义 |
| --- | --- |
| `real` | 官方 API / 浏览器真实采集的 AI 回答（无论是否提及品牌） |
| `simulated` | 搜索兜底或模拟生成的占位数据 |
| `demo` | 完全未采集时注入的种子数据 |

头部 KPI 提供双口径：`kpis`（全部平台均值）与 `kpis_real`（仅真实采集平台）。当存在真实平台时，页面默认展示真实口径并显示“仅真实平台”提示；趋势图 `/api/v1/trend` 只基于真实平台构建，避免模拟历史污染。各指标定义见 [docs/DATA_METRICS.md](docs/DATA_METRICS.md)。

## 趋势与周报

- `/api/v1/trend`：JSON 数据源优先，趋势数据由导出时按真实平台聚合生成；无真实数据时前端显示占位提示。
- `pipeline/generate_report.py`：生成 Markdown 周报到 `reports/`。
- `.github/workflows/weekly-report.yml`：每周日自动生成并提交周报。

## 测试

- `pipeline/tests/`：API、NLP、数据口径（真实 KPI / 趋势 / 周报）单元测试。
- `.github/workflows/crawl.yml` 中的 `test` job 每次运行 `pytest`。

---




## License

MIT
