# 03 - 应用开发层

> 用 LangChain 构建 LLM 应用。从最简单的聊天到自主决策的 Agent，掌握三种核心应用模式。
> 配套环境：VM2 (192.168.2.16) Python 开发环境，连接 VM1 的 Ollama API。

## 学习路线

```
Demo1 (入门)              Demo2 (进阶)              Demo3 (高级)
Gradio 聊天界面      -->  RAG 文档问答        -->  Agent 工具调用
                                                       
你写了什么:            你写了什么:               你写了什么:
  LLM 调用              文档加载/分割              工具函数定义
  消息构建              Embedding 向量化           Agent 创建
  Gradio UI            向量数据库存储             测试多步推理
  多轮对话              LCEL 检索链               
                                                       
你学到了什么:           你学到了什么:              你学到了什么:
  LLM 是 HTTP 服务      文本可以变成向量           AI 可以自主决策
  对话 = 消息列表       相似度检索找到相关内容      工具 = AI 的"手"
  Web UI 只是壳         先查再生成 = RAG           ReAct = 思考+行动
```

## 目录

| Demo | 目录 | 核心概念 | 难度 | 学习时间 |
|------|------|----------|------|---------|
| Demo1: 聊天界面 | `chat-ui/` | LLM API、多轮对话、Gradio Web UI | 入门 | 1-2 小时 |
| Demo2: RAG 问答 | `rag/` | Embedding、向量数据库、检索增强生成 | 中级 | 2-3 小时 |
| Demo3: Agent | `agent/` | 工具定义、ReAct 模式、自主决策 | 中级 | 2-3 小时 |

## 每个 Demo 的文件

```
chat-ui/
├── README.md           # 逐行讲解 + 5 个练习
├── app.py              # 提取的学习用代码（含所有练习）
└── demo1_chat_ui.py    # 可直接运行的完整代码

rag/
├── README.md           # 逐行讲解 + 5 个练习
└── demo2_rag.py        # 可直接运行的完整代码

agent/
├── README.md           # 逐行讲解 + 5 个练习
└── demo3_agent.py      # 可直接运行的完整代码
```

## 运行方式

```bash
# SSH 到 VM2
ssh llm2@192.168.2.16     # 密码: Admin123@pl

# 运行任意 demo
cd ~/demos
python3 demo1_chat_ui.py   # 聊天界面 → http://192.168.2.16:7860
python3 demo2_rag.py       # RAG 问答（命令行输出）
python3 demo3_agent.py     # Agent 工具调用（命令行输出）
```

---

## Demo1: Gradio 聊天界面

> 最基础的 LLM 应用：用户输入 → LLM 处理 → 返回回答。

### 核心知识点

| 知识点 | 说明 | 对应代码 |
|--------|------|---------|
| LLM 是 HTTP 服务 | ChatOpenAI 底层是 HTTP POST 请求 | `llm.invoke(messages)` |
| 消息格式 | SystemMessage / HumanMessage / AIMessage | `messages = [...]` |
| 多轮对话 | LLM 没有记忆，靠 history 参数传递上下文 | `for msg in history:` |
| Temperature | 控制输出随机性：0=确定，1=创意 | `ChatOpenAI(temperature=0.7)` |
| Gradio UI | 一个 Python 函数自动生成 Web 界面 | `gr.ChatInterface(fn=chat)` |

### 数据流

```
浏览器                    VM2                              VM1
┌──────┐                 ┌────────────┐                   ┌──────────┐
│ 用户  │──HTTP──>       │ Gradio      │                   │          │
│ 输入  │                │   ↓         │                   │          │
│      │                │ chat()      │                   │          │
│      │                │   ↓         │──HTTP POST──>    │ Ollama   │
│      │                │ llm.invoke  │  /v1/chat/...     │ qwen2.5  │
│      │                │   ↓         │<──HTTP 响应──     │          │
│ 显示  │<──HTTP──       │ return 回答 │                   │          │
└──────┘                └────────────┘                   └──────────┘
```

### 学习步骤

1. **读** `chat-ui/README.md` — 逐行理解代码
2. **跑** `python3 demo1_chat_ui.py` — 浏览器打开体验
3. **改** 尝试练习 1（换默认模型）和练习 2（流式输出）
4. **深入** 做练习 5（不用 LangChain，直接调 Ollama API）— 理解底层

### 关键理解

**Gradio 6.x 的 history 格式：**
```python
# 不是旧版的元组: [("你好", "你好！")]
# 而是字典列表:
[
    {"role": "user", "content": "你好"},
    {"role": "assistant", "content": "你好！"}
]
```

---

## Demo2: RAG 文档问答

> 让 AI 基于你的文档回答问题，而不是只靠训练知识。这是企业级 LLM 应用最常见的模式。

### 核心知识点

| 知识点 | 说明 | 对应代码 |
|--------|------|---------|
| Document 对象 | LangChain 的文档标准格式 | `Document(page_content="...")` |
| 文本分割 | 长文档切成小段，提高检索精度 | `RecursiveCharacterTextSplitter` |
| Embedding | 文字 → 数字向量，语义相近 = 向量距离近 | `OllamaEmbeddings(model="all-minilm:33m")` |
| 向量数据库 | 存储和检索向量 | `Chroma.from_documents(...)` |
| Retriever | 根据问题检索最相关的文档片段 | `vectorstore.as_retriever(k=3)` |
| LCEL 链 | LangChain 的管道语法，用 `|` 串联组件 | `rag_chain = {...} \| prompt \| llm \| parser` |

### 数据流

```
准备阶段（只执行一次）:
┌────────┐    ┌────────┐    ┌───────────┐    ┌──────────┐
│ 文档    │──>│ 分割    │──>│ Embedding │──>│ ChromaDB │
│ 3 篇   │    │ 15+ 段  │    │ 向量化    │    │ 存储     │
└────────┘    └────────┘    └───────────┘    └──────────┘

问答阶段（每次提问）:
┌────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ 用户问题│──>│ 检索文档  │──>│ 组装提示词│──>│ LLM 生成 │
│        │    │ top-k 相似│    │ 填入模板  │    │ 回答     │
└────────┘    └──────────┘    └──────────┘    └──────────┘
```

### LCEL 链详解

这是 Demo2 最核心的代码，也是最难理解的部分：

```python
rag_chain = (
    {"context": retriever, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)
```

**数据在管道中的流动：**

```
输入: "VM1 的 CPU 是多少？"
  │
  ├─ retriever → 检索到 "VM1: 16 vCPU / 64GB RAM"
  ├─ RunnablePassthrough → 原样传递问题
  │
  ↓ {"context": "VM1: 16 vCPU...", "question": "VM1的CPU是多少？"}
  │
  ↓ prompt 填入模板 → "根据以下上下文回答问题...\n上下文：VM1: 16 vCPU...\n问题：..."
  │
  ↓ llm 推理 → AIMessage(content="VM1 配备了 16 个 vCPU")
  │
  ↓ StrOutputParser → "VM1 配备了 16 个 vCPU"
  │
  ↓ 返回给用户
```

### 学习步骤

1. **读** `rag/README.md` — 理解 RAG 原理和每个组件
2. **跑** `python3 demo2_rag.py` — 观察 4 个问答
3. **改** 练习 1（调 chunk_size）和练习 2（加载真实文件）
4. **深入** 练习 5（用 FAISS 替换 ChromaDB）— 理解向量数据库接口抽象

### 关键理解

**RAG 解决了什么问题？**

```
没有 RAG:
  用户: "VM1 的内存是多少？"
  LLM: "我不知道，我的训练数据里没有你的环境信息"

有了 RAG:
  用户: "VM1 的内存是多少？"
  步骤1: 检索 → "VM1 - llm-inference: 16 vCPU / 64GB RAM"
  步骤2: 把检索结果 + 问题一起发给 LLM
  LLM: "根据文档，VM1 的内存是 64GB"
```

**RAG = 开卷考试。** LLM 不擅长记住具体事实，但擅长阅读理解。RAG 把"回答问题"变成"阅读理解题"。

---

## Demo3: Agent 工具调用

> 让 AI 不仅能聊天，还能"动手做事"——调用计算器、查知识库、做单位转换。

### 核心知识点

| 知识点 | 说明 | 对应代码 |
|--------|------|---------|
| @tool 装饰器 | 把 Python 函数变成 Agent 可调用的工具 | `@tool def calculator(...)` |
| Docstring = 工具描述 | Agent 靠 docstring 理解工具能做什么 | `"""计算数学表达式..."""` |
| ReAct 模式 | Reasoning + Acting，思考→行动→观察→循环 | `create_react_agent(...)` |
| 多步推理 | Agent 可以连续调用多个工具解决复杂问题 | 先 calculator 再 unit_converter |
| LangGraph | Agent 的状态管理和流转 | `langgraph.prebuilt` |

### Agent 决策流程

```
用户: "计算 (15+27)*3-18，然后把结果从 km 转成 miles"
  │
  v
┌─────────────────┐
│ Agent 思考       │ "需要计算，用 calculator"
│ (Reason)        │
└────────┬────────┘
         │
         v
┌─────────────────┐
│ 调用 calculator  │ → 返回 "72"
│ (Act)           │
└────────┬────────┘
         │
         v
┌─────────────────┐
│ Agent 观察       │ "结果是 72，还需要转单位"
│ (Observe)       │
└────────┬────────┘
         │
         v
┌─────────────────┐
│ 调用 converter   │ → 返回 "72 km = 44.74 miles"
│ (Act)           │
└────────┬────────┘
         │
         v
┌─────────────────┐
│ Agent 总结       │ "结果是 44.74 英里"
│ (Final Answer)  │
└─────────────────┘
```

### 工具定义三要素

```python
@tool                                          # 1. 装饰器标记
def calculator(expression: str) -> str:        # 2. 参数类型注解
    """计算数学表达式..."""                      # 3. Docstring 描述（最重要！）
    ...
    return f"{expression} = {result}"          # 4. 返回字符串
```

| 要素 | Agent 怎么用 | 写错了会怎样 |
|------|-------------|-------------|
| `@tool` | 注册为可用工具 | 函数不会被 Agent 发现 |
| 参数类型注解 | 知道该传什么类型的参数 | 参数类型错误，工具调用失败 |
| Docstring | **判断什么时候该用这个工具** | Agent 不知道工具能做什么，选错或不用 |
| 返回字符串 | 读取结果用于下一步推理 | Agent 无法理解返回值 |

### 学习步骤

1. **读** `agent/README.md` — 理解 ReAct 和工具定义
2. **跑** `python3 demo3_agent.py` — 观察 Agent 如何选择工具
3. **改** 练习 1（添加天气工具）和练习 2（添加时间工具）
4. **深入** 练习 5（打印 Agent 完整推理过程）— 理解内部消息流转

### 关键理解

**Agent vs 普通 LLM：**

```
普通 LLM:
  用户: "123 * 456 = ?"
  LLM: "56088"  ← 可能算错！LLM 不擅长精确计算

Agent:
  用户: "123 * 456 = ?"
  Agent 思考: "需要精确计算" → 调用 calculator("123 * 456")
  工具返回: "56088"
  Agent: "123 × 456 = 56088"  ← 100% 准确
```

---

## 三个 Demo 的对比

| 维度 | Demo1: 聊天 | Demo2: RAG | Demo3: Agent |
|------|-----------|-----------|-------------|
| 输入 | 用户问题 | 用户问题 + 文档 | 用户问题 |
| 处理 | 直接发给 LLM | 先检索文档，再发给 LLM | LLM 自主决定调用什么工具 |
| 输出 | LLM 直接回答 | 基于文档的回答 | 工具结果 + LLM 总结 |
| 知识来源 | LLM 训练数据 | 你提供的文档 | 工具返回的结果 |
| 复杂度 | 低 | 中 | 中高 |
| 适用场景 | 日常对话 | 企业知识库问答 | 需要执行操作的自动化 |
| 核心组件 | ChatOpenAI | ChromaDB + Retriever | @tool + create_react_agent |

## 跨 Demo 的核心概念

这三个 Demo 共享一些基础概念，理解一次就够了：

| 概念 | Demo1 | Demo2 | Demo3 |
|------|-------|-------|-------|
| ChatOpenAI | 直接调用 | 检索链的最后一步 | Agent 的大脑 |
| Ollama API | /v1/chat/completions | /v1/embeddings + /v1/chat | /v1/chat + tool calling |
| 消息格式 | HumanMessage/AIMessage | PromptTemplate 生成 | Agent 内部管理 |
| LangChain | 封装 HTTP 请求 | LCEL 管道语法 | Agent 框架 |

## 学习建议

### 推荐顺序

```
第 1 天: Demo1（1-2 小时）
  → 读 README → 跑代码 → 做练习 1、2、5
  → 目标：理解 LLM 调用和多轮对话

第 2 天: Demo2（2-3 小时）
  → 读 README → 跑代码 → 做练习 1、2
  → 目标：理解 RAG 流程和向量检索

第 3 天: Demo3（2-3 小时）
  → 读 README → 跑代码 → 做练习 1、2、5
  → 目标：理解 Agent 决策和工具定义

第 4 天: 综合练习
  → 把 Demo1 的 Gradio UI 和 Demo2 的 RAG 结合
  → 做一个有 Web 界面的 RAG 问答系统
```

### 综合练习 ideas

完成三个 Demo 后，尝试把这些能力组合起来：

| 项目 | 组合 | 难度 |
|------|------|------|
| RAG 聊天界面 | Demo1 + Demo2 | 中 |
| 带工具的聊天界面 | Demo1 + Demo3 | 中 |
| 完整 RAG+Agent 系统 | Demo1 + Demo2 + Demo3 | 高 |
| 多文档 RAG（PDF/网页） | Demo2 扩展 | 中 |
| 自定义知识库 Agent | Demo3 扩展 | 中 |

### 常见问题

**Q: Demo1 的 Gradio 界面刷新后对话丢失？**
A: Gradio 的 ChatInterface 默认不持久化 history。参考 Demo1 练习 4 实现 JSON 文件持久化。

**Q: Demo2 检索到的文档不相关？**
A: 三个排查方向：1) Embedding 模型不适合中文（换 nomic-embed-text）2) chunk_size 太大或太小 3) k 值不合适

**Q: Demo3 Agent 选错了工具？**
A: 小模型（7b）有时会选错。改善方法：1) 让 docstring 更明确 2) 减少工具数量 3) 用更大的模型

**Q: 这三个 Demo 哪个在工作中最常用？**
A: Demo2 (RAG) 是目前企业级 LLM 应用最常见的模式。几乎所有"基于公司内部文档问答"的需求都是 RAG。
