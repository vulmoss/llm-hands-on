# AI 全栈极客学习路线

> 从基础设施到应用开发到安全攻防，系统掌握 LLM 全栈能力。
> 配套环境：VM1 (192.168.2.15) 提供 Ollama 推理，VM2 (192.168.2.16) 提供 Python 开发环境。

## 学习路线

```
01-infra         02-model         03-app           04-engineering      05-security        06-frontend
基础设施层   -->  模型层     -->   应用开发层   -->   工程化层      -->   AI 安全层    -->   前端展示层
                                                                                        
 ESXi + VM       模型选型         Demo1: 聊天      FastAPI 部署        Prompt 注入        Next.js
 Ollama 部署     量化原理         Demo2: RAG       Docker 容器化       数据泄露           流式输出
 网络配置        Embedding        Demo3: Agent     监控/日志           Agent 越权         多用户
```

## 目录结构

```
learning/
├── README.md                  # 本文件 - 学习路线总览
│
├── 01-infra/                  # 基础设施层（已完成）
│   ├── README.md
│   ├── esxi-lab-guide.md      # ESXi 环境操作手册
│   ├── llm-inference.vmx      # VM1 配置
│   └── llm-dev.vmx            # VM2 配置
│
├── 02-model/                  # 模型层（待补充）
│   └── README.md
│
├── 03-app/                    # 应用开发层（已完成 3 个 demo）
│   ├── README.md
│   ├── chat-ui/               # Demo1: Gradio 聊天界面
│   │   ├── README.md          # 逐行讲解 + 5 个练习
│   │   ├── app.py             # 学习用代码（含所有练习）
│   │   └── demo1_chat_ui.py   # 可运行完整代码
│   ├── rag/                   # Demo2: RAG 文档问答
│   │   ├── README.md
│   │   └── demo2_rag.py
│   └── agent/                 # Demo3: Agent 工具调用
│       ├── README.md
│       └── demo3_agent.py
│
├── 04-engineering/            # 工程化层（待补充）
│   └── README.md
│
├── 05-security/               # AI 安全层（待补充）
│   └── README.md
│
└── 06-frontend/               # 前端展示层（待补充）
    └── README.md
```

## 前置知识

| 知识点 | 需要程度 | 学习资源 |
|--------|----------|----------|
| Python 基础 | 必须 | 菜鸟教程 python3 |
| HTTP 请求 (GET/POST) | 必须 | 了解 REST API 概念 |
| JSON 数据格式 | 必须 | Python json 模块 |
| pip 包管理 | 必须 | `pip3 install xxx` |
| 类与对象 | 03-app 需要 | Python OOP 基础 |

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
┌──────────────────────────────────────────────────────────────┐
│                    LLM 应用开发核心概念                        │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  用户提问 ──> Prompt ──> LLM (Ollama) ──> 回答               │
│                                                              │
│  Demo1: 用户 ──> Gradio UI ──> LangChain ──> Ollama          │
│                                                              │
│  Demo2: 用户 ──> 检索相关文档 ──> 文档+问题 ──> LLM ──> 回答  │
│       (RAG: 先查资料再回答，减少幻觉)                          │
│                                                              │
│  Demo3: 用户 ──> Agent 思考 ──> 选择工具 ──> 执行 ──> 回答    │
│       (Agent: 能自主决定用什么工具来解决问题)                    │
│                                                              │
└──────────────────────────────────────────────────────────────┘
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

r = requests.get("http://192.168.2.15:11434/api/tags")
for model in r.json()["models"]:
    print(f"{model['name']}  大小: {model['size']/1e9:.1f}GB")
```

---

## 为什么 VM2 的 Python 能调用 VM1？

**核心原理：VM1 上的 Ollama 是一个 HTTP 服务，VM2 通过 HTTP 请求调用它。**

| 场景 | 客户端 | 请求 | 服务端 |
|------|--------|------|--------|
| 浏览网页 | 浏览器 | HTTP GET | Nginx/Apache |
| 调用 LLM | Python/LangChain | HTTP POST | Ollama |

```
VM2 (192.168.2.16)                    VM1 (192.168.2.15)
┌──────────────────┐                  ┌──────────────────────┐
│  Python 代码     │ ── HTTP POST ──> │  Ollama (端口 11434) │
│  LangChain       │                  │  加载模型 -> 推理     │
│                  │ <── HTTP 响应 ── │  生成回答             │
└──────────────────┘                  └──────────────────────┘
```

### 必须满足的 3 个前提条件

| 条件 | 当前状态 | 怎么验证 |
|------|---------|---------|
| 两台 VM 网络互通 | 都在 192.168.2.x 网段 | VM2 上 `ping 192.168.2.15` |
| Ollama 监听 0.0.0.0 | `snap set ollama host=0.0.0.0` | VM1 上 `sudo snap get ollama` |
| 端口没被防火墙拦截 | ESXi 内部网络默认全通 | VM2 上 `curl http://192.168.2.15:11434/api/tags` |
