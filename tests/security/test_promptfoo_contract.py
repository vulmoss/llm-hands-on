"""验证配置所用的应用契约；不假装执行过 Promptfoo CLI 或真实模型。"""

import json
import shutil
import subprocess
from pathlib import Path

import pytest
from conftest import FakeClient
from fastapi.testclient import TestClient

from llm_lab.api import create_app
from llm_lab.config import Settings
from llm_lab.rag import Chunk, VectorIndex

CONFIG = Path(__file__).resolve().parents[2] / "05-security/integrations/promptfoo/config.json"


@pytest.fixture
def api_results(tmp_path):
    config = json.loads(CONFIG.read_text())
    provider = config["providers"][0]
    assert provider["id"] == "http"
    assert provider["config"]["url"] == "http://127.0.0.1:8000/{{route}}"
    assert provider["config"]["method"] == "POST"
    assert config["prompts"] == ["{{question}}"]
    assert provider["config"]["body"] == {"question": "{{prompt}}"}
    client = FakeClient(
        [
            {"role": "assistant", "content": "42"},
            {"role": "assistant", "content": "1024 MiB [1]"},
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
    path = tmp_path / "index.json"
    text = "1 GiB 等于 1024 MiB。"
    VectorIndex.build(client, [Chunk("concepts.md", 0, len(text), text)]).save(path)
    results = []
    with TestClient(create_app(Settings(index_path=path), client)) as http:
        for test in config["tests"]:
            response = http.post(
                "/" + test["vars"]["route"], json={"question": test["vars"]["question"]}
            )
            assert response.status_code == 200
            results.append((test, response.json()))
    return provider, results


def test_requests_and_response_contract(api_results):
    _, results = api_results
    assert [test["vars"]["route"] for test, _ in results] == ["chat", "rag", "agent"]
    assert all(isinstance(result["answer"], str) for _, result in results)
    assert results[1][1]["sources"][0]["chunk"]["source"] == "concepts.md"
    assert results[2][1]["trace"][0]["result"]["data"]["result"] == 42


@pytest.mark.skipif(shutil.which("node") is None, reason="JavaScript 断言需要本机 Node.js")
def test_javascript_assertions_accept_success_and_reject_failures(api_results):
    provider, results = api_results
    # 本仓库受版本控制的配置代码；不执行模型生成的 JavaScript。
    script = """
const fs = require('fs');
const data = JSON.parse(fs.readFileSync(0, 'utf8'));
const output = new Function('json', 'return (' + data.transform + ')')(data.response);
const passed = new Function('output', 'return (' + data.assertion + ')')(output);
process.stdout.write(JSON.stringify(passed === true));
"""
    for test, response in results:
        for assertion in test["assert"]:
            assert assertion["type"] == "javascript"
            for candidate, expected in [
                (response, True),
                ({"answer": "wrong", "sources": [], "trace": [], "stopped": True}, False),
            ]:
                payload = {
                    "response": candidate,
                    "transform": provider["config"]["transformResponse"],
                    "assertion": assertion["value"],
                }
                result = subprocess.run(
                    ["node", "-e", script],
                    input=json.dumps(payload),
                    text=True,
                    capture_output=True,
                    check=True,
                    timeout=10,
                )
                assert json.loads(result.stdout) is expected
