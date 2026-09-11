"""集中读取环境变量；核心逻辑也可以直接接收 Settings。"""

import math
import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit


@dataclass(frozen=True)
class Settings:
    base_url: str = "http://127.0.0.1:11434"
    model: str = "qwen2.5:7b"
    embedding_model: str = "all-minilm:33m"
    timeout: float = 120
    temperature: float = 0
    max_tokens: int = 512
    history_turns: int = 10
    max_tool_calls: int = 6
    index_path: Path = Path(".data/index.json")

    def __post_init__(self):
        url = urlsplit(self.base_url)
        if (
            url.scheme not in {"http", "https"}
            or not url.hostname
            or url.path not in {"", "/"}
            or url.query
            or url.fragment
            or url.username
            or url.password
        ):
            raise ValueError("OLLAMA_BASE_URL 必须是 http(s)://主机:端口，不含 /v1、凭据或查询参数")
        if not self.model.strip() or not self.embedding_model.strip():
            raise ValueError("模型名不能为空")
        if not math.isfinite(self.timeout) or self.timeout <= 0:
            raise ValueError("OLLAMA_TIMEOUT 必须大于 0")
        if not math.isfinite(self.temperature) or not 0 <= self.temperature <= 2:
            raise ValueError("LLM_TEMPERATURE 必须在 0 到 2 之间")
        if self.max_tokens < 1 or self.history_turns < 0 or self.max_tool_calls < 1:
            raise ValueError("Token/工具次数必须为正整数，历史轮数不能为负")

    @classmethod
    def from_env(cls):
        return cls(
            base_url=os.getenv("OLLAMA_BASE_URL", cls.base_url).rstrip("/"),
            model=os.getenv("OLLAMA_MODEL", cls.model),
            embedding_model=os.getenv("OLLAMA_EMBED_MODEL", cls.embedding_model),
            timeout=float(os.getenv("OLLAMA_TIMEOUT", str(cls.timeout))),
            temperature=float(os.getenv("LLM_TEMPERATURE", str(cls.temperature))),
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", str(cls.max_tokens))),
            history_turns=int(os.getenv("LLM_HISTORY_TURNS", str(cls.history_turns))),
            max_tool_calls=int(os.getenv("LLM_MAX_TOOL_CALLS", str(cls.max_tool_calls))),
            index_path=Path(os.getenv("LLM_INDEX_PATH", str(cls.index_path))),
        )
