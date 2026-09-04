"""
01-demo1-gradio-chat.py
=======================
从 01-demo1-gradio-chat.md 中提取的所有 Python 代码。
包含：主代码（可直接运行）+ 5 个练习的参考代码。

主代码运行: python3 01-demo1-gradio-chat.py
练习代码: 取消对应注释块即可运行
"""

import warnings
warnings.filterwarnings("ignore")

# ============================================================
# 主代码：Gradio 聊天界面（对应文档第一部分 ~ 第四部分）
# ============================================================

import gradio as gr
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

OLLAMA_BASE = "http://192.168.2.15:11434/v1"


def build_llm(model="qwen2.5:7b"):
    """根据模型名称创建 LLM 实例。"""
    return ChatOpenAI(
        base_url=OLLAMA_BASE,
        api_key="ollama",
        model=model,
        temperature=0.7,
    )


def chat(message, history, model_choice, system_prompt):
    """核心对话函数：构建消息列表 -> 调用 LLM -> 返回回答。"""
    llm = build_llm(model=model_choice)

    messages = []
    if system_prompt:
        messages.append(SystemMessage(content=system_prompt))

    for msg in history:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            messages.append(AIMessage(content=msg["content"]))

    messages.append(HumanMessage(content=message))

    response = llm.invoke(messages)
    return response.content


demo = gr.ChatInterface(
    fn=chat,
    title="LLM Chat - Ollama + LangChain",
    description="连接本地 Ollama 的聊天机器人",
    additional_inputs=[
        gr.Radio(choices=["qwen2.5:1.5b", "qwen2.5:7b"],
                 value="qwen2.5:7b", label="选择模型"),
        gr.Textbox(value="你是一个有帮助的AI助手，请用中文回答。",
                   label="系统提示词", lines=2),
    ],
    examples=[["用简单的语言解释什么是机器学习"], ["写一首关于编程的诗"]],
)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)


# ============================================================
# 练习 1：修改默认模型（难度：★）
# 把 value="qwen2.5:7b" 改为 value="qwen2.5:1.5b"
# ============================================================

# 找到 ChatInterface 中的 gr.Radio，修改 value：
#
# gr.Radio(choices=["qwen2.5:1.5b", "qwen2.5:7b"],
#          value="qwen2.5:1.5b", label="选择模型")   # <-- 改这里


# ============================================================
# 练习 2：添加流式输出（难度：★★）
# 把 chat() 函数改为 yield 生成器，实现逐字显示
# ============================================================

def chat_stream(message, history, model_choice, system_prompt):
    """流式输出版本的 chat 函数。"""
    llm = build_llm(model=model_choice)

    messages = []
    if system_prompt:
        messages.append(SystemMessage(content=system_prompt))

    for msg in history:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            messages.append(AIMessage(content=msg["content"]))

    messages.append(HumanMessage(content=message))

    full_response = ""
    for chunk in llm.stream(messages):
        full_response += chunk.content
        yield full_response


# ============================================================
# 练习 3：添加角色设定（难度：★★）
# 预设角色，用户选择后 AI 以该角色身份回答
# ============================================================

role_prompts = {
    "通用助手": "你是一个有帮助的AI助手。",
    "Python老师": "你是一个Python编程老师，用简单易懂的方式教学。",
    "段子手": "你是一个幽默的段子手，用搞笑的方式回答问题。",
    "诗人": "你是一个诗人，尽量用诗意的语言回答。",
}

# 在 additional_inputs 中添加：
# gr.Dropdown(
#     choices=["通用助手", "Python老师", "段子手", "诗人"],
#     value="通用助手",
#     label="选择角色"
# )

# 在 chat() 函数开头根据角色选择设置 system_prompt：
# system_prompt = role_prompts[role_choice]


# ============================================================
# 练习 4：添加对话历史持久化（难度：★★★）
# 刷新页面后对话历史不丢失
# ============================================================

import json

HISTORY_FILE = "/tmp/chat_history.json"

def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f)

def load_history():
    try:
        with open(HISTORY_FILE) as f:
            return json.load(f)
    except FileNotFoundError:
        return []


# ============================================================
# 练习 5：不用 LangChain，直接调用 Ollama API（难度：★★）
# 理解 LangChain 底层到底做了什么
# ============================================================

import requests

def chat_direct(message, history):
    """绕过 LangChain，直接用 requests 调用 Ollama 的 /api/chat 接口。"""
    messages = []
    for msg in history:
        if msg["role"] == "user":
            messages.append({"role": "user", "content": msg["content"]})
        elif msg["role"] == "assistant":
            messages.append({"role": "assistant", "content": msg["content"]})
    messages.append({"role": "user", "content": message})

    response = requests.post(
        "http://192.168.2.15:11434/api/chat",
        json={"model": "qwen2.5:7b", "messages": messages, "stream": False}
    )
    return response.json()["message"]["content"]


# 测试直接调用（不依赖 Gradio）
if __name__ == "__main__":
    print("=== 练习5测试：直接调用 Ollama API ===")
    result = chat_direct("你好，请用一句话介绍自己", [])
    print(f"回答: {result}")
