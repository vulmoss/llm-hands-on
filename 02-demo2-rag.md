# Demo2: RAG 文档问答 - 逐行讲解

> 目标：让 AI 基于你提供的文档回答问题，而不是只靠模型自身的训练知识。
> 难度：中级 | 运行时间：~30秒（含向量化） | 涉及概念：Embedding、向量数据库、检索链

## 什么是 RAG？

RAG = Retrieval-Augmented Generation（检索增强生成）

```
没有 RAG:
  用户问: "VM1 的内存是多少？"
  LLM 回答: "我不知道，我的训练数据里没有你的环境信息"

有了 RAG:
  用户问: "VM1 的内存是多少？"
  步骤1: 从你的文档中检索出相关段落 → "VM1 - llm-inference: 16 vCPU / 64GB RAM"
  步骤2: 把检索到的段落 + 用户问题一起发给 LLM
  LLM 回答: "根据文档，VM1 的内存是 64GB"
```

**核心思想：** LLM 不擅长记住具体事实，但擅长阅读理解。RAG 把"回答问题"变成了"阅读理解题"。

---

## 运行方式

```bash
# 在 VM2 上运行
ssh llm2@192.168.2.16
cd ~/demos
python3 demo2_rag.py
```

---

## 完整代码逐段讲解

### 第一部分：导入模块

```python
import warnings
warnings.filterwarnings("ignore")

from langchain_openai import ChatOpenAI
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
```

**逐行解释：**

| 导入 | 作用 | 为什么需要 |
|------|------|-----------|
| `ChatOpenAI` | LLM 对话类 | 最终用来生成回答 |
| `OllamaEmbeddings` | 文本向量化 | 把文字变成数字向量，才能计算相似度 |
| `Chroma` | 向量数据库 | 存储和检索向量化的文档片段 |
| `RecursiveCharacterTextSplitter` | 文本分割器 | 把长文档切成小段，每段能独立检索 |
| `Document` | 文档对象 | LangChain 中文档的标准格式 |
| `PromptTemplate` | 提示词模板 | 构造发给 LLM 的格式化文本 |
| `RunnablePassthrough` | 数据透传 | LCEL 链式调用中传递原始数据 |
| `StrOutputParser` | 输出解析 | 把 LLM 返回的对象提取为纯字符串 |

**注意 import 路径的区别：**
- `langchain_openai`：OpenAI 兼容接口（独立包）
- `langchain_community`：社区维护的集成（Ollama、ChromaDB 等在这里）
- `langchain_text_splitters`：文本分割器（独立包，不在 langchain 主包里）
- `langchain_core`：核心基础类（所有包都依赖它）

---

### 第二部分：准备文档

```python
documents = [
    Document(page_content="""
    LLM推理学习环境介绍
    本环境部署在 VMware ESXi 6.7.0 主机上...
    """),
    Document(page_content="""
    Ollama 使用指南
    Ollama 是一个本地 LLM 推理引擎...
    """),
    Document(page_content="""
    LangChain 开发入门
    LangChain 是一个用于构建 LLM 应用的框架...
    """),
]
```

**关键概念：**

`Document` 是 LangChain 的文档对象，至少包含：
- `page_content`：文档的文本内容
- `metadata`：可选的元数据（来源、作者、页码等）

**为什么这里是 3 个 Document？** 实际项目中，你可能用 `TextLoader` 从文件加载：

```python
from langchain_community.document_loaders import TextLoader

loader = TextLoader("/path/to/file.txt")
documents = loader.load()  # 返回 Document 列表
```

也可以加载 PDF、网页、Markdown 等多种格式。

---

### 第三部分：文本分割（关键步骤）

```python
splitter = RecursiveCharacterTextSplitter(
    chunk_size=300,
    chunk_overlap=50,
    separators=["\n\n", "\n", "。", "，", " "]
)
chunks = splitter.split_documents(documents)
```

**为什么需要分割？**

1. LLM 有上下文长度限制（虽然 qwen2.5 支持 32K，但检索时不需要那么长）
2. 检索的粒度要小——整篇文档太粗糙，检索到的内容可能只有几句话相关
3. 向量数据库存储小片段更高效

**参数解释：**

| 参数 | 含义 | 为什么这样设 |
|------|------|-------------|
| `chunk_size=300` | 每个片段最多 300 个字符 | 太短丢失上下文，太长检索不精确 |
| `chunk_overlap=50` | 相邻片段重叠 50 个字符 | 防止一句话被从中间切断 |
| `separators` | 按什么字符切 | 优先按段落(\n\n)，其次按行(\n)，再按句子(。)，最后按词( ) |

**"Recursive" 的含义：** 分割器会依次尝试每个 separator，先按 `\n\n` 切，如果切出来还是太长，再按 `\n` 切，以此类推。

**直观理解分割效果：**

```
原始文档 (800字):
┌─────────────────────────────────────────────────┐
│ 段落1...段落2...段落3...段落4...段落5...         │
└─────────────────────────────────────────────────┘

分割后 (chunk_size=300, overlap=50):
┌──────────────┐
│ chunk 1      │
│ 段落1...段落2 │
└──────────────┘
     ^^^^^^ 重叠50字符
    ┌──────────────┐
    │ chunk 2      │
    │ 段落2...段落3 │
    └──────────────┘
         ^^^^^^ 重叠50字符
        ┌──────────────┐
        │ chunk 3      │
        │ 段落3...段落4 │
        └──────────────┘
```

---

### 第四部分：向量化存储（核心概念）

```python
embeddings = OllamaEmbeddings(
    model="all-minilm:33m",
    base_url="http://192.168.2.15:11434",
)
vectorstore = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    collection_name="llm_lab_docs",
)
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
```

**什么是 Embedding（向量化）？**

把文字变成一组数字（向量），使得：
- 意思相近的文字 → 向量距离近
- 意思不同的文字 → 向量距离远

```
"VM1 的内存" → [0.12, -0.34, 0.78, ..., 0.56]  (384维向量)
"服务器配置" → [0.11, -0.32, 0.75, ..., 0.54]  (距离很近！)
"今天天气"   → [-0.45, 0.67, -0.12, ..., 0.89]  (距离很远)
```

**all-minilm:33m 模型：**
- 33M 参数，只有 67MB
- 输出 384 维向量
- 速度快，适合 CPU 推理
- 英文效果好，中文一般（生产环境建议用多语言模型如 `nomic-embed-text`）

**ChromaDB 做了什么？**

```
ChromaDB 内部:
┌────────────────────────────────────────────────────┐
│ collection: "llm_lab_docs"                         │
│                                                    │
│  ID  │  向量 (384维)              │  原始文本       │
│  0   │  [0.12, -0.34, ...]       │  "VM1配置..."   │
│  1   │  [0.11, -0.32, ...]       │  "Ollama是..."  │
│  2   │  [-0.45, 0.67, ...]       │  "LangChain..." │
│  ... │  ...                      │  ...            │
└────────────────────────────────────────────────────┘
```

**`as_retriever(search_kwargs={"k": 3})` 的含义：**
- 把向量数据库转换为"检索器"
- `k=3` 表示每次检索返回最相似的 3 个片段

**检索过程：**

```
用户问: "VM1 的 CPU 是多少？"
    │
    v
Embedding 模型把问题变成向量: [0.13, -0.33, 0.77, ...]
    │
    v
在 ChromaDB 中计算与所有文档向量的相似度
    │
    v
返回最相似的 k=3 个文档片段:
  1. "VM1 - llm-inference: 16 vCPU / 64GB RAM" (相似度 0.92)
  2. "本环境部署在 ESXi 6.7.0 上" (相似度 0.78)
  3. "已安装模型: qwen2.5:1.5b 和 7b" (相似度 0.65)
```

---

### 第五部分：构建 LCEL 检索链

```python
llm = ChatOpenAI(
    base_url=OLLAMA_BASE,
    api_key="ollama",
    model="qwen2.5:7b",
    temperature=0,
)

prompt = PromptTemplate.from_template("""根据以下上下文信息回答问题。如果上下文中没有相关信息，就说"根据已有信息无法回答"。

上下文：
{context}

问题：{question}

回答：""")

rag_chain = (
    {"context": retriever, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)
```

**LCEL（LangChain Expression Language）是什么？**

LCEL 是 LangChain 的"管道"语法，用 `|` 把多个组件串联起来，数据从左到右流动。

**逐步拆解 rag_chain 的数据流：**

```
用户输入: "VM1 的 CPU 是多少？"
    │
    v
步骤1: {"context": retriever, "question": RunnablePassthrough()}
    │
    │  retriever 检索文档 → "VM1: 16 vCPU / 64GB RAM..."
    │  RunnablePassthrough 原样传递问题
    │
    │  输出: {"context": "检索到的文档内容", "question": "VM1的CPU是多少？"}
    │
    v
步骤2: prompt (PromptTemplate)
    │
    │  把 context 和 question 填入模板
    │
    │  输出: "根据以下上下文信息回答问题...\n上下文：VM1: 16 vCPU...\n问题：VM1的CPU是多少？"
    │
    v
步骤3: llm (ChatOpenAI)
    │
    │  发给 Ollama 的 qwen2.5:7b 模型
    │
    │  输出: AIMessage(content="VM1 配备了 16 个 vCPU")
    │
    v
步骤4: StrOutputParser()
    │
    │  从 AIMessage 对象中提取纯文本
    │
    │  输出: "VM1 配备了 16 个 vCPU"
    │
    v
最终结果返回给用户
```

**为什么 temperature=0？** RAG 场景需要准确的回答，不需要创造性。设为 0 让模型每次给出最确定的答案。

---

### 第六部分：问答测试

```python
questions = [
    "VM1 的 CPU 和内存配置是多少？",
    "Ollama 的 API 地址是什么？",
    "如何用 LangChain 连接 Ollama？",
    "ChromaDB 和 FAISS 有什么区别？",
]

for q in questions:
    print(f"\n问题: {q}")
    answer = rag_chain.invoke(q)
    print(f"回答: {answer}")
```

`rag_chain.invoke(q)` 是 LCEL 链的统一调用方式。传入字符串，经过整个管道处理，返回最终字符串。

---

## 数据流全景图

```
                        RAG 完整流程

  文档准备阶段（只执行一次）:
  ┌──────────┐    ┌──────────┐    ┌──────────────┐    ┌──────────┐
  │ 原始文档  │──>│ 文本分割  │──>│ Embedding    │──>│ ChromaDB │
  │ (3篇)    │    │ (15+段)  │    │ 向量化       │    │ 存储向量  │
  └──────────┘    └──────────┘    └──────────────┘    └──────────┘

  问答阶段（每次提问）:
  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
  │ 用户问题  │──>│ 检索相关  │──>│ 组装提示词 │──>│ LLM 生成 │
  │          │    │ 文档片段  │    │ 填入模板   │    │ 回答     │
  └──────────┘    └──────────┘    └──────────┘    └──────────┘
                       │                               │
                       v                               v
                  ChromaDB                        Ollama API
                  相似度检索                       qwen2.5:7b
```

---

## 动手练习

### 练习 1：调整分割参数（难度：★）

**目标：** 观察 chunk_size 对分割结果和回答质量的影响。

**操作：** 修改分割参数，打印分割结果：

```python
splitter = RecursiveCharacterTextSplitter(
    chunk_size=100,   # 改小，看看会分成多少段
    chunk_overlap=20,
)
chunks = splitter.split_documents(documents)
print(f"chunk_size=100 时: {len(chunks)} 个片段")

for i, chunk in enumerate(chunks):
    print(f"\n--- 片段 {i+1} ({len(chunk.page_content)} 字) ---")
    print(chunk.page_content[:100] + "...")
```

**思考：**
- chunk_size=100 和 chunk_size=300 分别产生多少片段？
- 片段太小会丢失什么？太大会出什么问题？

---

### 练习 2：加载真实文件（难度：★★）

**目标：** 从实际文件中加载文档，而不是硬编码字符串。

**步骤 1：** 在 VM2 上创建一个文本文件：

```bash
cat > ~/demos/my_knowledge.txt << 'EOF'
Python 编程技巧

列表推导式:
squares = [x**2 for x in range(10)]
这是 Python 中最优雅的特性之一。

字典推导式:
word_lengths = {word: len(word) for word in ["hello", "world"]}

生成器表达式:
total = sum(x**2 for x in range(1000))
使用圆括号而不是方括号，节省内存。

装饰器:
def timer(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        print(f"{func.__name__} took {time.time()-start:.2f}s")
        return result
    return wrapper
EOF
```

**步骤 2：** 修改 demo2_rag.py，用 TextLoader 加载：

```python
from langchain_community.document_loaders import TextLoader

loader = TextLoader("~/demos/my_knowledge.txt")
documents = loader.load()
```

**步骤 3：** 运行并提问：

```python
questions = [
    "什么是列表推导式？",
    "装饰器怎么用？",
    "生成器和列表推导式有什么区别？",
]
```

---

### 练习 3：对比不同检索数量 k（难度：★★）

**目标：** 观察 k 值对回答质量的影响。

**操作：** 创建两个 retriever，一个 k=1，一个 k=5：

```python
retriever_k1 = vectorstore.as_retriever(search_kwargs={"k": 1})
retriever_k5 = vectorstore.as_retriever(search_kwargs={"k": 5})

# 手动检索看看返回了什么
query = "VM1 的配置"
print("k=1 检索结果:")
for doc in retriever_k1.invoke(query):
    print(f"  - {doc.page_content[:80]}...")

print("\nk=5 检索结果:")
for doc in retriever_k5.invoke(query):
    print(f"  - {doc.page_content[:80]}...")
```

**思考：** k 越大越好吗？什么情况下 k 大会反而降低回答质量？

---

### 练习 4：添加来源追踪（难度：★★★）

**目标：** 让 RAG 回答时标注引用了哪段文档。

**思路：** 使用 `return_source_documents=True` 或手动构建链：

```python
from langchain_core.runnables import RunnableMap

# 同时返回回答和来源
rag_chain_with_sources = RunnableMap(
    {"context": retriever, "question": RunnablePassthrough()}
) | RunnableMap(
    answer=lambda x: (prompt | llm | StrOutputParser()).invoke(x),
    sources=lambda x: [doc.metadata.get("source", "未知") for doc in x["context"]]
)

result = rag_chain_with_sources.invoke("VM1 的内存是多少？")
print(f"回答: {result['answer']}")
print(f"来源: {result['sources']}")
```

---

### 练习 5：用 FAISS 替换 ChromaDB（难度：★★）

**目标：** 对比两种向量数据库的使用方式和效果。

```python
from langchain_community.vectorstores import FAISS

# 只需要换一行代码
vectorstore = FAISS.from_documents(
    documents=chunks,
    embedding=embeddings,
)

# 其他代码完全不变！
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
```

**思考：** ChromaDB 和 FAISS 的 API 为什么可以无缝替换？（提示：它们都实现了相同的接口）

**FAISS 的特点：**
- Facebook 开源，C++ 底层，速度更快
- 不支持持久化（需要额外保存/加载）
- 适合大规模数据的快速检索

---

## 核心概念速查表

| 概念 | 一句话解释 | 类比 |
|------|-----------|------|
| Embedding | 把文字变成数字向量 | 把书的内容变成GPS坐标，相似的书坐标相近 |
| 向量数据库 | 存储和检索向量的数据库 | 一个能按"意思相似度"搜索的搜索引擎 |
| Text Splitter | 把长文档切成小段 | 把一本书拆成一个个段落卡片 |
| Retriever | 根据问题检索相关文档 | 图书管理员根据你的问题找到最相关的几页 |
| LCEL | LangChain 的管道语法 | 流水线：原料 → 加工1 → 加工2 → 成品 |
| RAG | 先检索再生成 | 开卷考试：先翻书找答案，再组织语言回答 |

---

## 常见问题

**Q: 为什么用 OllamaEmbeddings 而不是 OpenAIEmbeddings？**
A: OpenAIEmbeddings 调用的是 OpenAI 的 embedding API，需要付费且需要外网。OllamaEmbeddings 调用本地的 Ollama，免费且无需外网。

**Q: all-minilm:33m 对中文效果好吗？**
A: 一般。它是英文为主的模型。中文场景建议用 `nomic-embed-text` 或 `bge-m3` 等多语言 embedding 模型。

**Q: ChromaDB 的数据存在哪里？**
A: 默认存在内存中（程序结束就消失）。如果要持久化：
```python
vectorstore = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    persist_directory="./chroma_db",  # 保存到本地目录
)
```

**Q: 文档更新后需要重新向量化吗？**
A: 是的。如果文档内容变了，需要重新执行分割和向量化。生产环境通常会做增量更新。

**Q: 检索到的内容不相关怎么办？**
A: 几个排查方向：
1. embedding 模型不适合你的语言（换中文模型）
2. chunk_size 太大或太小（调整分割参数）
3. k 值不合适（增大或减小检索数量）
4. 文档本身质量不高（清洗数据）
