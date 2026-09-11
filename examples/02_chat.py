"""第二个练习：显式传入历史，观察第二轮请求。"""

from llm_lab.chat import build_messages
from llm_lab.client import OllamaClient
from llm_lab.config import Settings


def main():
    client = OllamaClient(Settings.from_env())
    messages = build_messages("我正在学习 Python。")
    answer = client.chat(messages)
    history = [messages[-1], answer]
    second = build_messages("我正在学习什么？", history)
    print("第二轮请求：", second)
    print("第二轮回答：", client.chat(second)["content"])


if __name__ == "__main__":
    main()
