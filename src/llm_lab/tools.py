"""显式工具注册表：模型提出调用，Python 验证参数并执行。"""

import inspect
import math
from dataclasses import dataclass
from typing import Callable


def number(value) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError("参数必须是有限数字")
    if abs(value) > 1e12:
        raise ValueError("教学工具只接受绝对值不超过 1e12 的数字")
    return float(value)


def calculator(operation: str, a: float, b: float) -> dict:
    a, b = number(a), number(b)
    operations = {
        "add": lambda: a + b,
        "subtract": lambda: a - b,
        "multiply": lambda: a * b,
        "divide": lambda: a / b,
        "power": lambda: a**b,
    }
    if operation not in operations:
        raise ValueError("不支持的操作")
    if operation == "power" and abs(b) > 100:
        raise ValueError("指数绝对值不能超过 100")
    result = operations[operation]()
    if isinstance(result, complex) or not math.isfinite(result):
        raise ValueError("结果不是有限实数")
    return {"result": result}


def unit_converter(value: float, from_unit: str, to_unit: str) -> dict:
    value = number(value)
    # 十进制 GB/MB 与二进制 GiB/MiB 明确区分。
    conversions = {
        ("km", "miles"): lambda v: v / 1.609344,
        ("miles", "km"): lambda v: v * 1.609344,
        ("kg", "lbs"): lambda v: v / 0.45359237,
        ("lbs", "kg"): lambda v: v * 0.45359237,
        ("c", "f"): lambda v: v * 9 / 5 + 32,
        ("f", "c"): lambda v: (v - 32) * 5 / 9,
        ("gb", "mb"): lambda v: v * 1000,
        ("mb", "gb"): lambda v: v / 1000,
        ("gib", "mib"): lambda v: v * 1024,
        ("mib", "gib"): lambda v: v / 1024,
    }
    if not isinstance(from_unit, str) or not isinstance(to_unit, str):
        raise ValueError("单位必须是字符串")
    key = (from_unit.strip().lower(), to_unit.strip().lower())
    if key not in conversions:
        raise ValueError("不支持的转换；支持 km/miles、kg/lbs、c/f、GB/MB、GiB/MiB")
    return {"value": conversions[key](value), "unit": to_unit}


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    properties: dict
    function: Callable

    def schema(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": self.properties,
                    "required": list(self.properties),
                    "additionalProperties": False,
                },
            },
        }

    def invoke(self, arguments: dict) -> dict:
        if not isinstance(arguments, dict):
            raise ValueError("工具参数必须是对象")
        inspect.signature(self.function).bind(**arguments)
        return self.function(**arguments)


def default_tools() -> dict[str, Tool]:
    tools = [
        Tool(
            "calculator",
            "对两个数字执行一次数学运算；复杂表达式分步调用。",
            {
                "operation": {
                    "type": "string",
                    "enum": ["add", "subtract", "multiply", "divide", "power"],
                },
                "a": {"type": "number"},
                "b": {"type": "number"},
            },
            calculator,
        ),
        Tool(
            "unit_converter",
            "单位转换：km/miles、kg/lbs、c/f、GB/MB（1000）、GiB/MiB（1024）。",
            {
                "value": {"type": "number"},
                "from_unit": {"type": "string"},
                "to_unit": {"type": "string"},
            },
            unit_converter,
        ),
    ]
    return {tool.name: tool for tool in tools}


def knowledge_tool(client, index) -> Tool:
    from .rag import format_hits

    def search_notes(query: str) -> dict:
        if not isinstance(query, str):
            raise ValueError("query 必须是字符串")
        hits = index.search(client, query)
        return {"references": format_hits(hits)}

    return Tool(
        "search_notes",
        "检索本地学习笔记；查询私人笔记中的事实时使用。",
        {
            "query": {"type": "string"},
        },
        search_notes,
    )
