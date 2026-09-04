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
│   └── day1/
│       ├── 01-demo1-gradio-chat.md   # Demo1 逐行讲解 + 练习
│       ├── 01-demo1-gradio-chat.py   # Demo1 提取的完整 Python 代码
│       ├── 02-demo2-rag.md           # Demo2 逐行讲解 + 练习
│       └── 03-demo3-agent.md         # Demo3 逐行讲解 + 练习
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

---

## 查询 VM1 上 Ollama 模型状态

### 方法 1：SSH 到 VM1 用命令行

```bash
ssh llm1@192.168.2.15     # 密码: Admin123@pl

# 列出已安装的模型
ollama list

# 查看正在运行的模型（加载到内存中的）
ollama ps

# 查看某个模型的详细信息（参数量、量化方式、上下文长度等）
ollama show qwen2.5:7b
```

### 方法 2：通过 HTTP API 远程查询（从 VM2 或任何机器）

Ollama 启动后监听 HTTP 端口，可以直接用 curl 查询：

```bash
# 列出所有模型
curl http://192.168.2.15:11434/api/tags

# 查看当前加载到内存的模型
curl http://192.168.2.15:11434/api/ps

# 查看 Ollama 版本
curl http://192.168.2.15:11434/api/version
```

### 方法 3：用 Python 查询

```python
import requests

# 列出模型
r = requests.get("http://192.168.2.15:11434/api/tags")
for model in r.json()["models"]:
    print(f"{model['name']}  大小: {model['size']/1e9:.1f}GB")
```

---

## 为什么 VM2 的 Python 能调用 VM1？

**核心原理：VM1 上的 Ollama 是一个 HTTP 服务，VM2 通过 HTTP 请求调用它。**

这和你在浏览器里访问网页是同一回事：

| 场景 | 客户端 | 请求 | 服务端 |
|------|--------|------|--------|
| 浏览网页 | 浏览器 | HTTP GET | Nginx/Apache |
| 调用 LLM | Python/LangChain | HTTP POST | Ollama |

浏览器发请求给 Web 服务器，Web 服务器返回 HTML 页面。
Python 发请求给 Ollama，Ollama 返回 AI 生成的文字。

### 数据流

```
VM2 (192.168.2.16)                    VM1 (192.168.2.15)
┌──────────────────┐                  ┌──────────────────────┐
│                  │   HTTP 请求      │                      │
│  Python 代码     │ ──────────────>  │  Ollama (端口 11434) │
│  LangChain       │   192.168.2.15   │                      │
│                  │   :11434/v1      │  加载模型 -> 推理     │
│                  │ <──────────────  │  生成回答             │
│                  │   HTTP 响应      │                      │
└──────────────────┘                  └──────────────────────┘
```

### 代码层面到底发生了什么

```python
# VM2 上写的这行代码：
llm = ChatOpenAI(
    base_url="http://192.168.2.15:11434/v1",  # 指向 VM1 的地址
    api_key="ollama",
    model="qwen2.5:7b",
)

# 当调用 llm.invoke("你好") 时，底层实际执行的是：
requests.post(
    "http://192.168.2.15:11434/v1/chat/completions",  # HTTP POST 到 VM1
    json={
        "model": "qwen2.5:7b",
        "messages": [{"role": "user", "content": "你好"}]
    }
)
# VM1 收到请求 -> 加载模型 -> CPU 推理 -> 返回文字
```

LangChain 的 `ChatOpenAI` 只是帮你封装了 HTTP 请求的构造过程。

### 必须满足的 3 个前提条件

| 条件 | 当前状态 | 怎么验证 |
|------|---------|---------|
| 两台 VM 网络互通 | 都在 192.168.2.x 网段 | VM2 上 `ping 192.168.2.15` |
| Ollama 监听 0.0.0.0（不只 localhost） | `snap set ollama host=0.0.0.0` | VM1 上 `sudo snap get ollama` |
| 端口没被防火墙拦截 | ESXi 内部网络默认全通 | VM2 上 `curl http://192.168.2.15:11434/api/tags` |

如果任何一个条件不满足，VM2 就连不上 VM1。
