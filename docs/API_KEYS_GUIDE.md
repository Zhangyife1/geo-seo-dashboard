# API Key 配置指南 — 接入真实 AI 平台数据

## 为什么需要配置 API Key？

GEO Dashboard 的数据采集管道支持两种运行模式：

1. **预留演示数据兜底（默认）**：当未配置任何 API Key 时，CI 环境不再生成模拟数据；真实采集不到的平台在导出阶段用预留演示数据补齐看板，方便预览，但数据不代表真实品牌可见性。
2. **真实数据模式**：配置各 AI 平台的 API Key 后，爬虫会通过官方 API 直接向 DeepSeek、Kimi、ChatGPT 等平台发送查询，采集真实的 AI 回答，再由 NLP 分析器计算品牌可见性指数、引用率、情感倾向等核心指标。

**简单来说：不配置 API Key = 看板用预留演示数据预览；配置后 = 看到嗖马 SomaAI 在各 AI 平台的真实曝光情况。**

---

## 各平台 API Key 一览

| 序号 | 平台 | 环境变量名称 | 获取地址 |
|------|------|--------------|----------|
| 1 | DeepSeek | `DEEPSEEK_API_KEY` | https://platform.deepseek.com/ |
| 2 | Kimi / Moonshot | `MOONSHOT_API_KEY` | https://platform.moonshot.cn/ |
| 3 | ChatGPT / OpenAI | `OPENAI_API_KEY` | https://platform.openai.com/ |
| 4 | Perplexity | `PERPLEXITY_API_KEY` | https://www.perplexity.ai/settings/api |
| 5 | 豆包 / 火山引擎 | `VOLC_API_KEY` | https://console.volcengine.com/ark |
| 6 | 文心一言 / 百度千帆 | `QIANFAN_API_KEY` + `QIANFAN_SECRET_KEY` | https://console.bce.baidu.com/qianfan/ |

> 注意：百度千帆需要同时配置两个变量（API Key 和 Secret Key），缺一不可。

---

## 各平台 API Key 获取方式

### 1. DeepSeek（推荐优先配置）

1. 访问 https://platform.deepseek.com/ ，注册并登录账号。
2. 进入「API Keys」管理页面。
3. 点击「创建 API Key」，生成一串以 `sk-` 开头的密钥。
4. 复制密钥并妥善保存（仅显示一次）。
5. DeepSeek 提供免费额度，新用户注册后可获得一定 token 赠送。

### 2. Kimi / Moonshot（推荐优先配置）

1. 访问 https://platform.moonshot.cn/ ，注册并登录。
2. 进入「API Key 管理」页面。
3. 点击「新建」创建 API Key。
4. 复制生成的密钥（以 `sk-` 开头）。
5. Moonshot 平台对新用户有免费体验额度，适合快速接入。

### 3. ChatGPT / OpenAI

1. 访问 https://platform.openai.com/ ，使用 OpenAI 账号登录。
2. 进入「API keys」页面（https://platform.openai.com/api-keys ）。
3. 点击「Create new secret key」生成密钥。
4. 复制密钥（以 `sk-` 开头）。
5. 注意：OpenAI API 为付费服务，需绑定信用卡并充值后方可使用。

### 4. Perplexity

1. 访问 https://www.perplexity.ai/settings/api ，登录账号。
2. 在 API 设置页面点击「Generate」生成 API Key。
3. 复制密钥（以 `pplx-` 开头）。
4. Perplexity API 为付费服务，提供 $5 的免费试用额度。

### 5. 豆包 / 火山引擎方舟

1. 访问 https://console.volcengine.com/ark ，注册火山引擎账号。
2. 完成实名认证。
3. 进入「方舟大模型平台」，开通模型推理服务。
4. 在「API Key 管理」中创建 API Key。
5. 复制生成的密钥。
6. 火山引擎对新用户有免费 token 额度。

### 6. 文心一言 / 百度千帆

1. 访问 https://console.bce.baidu.com/qianfan/ ，使用百度账号登录。
2. 完成企业/个人认证。
3. 进入「应用管理」，创建一个应用。
4. 在应用详情页获取 **API Key** 和 **Secret Key**。
5. 两个密钥都需要配置，缺一不可。
6. 千帆平台提供免费试用额度。

---

## 在 GitHub Secrets 中配置 API Key

爬虫运行在 GitHub Actions 中，需要通过 GitHub Secrets 安全地注入 API Key。请按以下步骤操作：

### 配置步骤

**第 1 步：进入 GitHub 仓库页面**

打开浏览器，访问你的 GEO Dashboard 仓库页面（例如 `https://github.com/你的用户名/geo-dashboard`）。

**第 2 步：进入 Secrets 管理页面**

在仓库页面顶部点击 **Settings** 标签页，然后在左侧菜单中依次展开：
- 点击 **Secrets and variables**
- 点击 **Actions**

此时你会看到「Repository secrets」区域，列出了已配置的所有密钥。

**第 3 步：新建 Secret**

点击绿色的 **「New repository secret」** 按钮。

**第 4 步：填写 Secret 信息**

在弹出的表单中：
- **Name**：输入环境变量名称（严格区分大小写），例如 `DEEPSEEK_API_KEY`
- **Secret**：粘贴对应的 API Key 值

> 名称必须与上文表格中的环境变量名称完全一致，否则爬虫无法读取。

**第 5 步：保存 Secret**

点击 **「Add secret」** 按钮，完成添加。添加后密钥值将不可再次查看（只能更新或删除）。

**第 6 步：重复添加其他平台**

对需要配置的每个平台重复第 3 ~ 5 步，依次添加：
- `DEEPSEEK_API_KEY`
- `MOONSHOT_API_KEY`
- `OPENAI_API_KEY`
- `PERPLEXITY_API_KEY`
- `VOLC_API_KEY`
- `QIANFAN_API_KEY`
- `QIANFAN_SECRET_KEY`

> 配置完成后，「Repository secrets」列表中应出现所有已添加的密钥名称。

### 配置示意图（文字说明）

```
仓库页面
  └── Settings（顶部标签）
        └── Secrets and variables（左侧菜单）
              └── Actions
                    └── [ New repository secret ] 按钮
                          ├── Name:  DEEPSEEK_API_KEY
                          └── Secret: sk-xxxxxxxxxxxxxxxxxxxx
                                └── [ Add secret ]
```

---

## 推荐优先配置的平台

如果时间或资源有限，建议按以下优先级配置：

| 优先级 | 平台 | 推荐理由 |
|--------|------|----------|
| ★★★★★ | DeepSeek | 接入最简单，注册即送免费额度，国内访问稳定 |
| ★★★★★ | Kimi / Moonshot | 接入简单，免费额度充足，中文理解能力强 |
| ★★★☆☆ | 豆包 / 火山引擎 | 国内平台，有免费额度，需实名认证 |
| ★★★☆☆ | 文心一言 / 百度千帆 | 国内主流平台，需配置两个密钥 |
| ★★☆☆☆ | ChatGPT / OpenAI | 需付费充值并绑定信用卡，国际平台 |
| ★★☆☆☆ | Perplexity | 需付费，免费试用额度较小 |

**建议：先配置 DeepSeek 和 Kimi 这两个平台，即可获得覆盖国内主流 AI 助手的真实数据。** 这两个平台注册门槛低、有免费额度、接入流程简单，是验证整条数据管道的最佳起点。

---

## 验证配置是否成功

配置完 GitHub Secrets 后，按以下步骤验证：

### 1. 手动触发 Workflow

1. 进入 GitHub 仓库的 **Actions** 标签页。
2. 在左侧 workflow 列表中选择 **「Daily GEO Data Crawl」**。
3. 点击右侧的 **「Run workflow」** 按钮。
4. 选择分支（通常为 `main`），点击绿色的 **「Run workflow」** 确认。

### 2. 查看运行日志

1. 在 Actions 页面点击刚刚触发的那次运行。
2. 点击 `crawl-and-export` 任务进入详细日志。
3. 展开 **「Run crawler (API-first + browser fallback)」** 步骤。
4. 查看日志中是否出现类似以下内容：

```
[deepseek API] Success
[deepseek API] Response received, length=1234
[kimi API] Success
[kimi API] Response received, length=987
```

- 如果看到 `[xxx API] Success`，说明对应平台的 API Key 配置成功，已获取真实数据。
- 如果看到 `[xxx API] Failed: Unauthorized` 或 `API key not configured`，说明该平台密钥未配置或无效。
- 如果看到 `No API keys configured`，说明该平台没有真实采集，导出时会用预留演示数据补齐；请补充对应平台的 API Key。

### 3. 检查数据更新

Workflow 运行成功后，检查 `pipeline/data/dashboard_data.json` 是否被自动提交更新（会有 `chore: update GEO data YYYY-MM-DD` 的 commit）。打开看板页面，确认各项指标不再是固定的演示数值。

---

## ADMIN_API_KEY 说明

除了上述各 AI 平台的采集密钥外，系统还有一个独立的管理密钥：

| 环境变量 | 用途 | 配置位置 |
|----------|------|----------|
| `ADMIN_API_KEY` | 保护 `/api/v1/seed` 接口，防止未授权调用演示数据注入接口 | Render 环境变量（部署时配置） |

### 作用

`/api/v1/seed` 接口用于在数据库为空时注入演示数据。该接口需要鉴权保护，调用时必须在请求头中携带 `X-Admin-Key`，且值与 `ADMIN_API_KEY` 环境变量一致，否则返回 `403 Forbidden`。

### 配置方法（Render 部署环境）

1. 登录 [Render 控制台](https://dashboard.render.com/)。
2. 进入你的 GEO Dashboard 服务。
3. 点击左侧 **Environment** 菜单。
4. 点击 **「Add Environment Variable」**。
5. **Key** 填 `ADMIN_API_KEY`，**Value** 填一个自定义的强随机字符串（例如 `geo-admin-2024-xyz-secret`）。
6. 保存后服务会自动重启。

> 该密钥**不需要**配置在 GitHub Secrets 中，仅在 Render 部署环境中配置即可。如果未配置，`/api/v1/seed` 接口将拒绝所有访问（始终返回 403）。

---

## 常见问题

**Q: 配置了 API Key 但采集还是失败怎么办？**

A: 请依次检查：
1. 密钥是否复制完整（前后没有多余空格）。
2. 密钥名称是否大小写完全正确。
3. 对应平台账号是否还有可用额度。
4. 查看 Actions 日志中的具体错误信息。

**Q: 可以只配置部分平台吗？**

A: 可以。未配置 API Key 的平台会自动跳过 API 采集，回退到浏览器爬虫模式；仍无真实数据时，导出阶段用预留演示数据补齐。建议至少配置 DeepSeek 和 Kimi 以保证基本的数据覆盖。

**Q: API Key 会泄露吗？**

A: 不会。GitHub Secrets 和 Render 环境变量都是加密存储的，日志中不会打印密钥明文，代码中通过 `${{ secrets.XXX }}` 引用，对协作者也不可见。
