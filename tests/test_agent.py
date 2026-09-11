import pytest
from conftest import FakeClient

from llm_lab.agent import run_agent
from llm_lab.tools import calculator, unit_converter


def call(name="calculator", arguments=None):
    return {
        "function": {
            "name": name,
            "arguments": arguments
            or {
                "operation": "multiply",
                "a": 6,
                "b": 7,
            },
        }
    }


def test_tool_result_is_returned_to_model():
    client = FakeClient(
        [
            {"role": "assistant", "content": "", "tool_calls": [call()]},
            {"role": "assistant", "content": "42"},
        ]
    )
    result = run_agent(client, "6*7")
    assert result["answer"] == "42"
    assert result["trace"][0]["result"]["data"]["result"] == 42
    assert client.requests[1]["messages"][-1]["role"] == "tool"
    assert client.requests[1]["messages"][-1]["tool_name"] == "calculator"


def test_budget_counts_all_calls_in_single_response():
    client = FakeClient([{"role": "assistant", "content": "", "tool_calls": [call()] * 10}])
    result = run_agent(client, "不停计算", max_tool_calls=2)
    assert result["stopped"] is True
    assert len(result["trace"]) == 2


def test_errors_return_as_tool_results():
    client = FakeClient(
        [
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    call("unknown"),
                    call(arguments={"operation": "divide", "a": 1, "b": 0}),
                    call(arguments={"operation": "add", "a": "1", "b": 1}),
                ],
            },
            {"role": "assistant", "content": "工具执行失败"},
        ]
    )
    result = run_agent(client, "故障测试")
    assert all(not item["result"]["ok"] for item in result["trace"])


def test_repeated_tool_calls_terminate():
    client = FakeClient([{"role": "assistant", "content": "", "tool_calls": [call()]}] * 4)
    result = run_agent(client, "重复调用", max_tool_calls=3)
    assert result["stopped"] and len(result["trace"]) == 3


def test_numeric_tools_and_units():
    assert calculator("power", 2, 10)["result"] == 1024
    assert unit_converter(1024, "MiB", "GiB")["value"] == 1
    assert unit_converter(1000, "MB", "GB")["value"] == 1
    for args in [("power", 2, 1000000), ("add", True, 1), ("add", float("inf"), 1)]:
        with pytest.raises(ValueError):
            calculator(*args)
