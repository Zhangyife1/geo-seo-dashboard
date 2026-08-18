# 站点收录操作清单（按顺序执行）

> 需要你使用对应平台的账号登录操作。每一步完成后打勾，全部完成后运行 `scripts/check_index_status.py` 复查。

## 0. 发布前准备（已完成模板，待上线）

- [ ] 在官网发布 `content/about-soma.md` 品牌事实页，URL 建议：`https://www.somaagent.com.cn/about-soma/`
- [ ] 在官网发布 `content/query-pages/` 下 8 个查询页，URL 建议：`https://www.somaagent.com.cn/geo/ai-marketing-robot/` 等
- [ ] 将 `seo/faq-jsonld-template.jsonld` 里的 FAQ 结构化数据粘贴到每个查询页头部
- [ ] 将 `seo/organization.jsonld` 粘贴到官网全站 `<head>`
- [ ] 将 `seo/sitemap-additions.xml` 里的 URL 合并进官网现有 sitemap（Rank Math 后台可添加自定义 URL 或直接编辑 sitemap）

## 1. 百度（最重要，国内模型和搜索主要来源）

### 1.1 注册并验证站点

1. 打开 https://ziyuan.baidu.com ，用百度账号登录
2. 左侧「站点管理」→「添加网站」，输入 `https://www.somaagent.com.cn`
3. 选择验证方式（任选其一）：
   - HTML 标签验证：把 Meta 标签复制到官网首页 `<head>`
   - 文件验证：把下载的验证文件上传到网站根目录
   - CNAME 验证：在域名 DNS 解析里添加 CNAME 记录
4. 验证成功后，站点状态变为“已认证”

### 1.2 提交 sitemap

1. 左侧「普通收录」→「sitemap」
2. 提交 `https://www.somaagent.com.cn/sitemap.xml`
3. 状态显示“正常”即生效，抓取频次选择“自动”

### 1.3 普通收录（手动提交新 URL）

#### 操作路径（不同版本界面文案略有差异）

登录 https://ziyuan.baidu.com → 确认当前操作的是已验证站点 `www.somaagent.com.cn` → 进入「搜索服务 / 资源提交 / 数据引入」→「普通收录」→ 切换到「手动提交」页签。

#### 具体步骤

1. 登录百度搜索资源平台：https://ziyuan.baidu.com ，如果账号下有多个站点，先在左上角/站点列表中确认选中 `www.somaagent.com.cn`。
2. 左侧菜单找到「资源提交」（部分版本显示为「数据引入」或「搜索服务」），点击进入「普通收录」。
3. 在「普通收录」页面顶部有三个页签：**API提交**、**手动提交**、**sitemap文件提交**，点击「手动提交」。
4. 在输入框中粘贴要提交的 URL，**每行一个**，例如：

```text
https://www.somaagent.com.cn/geo/ai-marketing-robot/
https://www.somaagent.com.cn/geo/intelligent-leads/
https://www.somaagent.com.cn/geo/ai-customer-service/
```

5. 提交前检查 URL 是否符合要求：
   - 必须是完整 URL（含 `https://`）
   - 域名必须与已验证站点一致（`www.somaagent.com.cn`）
   - 不能带中文、空格、`#` 锚点或多余参数
   - 如果页面有 301 跳转，直接提交跳转后的最终 URL
6. 查看页面上的配额提示（每日配额由站点质量和用户喜爱度决定，站点不同数量不同），确认今日剩余配额足够。
7. 点击「提交」按钮，等待页面提示提交结果。
8. 到「普通收录 → 数据反馈」查看：会显示当天通过不同方式提交成功的**去重后链接数量**；失败链接会给出原因（域名不符、格式错误、URL 不可访问、重复提交等）。
9. 提交后不要反复提交相同 URL（会重复消耗配额，且无额外效果）。

#### 提交后如何确认是否生效

- 到「数据统计 → 抓取诊断」输入刚才提交的 URL，点击抓取，确认百度蜘蛛能看到页面内容（HTTP 200 且返回正文）。
- 到「数据统计 → 索引量」查看该 URL/目录是否进入索引（索引数据最快每天更新，最迟一周）。
- 一般 3-7 天可见抓取/索引反馈，新站或低权重页面可能更久。

#### 常见失败原因

- URL 未上线或返回 404/403/5xx
- robots.txt 屏蔽了 Baiduspider
- 提交了跳转前的链接（应提交 301 后的最终链接）
- URL 含中文、空格或与验证域名不一致
- 当日配额已用完

### 1.4 快速收录 API（推荐，发布后实时推送）

1. 左侧「普通收录」→「快速收录」→「API 提交」→ 生成专属 `token`
2. 把 token 填入 `scripts/baidu_push.py` 的环境变量 `BAIDU_PUSH_TOKEN`
3. 每次发布新文章后执行：

```bash
python brand-geo/scripts/baidu_push.py https://www.somaagent.com.cn/geo/ai-marketing-robot/ https://www.somaagent.com.cn/geo/ai-customer-service/
```

## 2. 必应（Bing，影响 ChatGPT/Perplexity 的检索来源）

1. 打开 https://www.bing.com/webmasters ，用 Microsoft 账号登录
2. 「添加网站」→ 输入 `https://www.somaagent.com.cn`
3. 验证方式：DNS TXT 记录或 HTML 文件任选
4. 「Sitemaps」→ 提交 `https://www.somaagent.com.cn/sitemap.xml`
5. 对重点页面使用「URL 检查」→「请求编制索引」

## 3. Google（影响 ChatGPT/Perplexity/海外模型）

1. 打开 https://search.google.com/search-console ，用 Google 账号登录
2. 「添加资源」→ 建议选「网域」→ 输入 `somaagent.com.cn`
3. 按提示在 DNS 添加 TXT 记录完成验证
4. 「Sitemap」→ 提交 `sitemap.xml`
5. 对每个查询页使用「网址检查」→「请求编入索引」

## 4. 360 站长平台

1. 打开 https://zhanzhang.so.com ，360 账号登录
2. 添加站点 → 验证（推荐 CNAME 或 HTML 标签）
3. 提交 sitemap：`https://www.somaagent.com.cn/sitemap.xml`
4. 手动提交 8 个查询页 URL

## 5. 搜狗站长平台

1. 打开 https://zhanzhang.sogou.com ，搜狗/QQ 账号登录
2. 添加站点 → 验证
3. 提交 sitemap 和核心 URL

## 6. 百科类（提高模型知识库命中率）

- [ ] 百度百科：创建词条「嗖马人工智能技术（杭州）有限公司」或「嗖马SomaAI」，参考资料必须包含官网、媒体报道、天眼查工商信息
- [ ] 搜狗百科：同步创建
- [ ] 360百科：同步创建

## 7. 第三方内容平台（增加被检索引用的入口）

- [ ] 知乎：发布“AI营销机器人怎么选”等 8 个问题的高质量回答，文末附官网链接
- [ ] 百家号：发布 8 篇与查询页同主题的文章
- [ ] CSDN/掘金：发布“AI 营销机器人技术方案”类文章
- [ ] 微信公众号：发布品牌介绍 + 行业解读，同步到搜狗微信搜索

## 8. 口碑与投诉处理（必做，否则负面会被 AI 引用）

- [ ] 在黑猫投诉平台认领企业主体（https://tousu.sina.com.cn/ ）
- [ ] 对已投诉订单逐一回复、退款/处理，并请消费者撤诉或追加好评
- [ ] 在官网「服务与支持」页面公示售后/退款流程，降低投诉率
- [ ] 定期搜索“嗖马 投诉”“SOMA智选 退款”，发现新负面及时处理

## 9. 复查

全部完成后：

```bash
cd geo-seo-dashboard
python brand-geo/scripts/check_index_status.py
```

脚本会检查官网 robots、sitemap、必应收录情况，并输出报告。
