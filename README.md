# ai-agent-study
# LLM 应用开发学习手册

> 面向 AI 新手工程师，从零基础到能独立开发 LLM 应用。
> 配套环境：VM1 (192.168.2.15) 提供 Ollama 推理，VM2 (192.168.2.16) 提供 Python 开发环境。

## 学习路线

```
Demo1 (入门)          Demo2 (进阶)           Demo3 (高级)
Gradio 聊天界面  -->  RAG 文档问答  -->  Agent 工具调用
  |                    |                    |
  |- LLM API 调用      |- 文本向量化         |- 工具定义
  |- 多轮对话管理       |- 向量数据库         |- 自主决策
  |- Web UI 搭建       |- 检索增强生成       |- LangGraph 状态机
```

## 前置知识

| 知识点 | 需要程度 | 学习资源 |
|--------|----------|----------|
| Python 基础 | 必须 | 菜鸟教程 python3 |
| HTTP 请求 (GET/POST) | 必须 | 了解 REST API 概念 |
| JSON 数据格式 | 必须 | Python json 模块 |
| pip 包管理 | 必须 | `pip3 install xxx` |
| 类与对象 | Demo2/3 需要 | Python OOP 基础 |

## 文件结构

```
esxi/
├── demos/                        # 可运行的 demo 代码（已部署在 VM2 ~/demos/）
│   ├── demo1_chat_ui.py          # Gradio 聊天界面
│   ├── demo2_rag.py              # RAG 文档问答
│   └── demo3_agent.py            # Agent 工具调用
├── learning/                     # 本学习文档
│   ├── README.md                 # 本文件 - 学习路线总览
│   ├── 01-demo1-gradio-chat.md   # Demo1 逐行讲解 + 练习
│   ├── 02-demo2-rag.md           # Demo2 逐行讲解 + 练习
│   └── 03-demo3-agent.md         # Demo3 逐行讲解 + 练习
├── esxi-llm-lab-guide.md         # 环境操作手册
└── ...
```

## 快速开始

```bash
# 1. SSH 到开发机
ssh llm2@192.168.2.16     # 密码: Admin123@pl

# 2. 运行 demo
cd ~/demos
python3 demo1_chat_ui.py   # 浏览器打开 http://192.168.2.16:7860

# 3. 修改代码练习
vi demo1_chat_ui.py        # 尝试修改后保存，刷新浏览器看效果
```

## 核心概念速查

```
┌─────────────────────────────────────────────────────────┐
│                    LLM 应用开发核心概念                      │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  用户提问 ──> Prompt ──> LLM (Ollama) ──> 回答           │
│                                                         │
│  Demo1: 用户 ──> Gradio UI ──> LangChain ──> Ollama     │
│                                                         │
│  Demo2: 用户 ──> 检索相关文档 ──> 文档+问题 ──> LLM ──> 回答│
│       (RAG: 先查资料再回答，减少幻觉)                        │
│                                                         │
│  Demo3: 用户 ──> Agent 思考 ──> 选择工具 ──> 执行 ──> 回答  │
│       (Agent: 能自主决定用什么工具来解决问题)                  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```
# ai-agent-study
