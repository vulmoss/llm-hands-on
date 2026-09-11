"""聊天只负责组织消息。历史由调用者持有，不在服务端共享。"""

DEFAULT_SYSTEM = "你是一个有帮助的学习助手，请用中文回答；不确定时明确说明。"


def text_content(content) -> str:
    """兼容纯文本和 Gradio 6 的文本内容块；拒绝悄悄丢弃附件。"""
    if isinstance(content, str):
        return content
    if isinstance(content, list) and all(
        isinstance(block, dict)
        and block.get("type") == "text"
        and isinstance(block.get("text"), str)
        for block in content
    ):
        return "\n".join(block["text"] for block in content)
    raise ValueError("当前聊天入口只支持文本消息")


def build_messages(
    question: str, history=(), system: str = DEFAULT_SYSTEM, history_turns: int = 10
) -> list[dict]:
    if not isinstance(question, str) or not question.strip():
        raise ValueError("问题不能为空")
    if history_turns < 0:
        raise ValueError("历史轮数不能为负")
    previous = []
    for item in history:
        if not isinstance(item, dict) or item.get("role") not in {"user", "assistant"}:
            raise ValueError("历史消息只允许 user / assistant 角色")
        previous.append({"role": item["role"], "content": text_content(item.get("content"))})
    # 按 user 消息定位轮次，避免截断后以孤立的 assistant 消息开头。
    starts = [i for i, item in enumerate(previous) if item["role"] == "user"]
    previous = (
        previous[starts[-min(history_turns, len(starts))] :] if history_turns and starts else []
    )
    messages = [{"role": "system", "content": system}] if system else []
    return messages + previous + [{"role": "user", "content": question.strip()}]
