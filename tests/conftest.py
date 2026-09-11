from types import SimpleNamespace

import pytest


class FakeClient:
    def __init__(self, replies=None):
        self.settings = SimpleNamespace(
            embedding_model="test-embed", model="test-chat", temperature=0, max_tokens=512
        )
        self.replies = list(replies or [{"role": "assistant", "content": "根据资料回答 [1]"}])
        self.requests = []

    def embed(self, texts):
        # 刻意简单且确定，测试排序流程，不冒充模型的语义能力。
        return [[1.0, 0.0] if "Python" in text else [0.0, 1.0] for text in texts]

    def chat(self, messages, tools=None):
        self.requests.append({"messages": list(messages), "tools": tools})
        return self.replies.pop(0)

    def stream(self, messages):
        self.requests.append({"messages": list(messages)})
        yield "你"
        yield "好"


@pytest.fixture
def client():
    return FakeClient()
