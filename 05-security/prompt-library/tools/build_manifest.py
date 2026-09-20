#!/usr/bin/env python3
"""Generate skills.json from both source formats in the Skills/ tree.

Reads metadata from each SKILL.md and emits a compact JSON manifest
of all skills, grouped by category, for tooling that needs a machine-readable
index of the library.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT / "Skills"
OUT = ROOT / "skills.json"

sys.path.insert(0, str(ROOT))
from convert_skills import discover  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUT)
    args = parser.parse_args()
    if not SKILLS_DIR.is_dir():
        print(f"Error: {SKILLS_DIR} not found", file=sys.stderr)
        return 1

    manifest: dict = {
        "name": "claude-red-openai",
        "version": "0.3.0",
        "license": "MIT",
        "homepage": "https://github.com/SnailSploit/claude-red",
        "formats": ["codex", "chatgpt"],
        "categories": {},
        "skills": [],
    }

    for skill in discover(SKILLS_DIR):
        entry = {
            "name": skill.name,
            "category": skill.category,
            "path": skill.source.relative_to(ROOT).as_posix(),
            "description": skill.description,
        }
        manifest["categories"].setdefault(skill.category, []).append(skill.name)
        manifest["skills"].append(entry)

    manifest["skill_count"] = len(manifest["skills"])
    manifest["category_count"] = len(manifest["categories"])

    args.output.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(
        f"Wrote {args.output} with {manifest['skill_count']} skills across {manifest['category_count']} categories."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
