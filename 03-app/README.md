# 应用开发：三个能力，共用一套核心

先完成根目录 README 的安装和配置。所有命令从仓库根目录运行。

| 学习顺序 | 章节 | 核心代码 |
|---|---|---|
| 1 | [聊天](chat-ui/README.md) | `src/llm_lab/chat.py`、`client.py` |
| 2 | [RAG](rag/README.md) | `src/llm_lab/rag.py` |
| 3 | [Agent](agent/README.md) | `src/llm_lab/agent.py`、`tools.py` |

先运行 `examples/01_direct_http.py` 观察原始请求，再阅读这三个章节。
每个目录中的旧 demo 现在是兼容入口，业务代码统一放在 `src/llm_lab/`，避免多份实现漂移。

```bash
llm-lab ask '你好' --stream
llm-lab index data/notes
llm-lab rag '应用负责什么？'
llm-lab agent '100 公里是多少英里？' --trace
```

RAG 和 Agent 都复用聊天协议。区别在于：RAG 在请求前检索资料，Agent 在模型提出工具请求后执行工具并继续请求。
