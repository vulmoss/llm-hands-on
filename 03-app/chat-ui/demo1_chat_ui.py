"""
Demo 1: Gradio 聊天界面
========================
用 Gradio 搭建一个网页版聊天界面，连接 VM1 的 Ollama API。
启动后浏览器访问 http://192.168.2.16:7860

用法:
    python3 demo1_chat_ui.py
"""

import gradio as gr
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

OLLAMA_BASE = "http://192.168.2.15:11434/v1"

def build_llm(model="qwen2.5:7b"):
    return ChatOpenAI(
        base_url=OLLAMA_BASE,
        api_key="ollama",
        model=model,
        temperature=0.7,
    )

def chat(message, history, model_choice, system_prompt):
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
    description="连接本地 Ollama 的聊天机器人，支持切换模型和自定义系统提示词",
    additional_inputs=[
        gr.Radio(choices=["qwen2.5:1.5b", "qwen2.5:7b"], value="qwen2.5:7b", label="选择模型"),
        gr.Textbox(value="你是一个有帮助的AI助手，请用中文回答。", label="系统提示词", lines=2),
    ],
    examples=[["用简单的语言解释什么是机器学习"], ["写一首关于编程的诗"], ["Python 和 Java 有什么区别？"]],
)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
