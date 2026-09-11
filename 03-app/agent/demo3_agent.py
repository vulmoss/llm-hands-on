"""兼容旧入口；完整实现与练习见 src/llm_lab 和 examples。"""

import sys

from llm_lab.cli import main

if __name__ == "__main__":
    arguments = sys.argv[1:] or ["100 公里是多少英里？"]
    raise SystemExit(main(["agent", *arguments]))
