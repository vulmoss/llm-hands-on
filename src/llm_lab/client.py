"""Ollama 原生 HTTP 协议适配。上层无需知道 urllib 或响应字段。"""

import json
from collections.abc import Iterator
from http.client import HTTPException
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .config import Settings


class OllamaError(RuntimeError):
    """网络、服务端或协议错误；入口层负责向用户呈现。"""


class OllamaClient:
    def __init__(self, settings: Settings):
        self.settings = settings

    def _open(self, path: str, payload: dict | None = None):
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        request = Request(
            self.settings.base_url.rstrip("/") + path,
            data=data,
            headers={"Content-Type": "application/json"},
        )
        try:
            return urlopen(request, timeout=self.settings.timeout)
        except HTTPError as exc:
            detail = exc.read(2000).decode("utf-8", errors="replace")
            raise OllamaError(f"Ollama HTTP {exc.code}: {detail}") from exc
        except (URLError, OSError) as exc:
            raise OllamaError(
                f"无法连接 Ollama（{self.settings.base_url}）：{exc}。检查地址、端口和服务状态。"
            ) from exc

    @staticmethod
    def _decode(raw: bytes) -> dict:
        try:
            data = json.loads(raw)
        except (ValueError, UnicodeError) as exc:
            raise OllamaError("Ollama 返回了无效 JSON") from exc
        if not isinstance(data, dict):
            raise OllamaError("Ollama 响应必须是 JSON 对象")
        if data.get("error"):
            raise OllamaError(str(data["error"]))
        return data

    def _request(self, path: str, payload: dict | None = None) -> dict:
        try:
            with self._open(path, payload) as response:
                return self._decode(response.read())
        except (OSError, HTTPException) as exc:
            raise OllamaError(f"读取 Ollama 响应失败：{exc}") from exc

    def _chat_payload(self, messages: list[dict], stream: bool, tools=None) -> dict:
        payload = {
            "model": self.settings.model,
            "messages": messages,
            "stream": stream,
            "options": {
                "temperature": self.settings.temperature,
                "num_predict": self.settings.max_tokens,
            },
        }
        if tools:
            payload["tools"] = tools
        return payload

    @staticmethod
    def message(data: dict) -> dict:
        message = data.get("message")
        if (
            not isinstance(message, dict)
            or message.get("role") != "assistant"
            or not isinstance(message.get("content", ""), str)
        ):
            raise OllamaError("Ollama 返回了无效的 assistant 消息")
        return message

    def chat_response(self, messages: list[dict], tools=None) -> dict:
        data = self._request("/api/chat", self._chat_payload(messages, False, tools))
        self.message(data)
        return data

    def chat(self, messages: list[dict], tools=None) -> dict:
        return self.message(self.chat_response(messages, tools))

    def stream_events(self, messages: list[dict]) -> Iterator[dict]:
        """返回 NDJSON 事件，包括最后一个带计时指标的 done 事件。"""
        try:
            with self._open("/api/chat", self._chat_payload(messages, True)) as response:
                for line in response:
                    if not line.strip():
                        continue
                    event = self._decode(line)
                    self.message(event)
                    yield event
                    if event.get("done"):
                        return
        except (OSError, HTTPException) as exc:
            raise OllamaError(f"流式响应中断：{exc}") from exc
        raise OllamaError("流式响应提前结束，未收到 done 标记")

    def stream(self, messages: list[dict]) -> Iterator[str]:
        for event in self.stream_events(messages):
            text = event["message"].get("content", "")
            if text:
                yield text

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        data = self._request(
            "/api/embed",
            {
                "model": self.settings.embedding_model,
                "input": texts,
                "truncate": False,
            },
        )
        vectors = data.get("embeddings")
        if not isinstance(vectors, list) or len(vectors) != len(texts):
            raise OllamaError("Embedding 返回数量与输入文本数量不一致")
        return vectors

    def models(self) -> list[str]:
        data = self._request("/api/tags")
        models = data.get("models")
        if not isinstance(models, list) or any(
            not isinstance(item, dict) or not isinstance(item.get("name"), str) for item in models
        ):
            raise OllamaError("Ollama 返回了无效的模型列表")
        return [item["name"] for item in models]
