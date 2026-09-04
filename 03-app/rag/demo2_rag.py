"""
Demo 2: RAG 文档问答
=====================
用 LangChain + ChromaDB 实现检索增强生成 (RAG)。
流程: 加载文档 -> 文本分割 -> 向量化存储 -> 基于文档内容问答

用法:
    python3 demo2_rag.py
"""

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

OLLAMA_BASE = "http://192.168.2.15:11434/v1"

# ===== 1. 准备示例文档 =====
documents = [
    Document(page_content="""
    LLM推理学习环境介绍

    本环境部署在 VMware ESXi 6.7.0 主机上（IP: 192.168.2.14），包含两台虚拟机：

    VM1 - llm-inference（192.168.2.15）：
    - 配置：16 vCPU / 64GB RAM / 100GB 磁盘
    - 运行 Ollama v0.32.14，提供 LLM 推理 API
    - 已安装模型：qwen2.5:1.5b（986MB）和 qwen2.5:7b（4.7GB）
    - API 地址：http://192.168.2.15:11434
    - 注意：这是 CPU 推理，没有 GPU，建议使用小模型进行快速测试

    VM2 - llm-dev（192.168.2.16）：
    - 配置：8 vCPU / 32GB RAM / 80GB 磁盘
    - Python 3.10.12 开发环境
    - 已安装：JupyterLab 4.6.3、LangChain 1.3.18、Gradio 6.26.0、Streamlit 1.63.0
    - 向量数据库：ChromaDB 1.5.9、FAISS-CPU 1.15.0
    - 通过 OLLAMA_HOST 环境变量连接 VM1 的 Ollama API

    两台 VM 都存储在 data_sata 数据存储上（约 36TB，已用约 14TB）。
    """),
    Document(page_content="""
    Ollama 使用指南

    Ollama 是一个本地 LLM 推理引擎，通过 snap 安装在 VM1 上。

    常用命令：
    - ollama list：列出已安装的模型
    - ollama pull <model>：下载新模型
    - ollama run <model>：交互式对话
    - ollama rm <model>：删除模型

    API 端点：
    - GET /api/tags：列出模型
    - POST /api/generate：文本生成
    - POST /api/chat：对话补全
    - OpenAI 兼容接口：/v1

    配置参数（通过 snap set ollama）：
    - host=0.0.0.0：允许外部访问
    - num-parallel=2：并行请求数
    - keep-alive=10m：模型在内存中保持时间
    - max-loaded-models=2：最大同时加载模型数

    模型存储在 /var/snap/ollama/common/models/ 目录下。
    """),
    Document(page_content="""
    LangChain 开发入门

    LangChain 是一个用于构建 LLM 应用的框架，本环境已安装以下组件：

    核心包：
    - langchain 1.3.18：主框架
    - langchain-openai 1.6.0：OpenAI 兼容接口（用于连接 Ollama）
    - langchain-community 0.4.2：社区集成（ChromaDB、FAISS 等）

    连接 Ollama 的方式：
    ```python
    from langchain_openai import ChatOpenAI
    llm = ChatOpenAI(
        base_url="http://192.168.2.15:11434/v1",
        api_key="ollama",
        model="qwen2.5:7b"
    )
    ```

    RAG（检索增强生成）流程：
    1. 加载文档（TextLoader, PDFLoader 等）
    2. 文本分割（RecursiveCharacterTextSplitter）
    3. 向量化存储（ChromaDB.from_documents）
    4. 创建检索链（LCEL 方式组合 retriever + prompt + llm）
    5. 基于文档内容进行问答

    向量数据库选择：
    - ChromaDB：轻量级，适合开发测试，数据存储在本地目录
    - FAISS：Facebook 开源，检索速度快，适合大规模数据
    """),
]

# ===== 2. 文本分割 =====
print("正在分割文档...")
splitter = RecursiveCharacterTextSplitter(
    chunk_size=300,
    chunk_overlap=50,
    separators=["\n\n", "\n", "。", "，", " "]
)
chunks = splitter.split_documents(documents)
print(f"文档被分割为 {len(chunks)} 个片段")

# ===== 3. 向量化存储 =====
print("正在向量化并存储到 ChromaDB...")
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
print("向量化完成！")

# ===== 4. 用 LCEL 创建检索问答链 =====
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

# ===== 5. 问答测试 =====
questions = [
    "VM1 的 CPU 和内存配置是多少？",
    "Ollama 的 API 地址是什么？",
    "如何用 LangChain 连接 Ollama？",
    "ChromaDB 和 FAISS 有什么区别？",
]

print("\n" + "=" * 60)
print("RAG 文档问答 Demo")
print("=" * 60)

for q in questions:
    print(f"\n问题: {q}")
    answer = rag_chain.invoke(q)
    print(f"回答: {answer}")
    print("-" * 40)

print("\nDemo 完成！你可以修改 questions 列表来问更多问题。")
