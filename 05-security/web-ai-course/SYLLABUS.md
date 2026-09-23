# 12 周学习与验收路线

建议每周 8 小时，共约 96 小时；这是本模块估算，不沿用海报的课时或收益承诺。每周：原理 2h、手动实验 2h、代码/测试 2h、AI 复核与记录 2h。时间不足时延长周期，以验收为准。

| 周 | 单元与先修 | 当周操作 | 必交产物 / 通过标准 |
|---|---|---|---|
| 1 | [HTTP 与实验基线](units/01-foundations.md)，Python 基础 | doctor、单次正常请求、学习浏览器 Network | 环境记录；能解释 method/header/body/status |
| 2 | [AI 证据工作流](units/02-ai-workflow.md)，周 1 | 单实验 JSON → 离线消息 → Ollama 草稿 | 逐句标事实/推测；指出至少一个模型遗漏 |
| 3 | [JS / 前端入口](units/03-frontend.md)，周 1 | DOM 对照、source map、动态模块、插件 | 入口表与一个假阳性解释 |
| 4 | [浏览器边界](units/04-browser.md)，周 3 | xss/csrf/cors/redirect；手动浏览器对照 | 正常与异常请求、响应头和截图 |
| 5 | [认证授权](units/05-auth.md)，周 1/4 | idor/mass-assignment/oauth；两账号矩阵 | 所有权、字段权限、state/replay 分别成立 |
| 6 | [服务与文件边界](units/06-service-files.md)，周 1/5 | ssrf/upload；上传名、下载名对照 | 说明哪些是实际网络请求、哪些是虚拟存储 |
| 7 | [数据库注入](units/07-injection.md)，周 1 | sqli；读查询、改参数化、跨数据库对照 | 查询结构变化解释；两条正常回归 |
| 8 | [云与进阶漏洞](units/08-cloud-advanced.md)，周 5/6/7 | cloud-storage；XML/RCE/签名高级流程选一 | 权限矩阵或靶场版本与失败案例；不冒充云实测 |
| 9 | [业务状态机](units/09-business.md)，周 5 | business-logic；价格/数量/重放/并发设计 | 状态转移图、幂等与原子性验收定义 |
| 10 | [多语言代码审计](units/10-audit.md)，周 3/5/7 | 六语言题；在已有 taskboard 跟踪一条调用链 | Source→验证→Sink + 修复与回归 |
| 11 | [AI 系统边界](units/11-ai-boundaries.md)，周 2/10 | 现有 RAG 配对与 Agent 边界实验 | 区分模型回答偏移、检索权限、工具权限 |
| 12 | [综合项目与报告](units/12-capstone.md)，前 11 周 | 选 3 个实验，盲测→审计→修复→复测 | 完整报告；同学只读报告即可复现 |

## 最短主线

先做 01 → 03 → 05 → 07 → 02 → 12：HTTP、JS、越权、SQL、AI 复核、报告。完成后再补跨站、OAuth、云和进阶解析器。所有课都用“正常—异常—修复后异常—修复后正常”四格证据，不仅保存成功的一次请求。

## 毕业标准

1. 无模型也能完成 12 个对照实验，能定位根因所在分支。
2. 浏览器里解释 XSS HTML 上下文、DOM sink、Cookie/SameSite、CORS 与 CSRF 的区别。
3. 对同一资源用匿名 / 所有者 / 他人执行权限矩阵；固定 ID 改为 UUID 后仍能解释权限问题。
4. 模型产出的审阅必须指向真实证据，不能把“建议测试”写成“已经发现”。
5. 区分本地模型实验、真实产品靶场与真实业务结论；未验证项如实留空。
6. 报告含修复和复测，以及不会暴露真实凭据的最小证据。
