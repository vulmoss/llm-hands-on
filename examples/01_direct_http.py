"""第一个练习：只用 Python 标准库调用模型，无需安装项目包。"""

import json
import os
from urllib.request import Request, urlopen


def main():
    endpoint = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
    payload = {
        "model": os.getenv("OLLAMA_MODEL", "qwen2.5:7b"),
        "messages": [{"role": "user", "content": "用一句话解释什么是 Token"}],
        "stream": False,
    }
    print("请求：", json.dumps(payload, ensure_ascii=False, indent=2))
    request = Request(
        endpoint + "/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urlopen(request, timeout=float(os.getenv("OLLAMA_TIMEOUT", "120"))) as response:
        data = json.load(response)
    print("完整响应：", json.dumps(data, ensure_ascii=False, indent=2))
    print("答案：", data["message"]["content"])


if __name__ == "__main__":
    main()
