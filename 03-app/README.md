# 03 - 应用开发层

> 用 LangChain 构建 LLM 应用：聊天界面、RAG 文档问答、Agent 工具调用。

## 目录

| Demo | 目录 | 核心概念 | 难度 |
|------|------|----------|------|
| Demo1: 聊天界面 | `chat-ui/` | LLM API、多轮对话、Gradio Web UI | 入门 |
| Demo2: RAG 问答 | `rag/` | Embedding、向量数据库、检索增强生成 | 中级 |
| Demo3: Agent | `agent/` | 工具定义、ReAct 模式、自主决策 | 中级 |

## 每个 Demo 的文件

```
chat-ui/
├── README.md           # 逐行讲解 + 5 个练习
├── app.py              # 提取的学习用代码（含所有练习）
└── demo1_chat_ui.py    # 可直接运行的完整代码

rag/
├── README.md
├── demo2_rag.py

agent/
├── README.md
└── demo3_agent.py
```

## 运行方式

```bash
# SSH 到 VM2
ssh llm2@192.168.2.16

# 运行任意 demo
cd ~/demos
python3 demo1_chat_ui.py    # 聊天界面 → http://192.168.2.16:7860
python3 demo2_rag.py        # RAG 问答（命令行输出）
python3 demo3_agent.py      # Agent 工具调用（命令行输出）
```

## 学习顺序

建议按 Demo1 → Demo2 → Demo3 顺序学习。每个 demo 先读 README.md 理解原理，再运行代码观察效果，最后动手做练习。
