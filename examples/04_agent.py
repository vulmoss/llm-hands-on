"""第四个练习：工具调用是可观察的程序流程。"""

import json

from llm_lab.agent import run_agent
from llm_lab.client import OllamaClient
from llm_lab.config import Settings


def main():
    settings = Settings.from_env()
    result = run_agent(
        OllamaClient(settings),
        "计算 2 的 10 次方，假设单位是 MiB，换算成 GiB。",
        max_tool_calls=settings.max_tool_calls,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
