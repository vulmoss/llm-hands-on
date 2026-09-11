"""客户端观测首段文本延迟，同时保留服务端 token 生成指标。"""

from time import perf_counter

from .chat import build_messages


def benchmark(client, question: str) -> dict:
    start = perf_counter()
    first_text = None
    parts = []
    final = {}
    for event in client.stream_events(build_messages(question)):
        content = event["message"].get("content", "")
        if content:
            if first_text is None:
                first_text = perf_counter() - start
            parts.append(content)
        if event.get("done"):
            final = event
    elapsed = perf_counter() - start
    duration = final.get("eval_duration", 0)
    count = final.get("eval_count", 0)
    return {
        "model": client.settings.model,
        "temperature": client.settings.temperature,
        "max_tokens": client.settings.max_tokens,
        "question": question,
        "answer": "".join(parts),
        "first_text_seconds": first_text,
        "wall_seconds": elapsed,
        "output_tokens": count,
        "tokens_per_second": count / duration * 1e9 if duration > 0 else None,
        "prompt_eval_seconds": final.get("prompt_eval_duration", 0) / 1e9,
        "load_seconds": final.get("load_duration", 0) / 1e9,
    }
