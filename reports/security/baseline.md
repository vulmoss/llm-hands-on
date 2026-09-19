# 安全实验基线

状态：离线工程验证通过；真实模型评估未运行。
原因：当前 LLM 测试环境不可连接，本次不尝试连接或启动模型服务。

离线验证日期：2026-09-19（UTC）。
环境：Python 3.12.5，v26.8.1（Node.js），macOS。
完整测试：73 passed；其中包含本地 JavaScript 断言正反例，无安全测试跳过。
Ruff 检查、格式检查、20 条样例校验与目录一致性检查均通过。
测试运行出现两条第三方弃用提示（Starlette/httpx 与 AnyIO），未影响本次测试。

复核命令（已安装开发依赖与 Node.js 的环境）：

```bash
GRADIO_ANALYTICS_ENABLED=False python -m pytest -q
python -m ruff check .
python -m ruff format --check .
python scripts/gen_security_catalog.py --check
python -m llm_lab security-eval --cases data/security/benign.jsonl data/security/rag-injection.jsonl --check
```

## 验证层次

| 层次 | 本次结果 | 证据 |
|---|---|---|
| 样例和生成目录 | 通过 | `security-eval --check`、`scripts/gen_security_catalog.py --check` |
| Agent 执行边界、评估统计 | 通过 | `tests/security/` |
| Promptfoo 请求/响应与 JS 断言 | 通过 | `tests/security/test_promptfoo_contract.py` |
| Promptfoo CLI 与实际服务 | 未运行 | 环境恢复后执行 |
| 真实 RAG 提示注入、正常回答质量 | 未运行 | 无实测通过率或攻击成功率 |

测试替身的结果只验证程序行为，不作为模型成绩。正式结果保存于 `.data/security/`，不默认提交原始输出。
公开报告应复核样例内容和错误信息，仅发布适合公开的证据。

## 恢复环境后补充

- 日期、代码提交、Python / Ollama / Promptfoo 版本。
- 生成模型与 Embedding 模型名称及 digest，参数、重复次数。
- 数据与代码 SHA-256（评估结果自动记录）。
- 正常/注入各自的尝试数、完成数、错误数、通过数与标记命中数。
- 人工复核确认的注入行为、误报和漏报；改动前后比较。
- 局限：固定小样本、子串启发式、单文档检索，不代表普遍安全性。
