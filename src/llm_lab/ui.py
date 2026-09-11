"""可选 Gradio 入口：仅导入本模块不需要安装 Gradio。"""

from .chat import DEFAULT_SYSTEM, build_messages
from .client import OllamaClient, OllamaError
from .config import Settings


def create_ui(settings: Settings, client=None):
    import gradio as gr

    client = client or OllamaClient(settings)

    def respond(message, history, system):
        try:
            messages = build_messages(message, history, system, settings.history_turns)
            answer = ""
            for part in client.stream(messages):
                answer += part
                yield answer
        except (OllamaError, ValueError) as exc:
            raise gr.Error(str(exc)) from exc

    return gr.ChatInterface(
        fn=respond,
        title="LLM 学习实验室",
        description=f"模型：{settings.model} · 流式对话 · 最近 {settings.history_turns} 轮上下文",
        additional_inputs=[gr.Textbox(value=DEFAULT_SYSTEM, label="系统提示词", lines=2)],
        additional_inputs_accordion="对话设置",
        examples=[
            ["用一个例子解释什么是 Token", DEFAULT_SYSTEM],
            ["我正在学习 Python，请给我一道函数练习题", DEFAULT_SYSTEM],
        ],
        cache_examples=False,
        api_name="chat",
        save_history=True,
    )


def launch(settings: Settings, host: str = "127.0.0.1", port: int = 7860):
    create_ui(settings).launch(server_name=host, server_port=port)
