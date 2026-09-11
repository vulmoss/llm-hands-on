"""兼容旧入口；完整实现与练习见 src/llm_lab 和 examples。"""

import sys

from llm_lab.cli import main

if __name__ == "__main__":
    arguments = sys.argv[1:] or ["推理服务负责什么？"]
    raise SystemExit(main(["rag", *arguments]))
