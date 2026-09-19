"""所有入口共用配置与业务函数；命令失败返回非零退出码。"""

import argparse
import json
import sys
from pathlib import Path

from .agent import run_agent
from .benchmark import benchmark
from .chat import DEFAULT_SYSTEM, build_messages
from .client import OllamaClient, OllamaError
from .config import Settings
from .rag import VectorIndex, answer_question, format_hits, load_chunks
from .tools import default_tools, knowledge_tool


def dump(data):
    print(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False))


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description="LLM 学习实验室：从 HTTP 到 RAG 和 Agent")
    commands = root.add_subparsers(dest="command", required=True)
    commands.add_parser("doctor", help="检查 Ollama 连接及配置模型是否已安装")
    ask = commands.add_parser("ask", help="单次提问")
    ask.add_argument("question")
    ask.add_argument("--stream", action="store_true")
    ask.add_argument("--system", default=DEFAULT_SYSTEM)
    chat = commands.add_parser("chat", help="命令行多轮聊天（/clear 清空，/exit 退出）")
    chat.add_argument("--system", default=DEFAULT_SYSTEM)
    index = commands.add_parser("index", help="从 UTF-8 Markdown/文本目录构建向量索引")
    index.add_argument("directory", type=Path)
    index.add_argument("--index", type=Path)
    index.add_argument("--chunk-size", type=int, default=500)
    index.add_argument("--overlap", type=int, default=80)
    rag = commands.add_parser("rag", help="检索文档并回答")
    rag.add_argument("question")
    rag.add_argument("--index", type=Path)
    rag.add_argument("-k", type=int, default=3)
    rag.add_argument("--min-score", type=float, default=-1)
    rag.add_argument("--retrieve-only", action="store_true", help="只观察片段和分数，不生成答案")
    rag.add_argument("--json", action="store_true")
    agent = commands.add_parser("agent", help="运行有工具调用预算的 Agent")
    agent.add_argument("question")
    agent.add_argument("--with-notes", action="store_true", help="增加本地笔记检索工具")
    agent.add_argument("--index", type=Path)
    agent.add_argument("--trace", action="store_true")
    bench = commands.add_parser("benchmark", help="输出包含真实客户端延迟的 JSON 实验记录")
    bench.add_argument("question")
    bench.add_argument("--repeat", type=int, default=3)
    security = commands.add_parser("security-eval", help="校验或运行固定 RAG 安全样例")
    security.add_argument("--cases", type=Path, nargs="+", required=True)
    security.add_argument("--check", action="store_true", help="仅离线校验，不连接模型")
    security.add_argument("--output", type=Path, help="新建 JSON 证据文件，不覆盖已有文件")
    security.add_argument("--repeat", type=int, default=1)
    security.add_argument("--label", default="baseline")
    for name, default_port in [("ui", 7860), ("serve", 8000)]:
        command = commands.add_parser(
            name, help="启动网页聊天" if name == "ui" else "启动 HTTP API"
        )
        command.add_argument("--host", default="127.0.0.1")
        command.add_argument("--port", type=int, default=default_port)
    return root


def stream_answer(client, messages) -> str:
    parts = []
    for part in client.stream(messages):
        print(part, end="", flush=True)
        parts.append(part)
    print()
    return "".join(parts)


def interactive(client, settings: Settings, system: str):
    history = []
    print("输入 /clear 清空上下文，/exit 退出。")
    while True:
        try:
            question = input("你> ").strip()
        except EOFError:
            return
        if question == "/exit":
            return
        if question == "/clear":
            history.clear()
            print("上下文已清空。")
            continue
        if not question:
            continue
        messages = build_messages(question, history, system, settings.history_turns)
        try:
            answer = stream_answer(client, messages)
        except OllamaError as exc:
            print(f"\n错误：{exc}", file=sys.stderr)
            continue
        # 只把完整回答加入历史，失败的半截响应不进入下一轮。
        history = [item for item in messages if item["role"] != "system"]
        history.append({"role": "assistant", "content": answer})


def dispatch(args, settings: Settings, client) -> int:
    if args.command == "doctor":
        models = client.models()

        def installed(name):
            return name in models or (":" not in name and f"{name}:latest" in models)

        missing = [
            name for name in (settings.model, settings.embedding_model) if not installed(name)
        ]
        dump({"base_url": settings.base_url, "models": models, "missing": missing})
        if missing:
            print(
                "请在 Ollama 主机上运行：" + "；".join(f"ollama pull {name}" for name in missing),
                file=sys.stderr,
            )
        return 1 if missing else 0
    if args.command == "ask":
        messages = build_messages(args.question, system=args.system)
        if args.stream:
            stream_answer(client, messages)
        else:
            print(client.chat(messages).get("content", ""))
    elif args.command == "chat":
        interactive(client, settings, args.system)
    elif args.command == "index":
        chunks = load_chunks(args.directory, args.chunk_size, args.overlap)
        index = VectorIndex.build(client, chunks)
        path = args.index or settings.index_path
        index.save(path)
        dump({"index": str(path), "chunks": len(chunks), "embedding_model": index.model})
    elif args.command == "rag":
        index = VectorIndex.load(args.index or settings.index_path)
        if args.retrieve_only:
            hits = index.search(client, args.question, args.k, args.min_score)
            print(format_hits(hits) or "没有满足阈值的片段。")
            print("\n余弦相似度：", [round(hit.score, 4) for hit in hits])
        else:
            result = answer_question(client, index, args.question, args.k, args.min_score)
            if args.json:
                dump(result)
            else:
                print(result["answer"])
                print("\n提供给模型的参考片段（不代表已自动验证引用）：")
                for source in result["sources"]:
                    chunk = source["chunk"]
                    print(
                        f"[{source['id']}] {chunk['source']}:{chunk['start']}:{chunk['end']} "
                        f"score={source['score']:.4f}"
                    )
    elif args.command == "agent":
        tools = default_tools()
        if args.with_notes:
            tool = knowledge_tool(client, VectorIndex.load(args.index or settings.index_path))
            tools[tool.name] = tool
        result = run_agent(client, args.question, tools, settings.max_tool_calls)
        dump(result) if args.trace else print(result["answer"])
        return 2 if result["stopped"] else 0
    elif args.command == "benchmark":
        if not 1 <= args.repeat <= 100:
            raise ValueError("repeat 必须在 1 到 100 之间")
        dump([{"run": i + 1, **benchmark(client, args.question)} for i in range(args.repeat)])
    elif args.command == "security-eval":
        from .security_eval import run_evaluation

        return run_evaluation(args, client)
    elif args.command == "ui":
        from .ui import launch

        launch(settings, args.host, args.port)
    elif args.command == "serve":
        import uvicorn

        from .api import create_app

        uvicorn.run(create_app(settings, client), host=args.host, port=args.port)
    return 0


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "security-eval" and args.check:
            from .security_eval import load_cases

            cases = load_cases(args.cases)
            dump({"cases": len(cases), "validation": "passed", "model_evaluation": "not_run"})
            return 0
        settings = Settings.from_env()
        return dispatch(args, settings, OllamaClient(settings))
    except ImportError as exc:
        extra = "ui" if args.command == "ui" else "api"
        print(f"缺少可选依赖：{exc}。运行 python -m pip install -e '.[{extra}]'", file=sys.stderr)
        return 1
    except (OllamaError, ValueError, OSError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\n已退出。", file=sys.stderr)
        return 130
