"""Small observable agent loop and five-case regression. Fixtures are never model scores."""

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

COURSE = Path(__file__).resolve().parents[1]
ROOT = COURSE.parents[1]
sys.path.insert(0, str(ROOT / "src"))
from llm_lab.agent import run_agent  # noqa: E402
from llm_lab.client import OllamaClient, OllamaError  # noqa: E402
from llm_lab.config import Settings  # noqa: E402


class ScriptedClient:
    def __init__(self, mode):
        self.mode = mode
        self.calls = 0

    def chat(self, messages, tools=None):
        self.calls += 1
        if self.mode == "normal" and self.calls > 2:
            return {"role": "assistant", "content": "1024 MiB = 1 GiB（脚本替身）"}
        name = "not_registered" if self.mode == "unknown" else "calculator"
        arguments = {"operation": "power", "a": 2, "b": 10}
        if self.mode == "normal" and self.calls == 2:
            name, arguments = (
                "unit_converter",
                {"value": 1024, "from_unit": "mib", "to_unit": "gib"},
            )
        return {
            "role": "assistant",
            "content": "",
            "tool_calls": [{"function": {"name": name, "arguments": arguments}}],
        }


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def parse_prediction(text):
    data = json.loads(text)
    if not isinstance(data, dict) or set(data) != {"supported", "reason"}:
        raise ValueError("Expected supported/reason JSON object")
    if (
        type(data["supported"]) is not bool
        or not isinstance(data["reason"], str)
        or not data["reason"].strip()
    ):
        raise ValueError("Invalid prediction field types")
    return data


def score(cases, records):
    if [x["id"] for x in cases] != [x["id"] for x in records]:
        raise ValueError("Case IDs/order must exactly match the dataset")
    counts = dict(tp=0, tn=0, fp=0, fn=0, errors=0)
    for case, record in zip(cases, records):
        prediction = record.get("prediction")
        if type(prediction) is not bool:
            counts["errors"] += 1
        else:
            key = (
                ("tp" if prediction else "fn")
                if case["supported"]
                else ("fp" if prediction else "tn")
            )
            counts[key] += 1
    counts["total"] = len(cases)
    counts["accuracy_including_errors"] = (counts["tp"] + counts["tn"]) / len(cases)
    return counts


def evaluate(prompt_name, live, fixture=None):
    raw_cases = (COURSE / "data/regression.json").read_bytes()
    cases = json.loads(raw_cases)
    prompt = (COURSE / f"prompts/{prompt_name}.txt").read_text()
    settings = Settings.from_env()
    client = OllamaClient(settings) if live else None
    predictions = (
        [True, True, False, True, False]
        if fixture == "demo-v1"
        else [True, False, True, False, False]
    )
    records = []
    for i, case in enumerate(cases):
        started = time.monotonic()
        raw = ""
        try:
            if live:
                response = client.chat_response(
                    [
                        {"role": "system", "content": prompt},
                        {"role": "user", "content": case["evidence"]},
                    ]
                )
                raw = response["message"]["content"]
                parsed = parse_prediction(raw)
                if response.get("done_reason") == "length":
                    raise ValueError("Truncated model response")
            else:
                parsed = {"supported": predictions[i], "reason": "预设替身，不代表真实模型"}
                raw = json.dumps(parsed, ensure_ascii=False)
            record = {
                "id": case["id"],
                "prediction": parsed["supported"],
                "reason": parsed["reason"],
                "raw": raw,
            }
        except (OllamaError, OSError, ValueError, KeyError) as exc:
            record = {"id": case["id"], "prediction": None, "error": str(exc), "raw": raw}
        record["seconds"] = round(time.monotonic() - started, 3)
        records.append(record)
    return {
        "source": "live-model" if live else "scripted-fixture",
        "fixture": fixture,
        "model": settings.model if live else "none",
        "max_tokens": settings.max_tokens,
        "temperature": settings.temperature,
        "prompt": prompt_name,
        "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
        "dataset_sha256": hashlib.sha256(raw_cases).hexdigest(),
        "records": records,
        "metrics": score(cases, records),
    }


def compare(a, b):
    for key in ("source", "model", "max_tokens", "temperature", "dataset_sha256"):
        if a[key] != b[key]:
            raise ValueError(f"A/B mismatch: {key}")
    return {
        "source": a["source"],
        "a": a["metrics"],
        "b": b["metrics"],
        "accuracy_delta": b["metrics"]["accuracy_including_errors"]
        - a["metrics"]["accuracy_including_errors"],
        "seconds_a": sum(r["seconds"] for r in a["records"]),
        "seconds_b": sum(r["seconds"] for r in b["records"]),
        "note": "5 条已知样例仅回归；不能据此证明泛化能力或真实漏洞检出率。",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    loop = sub.add_parser("loop")
    loop.add_argument("--mode", choices=["normal", "loop", "unknown"], default="normal")
    loop.add_argument("--live", action="store_true")
    loop.add_argument("--budget", type=int, default=3)
    loop.add_argument("--output", type=Path, required=True)
    evaluate_parser = sub.add_parser("eval")
    evaluate_parser.add_argument("--prompt", choices=["v1", "v2"], default="v1")
    mode = evaluate_parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--live", action="store_true")
    mode.add_argument("--fixture", choices=["demo-v1", "demo-v2"])
    evaluate_parser.add_argument("--output", type=Path, required=True)
    ab = sub.add_parser("compare")
    ab.add_argument("a", type=Path)
    ab.add_argument("b", type=Path)
    ab.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "loop":
            if args.live and args.mode != "normal":
                raise ValueError("Failure modes are scripted tests; use --mode normal with --live")
            settings = Settings.from_env()
            client = OllamaClient(settings) if args.live else ScriptedClient(args.mode)
            started = time.monotonic()
            result = run_agent(
                client, "计算2的10次方，按 MiB 换算成 GiB。", max_tool_calls=args.budget
            )
            events = [{"event": "plan", "summary": "执行计算并转换单位；只使用已注册教学工具"}]
            for step in result["trace"]:
                events += [
                    {"event": "tool_call", "name": step["tool"], "arguments": step["arguments"]},
                    {"event": "observation", "result": step["result"]},
                ]
            events.append(
                {"event": "stop", "budget_exhausted": result["stopped"], "answer": result["answer"]}
            )
            value = {
                "source": "live-model" if args.live else "scripted-fixture",
                "model": settings.model if args.live else "none",
                "max_tokens": settings.max_tokens,
                "temperature": settings.temperature,
                "events": events,
                "seconds": round(time.monotonic() - started, 3),
                "result": result,
            }
            save(args.output, value)
            print(f"Saved {len(events)} observable events; stopped={result['stopped']}")
            return 0
        if args.command == "eval":
            result = evaluate(args.prompt, args.live, args.fixture)
            save(args.output, result)
            print(json.dumps(result["metrics"], ensure_ascii=False))
            return 1 if result["metrics"]["errors"] else 0
        if args.command == "compare":
            result = compare(json.loads(args.a.read_text()), json.loads(args.b.read_text()))
            save(args.output, result)
            print(json.dumps(result, ensure_ascii=False, indent=2))
    except (OSError, ValueError, OllamaError, KeyError, TypeError) as exc:
        print(f"Practice error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
