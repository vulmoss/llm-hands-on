import pytest

from llm_lab.chat import build_messages, text_content
from llm_lab.config import Settings


def test_environment(monkeypatch):
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:11434/")
    monkeypatch.setenv("LLM_HISTORY_TURNS", "0")
    settings = Settings.from_env()
    assert settings.base_url == "http://localhost:11434"
    assert settings.history_turns == 0


@pytest.mark.parametrize(
    "changes",
    [
        {"base_url": "http://localhost:11434/v1"},
        {"base_url": "file:///etc/passwd"},
        {"timeout": 0},
        {"temperature": float("nan")},
        {"history_turns": -1},
    ],
)
def test_invalid_settings(changes):
    with pytest.raises(ValueError):
        Settings(**changes)


def test_history_trims_whole_turn_and_does_not_mutate_input():
    history = [
        {"role": "user", "content": "旧问题"},
        {"role": "assistant", "content": "旧答案"},
        {"role": "user", "content": "我学习 Python"},
        {"role": "assistant", "content": "好的"},
    ]
    messages = build_messages("我学什么？", history, history_turns=1)
    assert [m["content"] for m in messages[1:]] == ["我学习 Python", "好的", "我学什么？"]
    assert len(history) == 4
    assert len(build_messages("问题", history, history_turns=0)) == 2
    assert len(build_messages("问题", history, history_turns=10)) == 6


def test_block_content_and_invalid_history():
    assert text_content([{"type": "text", "text": "你好"}]) == "你好"
    with pytest.raises(ValueError):
        text_content([{"type": "image", "url": "file.png"}])
    with pytest.raises(ValueError):
        build_messages("问题", [{"role": "system", "content": "历史不能设置系统提示词"}])
    with pytest.raises(ValueError):
        build_messages(" ")
