# 11 · 把 Web 权限思维迁移到 RAG 与 Agent

目标：区分提示注入、数据权限和执行器权限。先修：单元 02、10。

```bash
python3 -m llm_lab security-eval --cases data/security/benign.jsonl data/security/rag-injection.jsonl --check
python3 -m pytest -q tests/security/test_agent_boundaries.py
```

`--check` 只验证样例格式。真实评估继续读 `05-security/rag-injection/README.md`，按其命令调用模型并保存结果；不要把离线替身当作真实模型实验。

Web 对象权限与 RAG 文档权限是同一个问题的两个入口：不能等模型看到所有文档后再要求它不泄露，应在检索前过滤可读文档。工具执行也不能只靠 system prompt，应在函数调用前校验工具名称、参数、主体和资源。现有 Agent 的次数预算与参数校验提供工程边界，不保证模型每次选择正确。

按配对样例记录正常任务成功率、注入任务偏移、拒绝过度与执行器拒绝。模型输出听从了恶意文档与实际触发外部操作是不同后果。本课程的 review 不提供执行工具，材料中的指令只作为待审数据。

进阶知识库：只索引自己整理的无凭据笔记；每条结论保留来源、日期与验证状态。新增笔记后重建索引并用有答案/无答案问题各验证一次。

产物：一个正常/注入配对、工具拒绝 trace、检索前权限设计。下一课：[综合报告](12-capstone.md)。
