# GEO & SEO 可视化看板

> 针对 **嗖马 SomaAI** (www.somaagent.com.cn) 的生成式引擎优化 (GEO) 成果量化看板，实时监测品牌在 DeepSeek、ChatGPT、豆包、文心一言、Kimi、Perplexity 等 AI 平台的可见性、引用率、情感倾向等核心指标。

**在线演示**: 部署后访问你的 Render URL 即可查看

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

## 快速部署到 Render (免费、带链接)

### 步骤 1: 创建 GitHub 仓库

```bash
cd geo-dashboard
git init
git add .
git commit -m "Initial commit: GEO & SEO dashboard"
git remote add origin https://github.com/<你的用户名>/geo-seo-dashboard.git
git push -u origin main
```

### 步骤 2: 在 Render 创建服务

1. 打开 [https://render.com](https://render.com)，用 GitHub 账号登录
2. 点击 **New +** → **Web Service**
3. 连接你的 GitHub 仓库 `geo-seo-dashboard`
4. Render 会自动识别 `render.yaml` 配置
5. 确认以下设置:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Free
6. 点击 **Create Web Service**
7. 等待构建完成（约 2-3 分钟）

### 步骤 3: 分享链接

部署成功后，Render 会分配一个公可访问的 URL，例如:

```
https://geo-seo-dashboard-xxxx.onrender.com/
```

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

## 常见问题

**Q: GitHub Actions 爬虫运行失败怎么办？**
A: 爬虫因网络/反爬失败是正常现象。工作流设置了 `continue-on-error: true`，失败时仍会导出已有的数据库数据。你可以在 Actions 日志中查看具体错误。

**Q: Render 上看板数据没有更新？**
A: 检查 GitHub Actions 是否成功执行并提交了 `dashboard_data.json`。Render 每次检测到代码更新会自动重新部署，冷启动约需 30 秒。

**Q: 可以修改爬虫运行频率吗？**
A: 可以。编辑 `.github/workflows/crawl.yml` 中的 `cron` 表达式。例如 `'0 */6 * * *` 表示每 6 小时运行一次。注意 GitHub Actions 免费额度为每月 2000 分钟。

**Q: 本地开发和线上部署的数据源可以切换吗？**
A: API 自动检测：如果 `pipeline/data/dashboard_data.json` 存在，优先读取 JSON；否则回退到 SQLite。所以部署时只要包含 JSON 文件即可使用 JSON 数据源。

---

## License

MIT
