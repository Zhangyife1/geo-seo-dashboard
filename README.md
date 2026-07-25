# GEO & SEO 可视化看板

> 针对 **嗖马 SomaAI** (www.somaagent.com.cn) 的生成式引擎优化 (GEO) 成果量化看板，实时监测品牌在 DeepSeek、ChatGPT、豆包、文心一言、Kimi、Perplexity 等 AI 平台的可见性、引用率、情感倾向等核心指标。

**在线演示**: 部署后访问你的 Render URL 即可查看

## 架构简介

本项目采用前后端一体化部署，单个服务同时提供:
- 看板页面 (`/`)
- RESTful API (`/api/v1/...`)
- Swagger 文档 (`/docs`)

## 项目结构

```
geo-dashboard/
├── app.py                  # 部署入口 (Render/本地运行)
├── requirements.txt         # Python 依赖
├── render.yaml             # Render 部署配置
├── .gitignore
├── geo-dashboard.html      # 看板前端
├── assets/                  # 看板静态资源
│   └── charts.js
└── pipeline/                # 数据管道
    ├── config.py             # 全局配置
    ├── database.py           # 数据库模型
    ├── api/main.py           # FastAPI 应用
    ├── crawler/              # 数据采集层
    └── processor/            # NLP 处理层
```

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

他人打开该链接即可看到完整的看板，API 自动连接，数据自动刷新。

## 本地运行

```bash
cd geo-dashboard
pip install -r requirements.txt
python app.py
# 访问 http://localhost:8000
```

## 关于"实时数据"

- 部署后首次启动会自动注入 30 天的演示数据
- 看板每 30 秒自动刷新一次 API 数据
- 如需真实数据，在本地运行爬虫采集，然后将 `pipeline/data/geo_data.db` 上传到服务器

## API 接口

| 接口 | 描述 |
|------|------|
| `/` | 看板页面 |
| `/api/v1/kpis` | 聚合 KPI 指标 |
| `/api/v1/platforms` | 所有平台最新指标 |
| `/api/v1/snapshots` | 平台快照明细 |
| `/api/v1/dashboard/all` | 看板全量数据 |
| `/docs` | Swagger 文档 |

## License

MIT
