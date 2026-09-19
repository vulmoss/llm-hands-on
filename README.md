# LLM Hands-on：从一次请求到文档助手

面向有少量 Python 基础的 AI 初学者。通过可观察、可测试的小步骤学习：
**HTTP 请求 → 多轮聊天 → 模型实验 → RAG → Agent → API / 网页 → 安全实验。**

核心代码只依赖 Python 标准库，Gradio 和 FastAPI 按需安装。所有入口共用同一套配置和业务逻辑。
原有 ESXi 操作记录保留在 `01-infra/`，已有的三组 demo 路径保留为兼容入口。

安全实操从 [实验目录](05-security/LABS.md) 开始：包含 10 组 RAG 正常/注入对照、
Agent 执行边界回归和 Promptfoo API 适配。
[基线记录](reports/security/baseline.md) 区分离线工程验证与尚待完成的真实模型评估。

## 1. 安装与配置

需要 Python 3.10+ 和可访问的 Ollama 服务。在仓库根目录运行：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
cp .env.example .env
# 编辑 .env 后将配置导入当前终端；程序不会自动读取 .env
set -a
source .env
set +a
```

默认连接 `http://127.0.0.1:11434`。使用原有 VM1 时，设置：

```bash
export OLLAMA_BASE_URL=http://192.168.2.15:11434
```

这里使用 Ollama **原生接口**，地址不加 `/v1`。在运行 Ollama 的主机准备模型：

```bash
ollama pull qwen2.5:7b
ollama pull all-minilm:33m
```

模型名沿用原项目，便于已有环境迁移，不代表模型效果排名。CPU 环境可先用
`OLLAMA_MODEL=qwen2.5:1.5b` 练习聊天；Agent 需要模型支持工具调用，应单独验证。

```bash
llm-lab doctor
llm-lab ask '用一句话解释 Token' --stream
llm-lab chat
```

`doctor` 检查连接与两个配置模型是否存在；缺少模型返回退出码 1。
它不验证模型的工具调用能力或检索质量。只练聊天时，Embedding 模型暂时可以不安装。

不安装项目也能运行第一课：`python examples/01_direct_http.py`。
其他命令也支持 `PYTHONPATH=src python -m llm_lab ...`。

## 2. 学习路径和验收

每天约两小时、希望先完成一周实操，可从[第一周学习计划](docs/week-01-plan.md)开始。
对应的[实验日志与验收表](practice/week-01/log.md)已放在工作区，按天填写即可。

| 阶段 | 阅读 / 运行入口 | 完成标准 |
|---|---|---|
| HTTP | `examples/01_direct_http.py` | 能解释发送的 JSON 和响应内容 |
| 聊天 | `examples/02_chat.py`、`src/llm_lab/chat.py` | 删除历史后，能解释第二轮答案的变化 |
| 模型实验 | [02-model](02-model/README.md) | 固定题目和参数，记录模型效果及耗时 |
| RAG | `examples/03_rag.py`、`src/llm_lab/rag.py` | 分清检索失败与生成失败，展示原始片段 |
| Agent | `examples/04_agent.py`、`src/llm_lab/agent.py` | 看懂工具参数、结果回传和停止原因 |
| 工程化 | [04-engineering](04-engineering/README.md) | 新环境可启动，故障有清晰反馈 |
| 安全实验 | [05-security](05-security/LABS.md) | 保存固定样例的结果，区分模型行为与执行器边界 |

每次实验只改一个变量，记录预期、实际输出和解释。不要用一次回答判断模型能力。
完整练习清单见 [学习与实验手册](docs/learning.md)。

## 3. 文档问答

```bash
# 构建时调用 Embedding 模型；索引保存到 .data/index.json
llm-lab index data/notes
# 先只看检索片段和分数
llm-lab rag '推理服务负责什么？' --retrieve-only
# 再生成回答并展示来源
llm-lab rag '推理服务负责什么？'
llm-lab rag '实验室的 GPU 序列号是什么？' --json
```

支持 UTF-8 `.md` / `.txt`，保留相对文件名和字符偏移。修改资料、切块策略或
Embedding 模型后重新构建；构建成功才替换旧索引，不会不断追加重复片段。
默认使用全部候选中的 top-k，可用 `--min-score` 在自己的题集上实验阈值。
相似度不是正确率，提示词也不能保证模型总会拒绝无依据问题。

## 4. 工具调用

```bash
llm-lab agent '计算 2 的 10 次方，假设单位是 MiB，换算成 GiB。' --trace
llm-lab agent '查询笔记，说明推理服务和应用的分工。' --with-notes --trace
```

默认提供计算、单位转换工具，`--with-notes` 加入已构建索引的检索工具。
计算器使用明确的操作枚举和两个数字，不执行表达式或任意代码。
`trace` 是工具调用记录，包含名称、参数和结果。
达到总工具调用上限时输出未完成状态并返回退出码 2。

## 5. 网页与 API

```bash
python -m pip install -e '.[ui,api]'
llm-lab ui                  # http://127.0.0.1:7860
llm-lab serve               # http://127.0.0.1:8000/docs
```

两条服务命令分别在不同终端运行。网页支持流式聊天、系统提示词和浏览器本地历史。
API 提供 `/health`、`/chat`、`/rag`、`/agent`。API 的聊天历史由每次请求显式传入。
`/agent` 默认仅开放计算和转换；笔记工具目前在 CLI 中通过 `--with-notes` 启用。

默认监听本机。原有内网 VM 场景可以加 `--host 0.0.0.0`，再用 VM 地址访问。
这是单用户教学服务，没有用户认证；更多部署说明见工程化章节。

## 6. 架构

```text
examples/、CLI、Gradio UI、FastAPI
                    ↓
       chat / rag / agent / benchmark
                    ↓
            OllamaClient + Settings
                    ↓
             Ollama 原生 HTTP API
```

```text
src/llm_lab/
  config.py       环境配置与检查
  client.py       HTTP / NDJSON / Embedding / 错误转换
  chat.py         消息构建与历史裁剪
  rag.py          文档、切块、持久化索引、检索与回答
  tools.py        工具定义、参数校验和注册
  agent.py        有工具调用预算的显式循环
  benchmark.py    客户端延迟与服务端吞吐指标
  cli.py          统一命令行
  ui.py / api.py  可选入口
examples/         按学习顺序排列的短脚本
data/notes/       无需私人数据的样例文档
data/eval/        有参考答案的小型题集
tests/            不依赖真实模型的自动化验证
docs/             架构、学习和迁移说明
```

设计取舍与扩展位置见 [架构说明](docs/architecture.md)，旧版用法变化见
[迁移说明](docs/migration.md)。

## 7. 安全实验

模型环境不可用时，可以先检查样例、执行器和实验导航：

```bash
python -m llm_lab security-eval --cases data/security/benign.jsonl data/security/rag-injection.jsonl --check
python -m pytest -q tests/security
python scripts/gen_security_catalog.py --check
```

`--check` 不连接模型。真实 RAG 评估、指标解释和前后对照见
[RAG 文档注入实验](05-security/rag-injection/README.md)；
API 接入见 [Promptfoo 配置](05-security/integrations/promptfoo/README.md)。
模型测试结果保存到 `.data/security/`，目录清单保存在 `data/security/labs.json`。

## 8. 验证

```bash
python -m pip install -e '.[api,ui,dev]'
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
```

自动化测试使用可控的模型替身检查程序行为，不证明真实模型的回答质量。
用 `data/eval/questions.jsonl` 和自己的问题做人工复核，并保存实验记录。
`requirements-lock.txt` 保存一次完整开发环境的依赖快照；使用方式和平台限制见工程化章节。

## 协议参考

- [Ollama Chat API](https://docs.ollama.com/api/chat)
- [Ollama Embedding API](https://docs.ollama.com/api/embed)
- [Ollama 工具调用](https://docs.ollama.com/capabilities/tool-calling)
- [Gradio ChatInterface](https://www.gradio.app/docs/gradio/chatinterface)
