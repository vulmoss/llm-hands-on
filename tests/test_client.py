import io
import json
from unittest.mock import patch
from urllib.error import HTTPError, URLError

import pytest

from llm_lab.client import OllamaClient, OllamaError
from llm_lab.config import Settings


def response(data):
    return io.BytesIO(json.dumps(data).encode())


def test_chat_uses_native_endpoint_and_options():
    client = OllamaClient(Settings())
    with patch(
        "llm_lab.client.urlopen",
        return_value=response(
            {
                "message": {"role": "assistant", "content": "你好"},
                "done": True,
            }
        ),
    ) as opening:
        assert client.chat([{"role": "user", "content": "你好"}])["content"] == "你好"
    request = opening.call_args.args[0]
    payload = json.loads(request.data)
    assert request.full_url.endswith("/api/chat")
    assert payload["stream"] is False
    assert payload["options"]["num_predict"] == 512
    assert opening.call_args.kwargs["timeout"] == 120


def test_stream_unicode_blank_lines_and_final_content():
    events = [
        {"message": {"role": "assistant", "content": "你"}, "done": False},
        {"message": {"role": "assistant", "content": "好"}, "done": True},
    ]
    raw = "\n" + "\n\n".join(json.dumps(e, ensure_ascii=False) for e in events)
    with patch("llm_lab.client.urlopen", return_value=io.BytesIO(raw.encode())):
        assert list(OllamaClient(Settings()).stream([])) == ["你", "好"]


@pytest.mark.parametrize(
    "raw",
    [
        b"not-json\n",
        b'{"error":"model failed"}\n',
        b'{"message":{"role":"assistant","content":"partial"}}\n',
    ],
)
def test_invalid_or_incomplete_stream(raw):
    with patch("llm_lab.client.urlopen", return_value=io.BytesIO(raw)):
        with pytest.raises(OllamaError):
            list(OllamaClient(Settings()).stream([]))


def test_network_and_http_errors():
    for exc in [
        URLError("offline"),
        HTTPError("url", 404, "missing", {}, io.BytesIO(b"missing model")),
    ]:
        with patch("llm_lab.client.urlopen", side_effect=exc):
            with pytest.raises(OllamaError):
                OllamaClient(Settings()).models()


def test_embedding_batch_is_not_silently_truncated():
    with patch(
        "llm_lab.client.urlopen", return_value=response({"embeddings": [[1, 2]]})
    ) as opening:
        client = OllamaClient(Settings())
        with pytest.raises(OllamaError, match="数量"):
            client.embed(["first", "second"])
        assert json.loads(opening.call_args.args[0].data)["truncate"] is False
