import importlib.util
import io
from contextlib import redirect_stdout
from unittest.mock import patch

import pytest

from llm_lab.benchmark import benchmark
from llm_lab.cli import main
from llm_lab.config import Settings


def test_cli_failure_exit_code():
    with patch("llm_lab.cli.Settings.from_env", side_effect=ValueError("bad config")):
        assert main(["ask", "hello"]) == 1


def test_cli_stream(client):
    with patch("llm_lab.cli.OllamaClient", return_value=client):
        output = io.StringIO()
        with redirect_stdout(output):
            assert main(["ask", "hello", "--stream"]) == 0
        assert output.getvalue() == "你好\n"


def test_benchmark_measures_client_latency(client):
    client.stream_events = lambda messages: iter(
        [
            {"message": {"content": ""}, "done": False},
            {"message": {"content": "你好"}, "done": False},
            {
                "message": {"content": ""},
                "done": True,
                "eval_count": 4,
                "eval_duration": 2e9,
                "prompt_eval_duration": 0.1e9,
            },
        ]
    )
    with patch("llm_lab.benchmark.perf_counter", side_effect=[10, 12, 15]):
        result = benchmark(client, "hello")
    assert result["first_text_seconds"] == 2
    assert result["wall_seconds"] == 5
    assert result["tokens_per_second"] == 2
    assert result["prompt_eval_seconds"] == 0.1


@pytest.mark.skipif(importlib.util.find_spec("fastapi") is None, reason="需要 api extra")
def test_api_validation_and_request_isolation(client, tmp_path):
    from fastapi.testclient import TestClient

    from llm_lab.api import create_app
    from llm_lab.client import OllamaError

    with TestClient(create_app(Settings(index_path=tmp_path / "missing.json"), client)) as http:
        assert http.get("/health").status_code == 200
        assert http.post("/chat", json={"question": "你好"}).status_code == 200
        assert client.requests[0]["messages"][-1]["content"] == "你好"
        client.replies.append({"role": "assistant", "content": "第二个独立请求"})
        assert http.post("/chat", json={"question": "另一用户"}).status_code == 200
        assert len(client.requests[1]["messages"]) == 2
        assert all(item["content"] != "你好" for item in client.requests[1]["messages"])
        assert http.post("/chat", json={"question": ""}).status_code == 422
        assert http.post("/chat", json={"question": " "}).status_code == 400
        assert http.post("/rag", json={"question": "资料"}).status_code == 400
        assert http.post("/rag", json={"question": "资料", "k": 0}).status_code == 422
        client.chat = lambda *args, **kwargs: (_ for _ in ()).throw(OllamaError("offline"))
        assert http.post("/chat", json={"question": "你好"}).status_code == 502


@pytest.mark.skipif(importlib.util.find_spec("gradio") is None, reason="需要 ui extra")
def test_ui_constructs_and_streams(client):
    from llm_lab.ui import create_ui

    ui = create_ui(Settings(), client)
    assert list(ui.fn("你好", [], "中文回答")) == ["你", "你好"]
    history = [{"role": "user", "content": [{"type": "text", "text": "我学 Python"}]}]
    assert list(ui.fn("我学什么", history, "中文回答"))[-1] == "你好"
    assert client.requests[-1]["messages"][1]["content"] == "我学 Python"
    ui.close()


def test_cli_index_then_rag(client, tmp_path):
    notes = tmp_path / "notes"
    notes.mkdir()
    (notes / "python.md").write_text("Python", encoding="utf-8")
    index = tmp_path / "index.json"
    with patch("llm_lab.cli.OllamaClient", return_value=client):
        with redirect_stdout(io.StringIO()):
            assert main(["index", str(notes), "--index", str(index)]) == 0
        output = io.StringIO()
        with redirect_stdout(output):
            assert main(["rag", "Python", "--index", str(index), "--json"]) == 0
        assert "python.md" in output.getvalue()


@pytest.mark.skipif(importlib.util.find_spec("fastapi") is None, reason="需要 api extra")
def test_api_rag_and_agent(client, tmp_path):
    from fastapi.testclient import TestClient

    from llm_lab.api import create_app
    from llm_lab.rag import Chunk, VectorIndex

    path = tmp_path / "index.json"
    VectorIndex.build(client, [Chunk("python.md", 0, 6, "Python")]).save(path)
    client.replies.extend(
        [
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "function": {
                            "name": "calculator",
                            "arguments": {"operation": "multiply", "a": 6, "b": 7},
                        }
                    }
                ],
            },
            {"role": "assistant", "content": "42"},
        ]
    )
    with TestClient(create_app(Settings(index_path=path), client)) as http:
        result = http.post("/rag", json={"question": "Python"})
        assert result.status_code == 200
        assert result.json()["sources"][0]["chunk"]["source"] == "python.md"
        result = http.post("/agent", json={"question": "6*7"})
        assert result.status_code == 200
        assert result.json()["answer"] == "42"
        assert result.json()["trace"][0]["result"]["data"]["result"] == 42
