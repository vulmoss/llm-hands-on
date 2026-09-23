# Web × AI 课程验证记录

日期：2026-09-23。基于远端 main `f65f307` 增补课程。所有实验数据为合成内容；没有测试第三方业务系统。

## 已完成

- Mac Python 3.12：12 个实验，每个漏洞版/修复版及正常请求对照均符合预期。
- 新增 pytest：33 项通过（5.13 秒的一次记录），覆盖真实回环 HTTP、身份矩阵、state 跨会话与重放、上传重置、数量边界、CORS 白名单、匿名存储、离线审阅与前端材料。
- Codex 内置浏览器：教学登录 200；漏洞版 Alice 读取 Bob 订单为 200、包含 B-book；修复版相同操作 403；动态 import 显示教学 chunk 文本。
- `.15:11434/api/tags` 实际可达，返回 qwen2.5:1.5b、qwen2.5:7b、all-minilm:33m。
- 通过原生 `/api/chat` 实际调用 qwen2.5:1.5b 两次，得到审阅草稿；每次都有 `done_reason=stop`。这证明集成能工作，不证明审计准确。

## 模型观察

第一次输入主要为响应与限制说明，模型重复“教学数据不能判断真实业务影响”，遗漏了 200 / 403、owner=bob 与所有权检查。已在课程中作为失败案例说明。第二次补充合成身份、原始请求，并要求逐条引用状态码/字段，模型正确引用了 200/403 和 Bob 订单，但把根因误解为 Cookie 标识匹配，又把 Alice 读 Bob 订单列为正常回归。人工纠正：问题是缺少对象所有权检查；正常回归应为 Alice 读订单 1，或 Bob 读订单 2。两次均未达到可独立审计标准，原始草稿见 [模型观察样例](web-ai-course-model-review.md)。模型意见不参与 passed 判定。

## 未完成或实现限制

- 本次未在 .16 运行：现有非交互 SSH 认证失败，未修改节点或认证配置。适配依据为已有 Ubuntu/Python 3.10 环境资料与标准库实现；Python 3.10 验证交由仓库 CI 矩阵。
- 无完整 OAuth/OIDC IdP、S3/OSS/COS、真实操作系统上传目录；对应实验明确为简化模型。
- 浏览器尚未验收反射 XSS 的脚本执行、真实跨站 CSRF/CORS、插件加载。HTTP 响应与前端静态文件检查不能替代这些验证。
- 独立 Playwright 启动被 macOS 沙箱的浏览器进程限制阻止；已用内置浏览器完成上述有限检查，没有将未执行步骤标记通过。
- 进阶 RCE/XXE/反序列化/SSTI、真实云签名、竞态、多语言框架与 Vulfocus 产品靶场为学习流程，未宣称本次实测。
- 固定教学 session/CSRF token 不可用于生产；源码 checkout 用于提供前端材料，独立 wheel 不含前端材料。

## 重跑

```bash
export PYTHONPATH="$PWD/src"
python3 -m llm_lab.web_security run --all
python3 -m pytest -q tests/security/test_web_course.py
python3 scripts/gen_security_catalog.py --check
```

## 全仓库回归

- `pytest -q`：106 passed；两个既有依赖弃用警告，不影响通过。
- 提示词库 `unittest`：9 项通过。
- Ruff 静态检查、格式检查、实验目录生成校验、Markdown 本地链接检查、JavaScript 语法检查与 `git diff --check` 通过。
- 本次没有修改 taskboard 代码，因此未重复运行其独立 Node/E2E 套件。
- Python 3.10 与 GitHub Actions 的运行结果应查看本次提交的 CI 状态，不能从 Mac Python 3.12 结果推断已通过。

