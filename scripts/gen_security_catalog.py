"""校验实验清单并生成导航；不执行清单里的命令、不连接模型。"""

import argparse
import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIELDS = {"id", "title", "entrypoint", "offline_command", "live_command", "model_status", "report"}


def validate_catalog(data: dict, root: Path) -> list[dict]:
    if (
        not isinstance(data, dict)
        or set(data) != {"labs"}
        or not isinstance(data["labs"], list)
        or not data["labs"]
    ):
        raise ValueError("清单必须包含非空 labs 列表")
    ids = set()
    for lab in data["labs"]:
        if not isinstance(lab, dict) or set(lab) != FIELDS:
            raise ValueError("实验字段不完整或含未知字段")
        for key in FIELDS - {"live_command"}:
            if not isinstance(lab[key], str) or not lab[key].strip() or "\n" in lab[key]:
                raise ValueError(f"{key} 必须是非空单行字符串")
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", lab["id"]) or lab["id"] in ids:
            raise ValueError("实验 id 格式错误或重复")
        ids.add(lab["id"])
        if lab["model_status"] not in {"pending", "not_applicable"}:
            raise ValueError("model_status 必须是 pending 或 not_applicable；实测结论写入报告")
        live = lab["live_command"]
        if live is not None and (not isinstance(live, str) or not live.strip() or "\n" in live):
            raise ValueError("live_command 必须是非空单行字符串或 null")
        if (live is None) != (lab["model_status"] == "not_applicable"):
            raise ValueError("真实模型状态与运行命令不一致")
        for key in ("entrypoint", "report"):
            path = root / lab[key]
            if (
                Path(lab[key]).is_absolute()
                or not path.resolve().is_relative_to(root.resolve())
                or not path.is_file()
            ):
                raise ValueError(f"{key} 必须指向仓库内已有文件：{lab[key]}")
    return data["labs"]


def render(labs: list[dict]) -> str:
    lines = [
        "# 安全实验目录",
        "",
        "由 `data/security/labs.json` 生成。修改清单后运行 `python scripts/gen_security_catalog.py`。",
        "",
        "离线测试检查程序行为；真实模型与 Promptfoo CLI 的实测结论见各实验报告。",
        "",
        "| 实验 | 真实模型评估 | 报告 |",
        "|---|---|---|",
    ]
    for lab in labs:
        entry = os.path.relpath(ROOT / lab["entrypoint"], ROOT / "05-security")
        report = os.path.relpath(ROOT / lab["report"], ROOT / "05-security")
        status = (
            "待环境恢复后验证" if lab["model_status"] == "pending" else "无需模型（执行器回归）"
        )
        title = lab["title"].replace("|", "\\|")
        lines.append(f"| [{title}]({entry}) | {status} | [验证记录]({report}) |")
    lines += ["", "## 离线验收命令", "", "从仓库根目录执行：", "", "```bash"]
    lines.extend(lab["offline_command"] for lab in labs)
    lines += ["```", ""]
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    output = ROOT / "05-security/LABS.md"
    try:
        data = json.loads((ROOT / "data/security/labs.json").read_text(encoding="utf-8"))
        rendered = render(validate_catalog(data, ROOT))
        if args.check:
            if not output.is_file() or output.read_text(encoding="utf-8") != rendered:
                print("实验目录过期，请运行 python scripts/gen_security_catalog.py")
                return 1
        else:
            output.write_text(rendered, encoding="utf-8")
    except (ValueError, OSError) as exc:
        print(f"实验目录错误：{exc}")
        return 2
    print("实验目录校验通过" if args.check else "实验目录已生成")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
