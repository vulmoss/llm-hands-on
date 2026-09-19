# Promptfoo 接入现有 API

配置检查 `/chat`、`/rag`、`/agent`。所有测试固定为本地接口，使用 JavaScript 断言，
没有配置外部模型评分器。Agent 断言检查实际 trace；RAG 来源非空只证明返回了候选来源，
并不能证明引用正确。文档注入的成对评估使用 [RAG 实验](../../rag-injection/README.md)。

## 离线可验证的范围

```bash
python -m pytest -q tests/security/test_promptfoo_contract.py
```

测试读取配置，用 FastAPI TestClient 与假模型验证请求/响应契约，并在本机有 Node.js 时运行实际
JavaScript 断言。没有 Node.js 时仅这部分断言测试跳过；CI 提供 Node.js。
这不等于执行过 Promptfoo CLI 或连接过真实模型。

## 环境恢复后

在仓库根目录，先准备样例笔记索引、启动 API：

```bash
python -m llm_lab index data/notes
python -m llm_lab serve
```

在另一个终端使用已安装的 Promptfoo CLI：

```bash
mkdir -p .data/security
PROMPTFOO_DISABLE_TELEMETRY=1 promptfoo eval --config 05-security/integrations/promptfoo/config.json --max-concurrency 1 --no-cache --output .data/security/promptfoo.json
```

安装方式按 [官方安装说明](https://www.promptfoo.dev/docs/installation/) 操作，实测时记录
`promptfoo --version`、Node.js 版本、应用提交与模型版本。本次仅交付适配配置，端到端验证待完成。
变更端口时修改 provider URL。增加测试时保持正常对照和可解释的断言。

参考：[HTTP provider](https://www.promptfoo.dev/docs/providers/http/) ·
[断言说明](https://www.promptfoo.dev/docs/configuration/expected-outputs/)。
