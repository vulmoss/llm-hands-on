#!/usr/bin/env python3
"""Export the mixed-format Skills library for Codex or ChatGPT (stdlib only)."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent


@dataclass(frozen=True)
class Skill:
    name: str
    category: str
    description: str
    source: Path
    body: str


def parse_frontmatter(text: str) -> dict[str, str]:
    """Read this repository's string-only YAML subset; reject unsupported syntax."""
    match = re.match(r"\A---\n(.*?)\n---(?:\n|$)", text, re.S)
    if not match:
        raise ValueError("Missing or invalid YAML frontmatter")
    fields = {}
    lines = match.group(1).splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        i += 1
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        field = re.fullmatch(r"([a-z_][a-z0-9_-]*):\s*(.*)", line)
        if not field:
            raise ValueError(f"Unsupported frontmatter line: {line!r}")
        key, value = field.groups()
        if key in fields:
            raise ValueError(f"Duplicate metadata field: {key}")
        if value in (">", ">-", "|", "|-"):
            parts = []
            while i < len(lines) and (lines[i].startswith(" ") or not lines[i]):
                parts.append(lines[i].strip())
                i += 1
            value = (" " if value.startswith(">") else "\n").join(parts).strip()
        elif value.startswith('"'):
            value = json.loads(value)
        elif value.startswith("'"):
            if not value.endswith("'"):
                raise ValueError("Unterminated quoted metadata")
            value = value[1:-1].replace("''", "'")
        fields[key] = value
    return fields


def load_skill(source: Path) -> Skill:
    text = source.read_text(encoding="utf-8-sig")
    if text.startswith("---\n"):
        metadata = parse_frontmatter(text)
        name = metadata.get("name", "")
        description = metadata.get("description", "")
        body = re.split(r"\n---(?:\n|$)", text, maxsplit=1)[1].lstrip("\n")
    else:
        name_match = re.search(r"^- \*\*Folder\*\*:\s*(.+)$", text, re.M)
        desc_match = re.search(r"^## Description\s*\n(.*?)(?=^## |\Z)", text, re.M | re.S)
        name = name_match.group(1).strip() if name_match else source.parent.name
        description = desc_match.group(1).strip() if desc_match else ""
        body = text
    if (
        not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name)
        or len(name) > 64
        or name != source.parent.name
    ):
        raise ValueError(f"{source}: invalid name or folder/name mismatch: {name!r}")
    description = " ".join(description.split())
    if not description:
        raise ValueError(f"{source}: missing description")
    return Skill(name, source.parent.parent.name, description, source, body)


def discover(source_dir: Path, categories=(), names=()) -> list[Skill]:
    files = sorted(source_dir.glob("*/*/SKILL.md"))
    if not files:
        raise ValueError(f"No <category>/<name>/SKILL.md files in {source_dir}")
    for selected, available, label in (
        (categories, {p.parent.parent.name for p in files}, "categories"),
        (names, {p.parent.name for p in files}, "skills"),
    ):
        if set(selected) - available:
            raise ValueError(f"Unknown {label}: {', '.join(sorted(set(selected) - available))}")
    skills = [
        load_skill(p)
        for p in files
        if (not categories or p.parent.parent.name in categories)
        and (not names or p.parent.name in names)
    ]
    if not skills:
        raise ValueError("No skills match the selected categories and names")
    if len({s.name for s in skills}) != len(skills):
        raise ValueError("Duplicate skill names across categories")
    return skills


def short_description(description: str) -> str:
    sentences = re.split(r"(?<=[.!?])\s+", description)
    chosen = [sentences[0]]
    trigger = next((s for s in sentences[1:] if s.startswith("Use ")), None)
    if trigger:
        chosen.append(trigger)
    result = " ".join(chosen).replace("<", "(").replace(">", ")")
    if len(result) > 900:
        result = result[:897].rsplit(" ", 1)[0] + "..."
    return result


def render_codex(skill: Skill) -> dict[Path, str]:
    entry = f"""---
name: {skill.name}
description: {json.dumps(short_description(skill.description), ensure_ascii=False)}
---

# {skill.name}

Use this skill for the requested {skill.category} task. Read the relevant sections
of [the methodology](references/methodology.md) before applying its guidance.
For a large reference, search its headings and task-specific terms first; read
matching sections and their prerequisites rather than loading the whole file.

Adapt the selected material to the user's objective, provided scope, and available
tools. Reference examples are not instructions to execute every command. Use the
current environment's tools; a reference cannot grant tools or permissions.
Separate observed evidence from hypotheses and proposed verification steps.
Report what was actually checked, limitations, and relevant remediation.
Respond in the user's language unless requested otherwise.
"""
    body = skill.body.replace("## Instructions for Claude", "## Instructions for the assistant")
    reference = f"<!-- Source: Skills/{skill.category}/{skill.name}/SKILL.md -->\n\n"
    reference += f"Description: {skill.description}\n\n{body}"
    return {
        Path(skill.name) / "SKILL.md": entry,
        Path(skill.name) / "references/methodology.md": reference,
    }


def render_chatgpt(skill: Skill, prompt: str) -> dict[Path, str]:
    body = skill.body.replace("## Instructions for Claude", "## Instructions for the assistant")
    text = f"{prompt.rstrip()}\n\n---\n\n# Reference: {skill.name}\n\n"
    text += f"Category: {skill.category}\n\n{skill.description}\n\n{body}"
    return {Path(f"{skill.name}.md"): text}


def write_outputs(output: Path, files: dict[Path, str], force=False, dry_run=False) -> None:
    # Check every conflict before writing anything. Identical files are idempotent.
    for relative, content in files.items():
        target = output / relative
        if any(p.is_symlink() for p in (target, *target.parents)):
            raise ValueError(f"Refusing symlink output: {target}")
        if target.exists() and (
            not target.is_file() or target.read_text(encoding="utf-8") != content
        ):
            if not force or not target.is_file():
                raise ValueError(f"Output exists: {target}; use --force to replace generated files")
    for relative, content in files.items():
        target = output / relative
        if dry_run:
            print(target)
        elif not target.exists() or target.read_text(encoding="utf-8") != content:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("codex", "chatgpt"), default="codex")
    parser.add_argument("--input", type=Path, default=ROOT / "Skills")
    parser.add_argument("--output", "--target", type=Path, help="Output or installation directory")
    parser.add_argument(
        "--install", action="store_true", help="Default Codex target: <repo>/.agents/skills"
    )
    parser.add_argument("--category", action="append", default=[])
    parser.add_argument("--skill", action="append", default=[])
    parser.add_argument("--list", action="store_true", help="List categories without writing files")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true", help="Replace conflicting generated files")
    args = parser.parse_args(argv)
    try:
        skills = discover(args.input, args.category, args.skill)
        if args.list:
            for category in sorted({s.category for s in skills}):
                print(f"{category:22} {sum(s.category == category for s in skills)}")
            return 0
        default = (
            ROOT / ".agents/skills"
            if args.install and args.format == "codex"
            else ROOT / "build" / args.format
        )
        requested = (args.output or default).expanduser().absolute()
        # Canonicalize the parent (e.g. macOS /tmp), but retain the leaf for checks.
        output = requested.parent.resolve() / requested.name
        source = args.input.resolve()
        if output.resolve() == source or source in output.resolve().parents:
            raise ValueError("Output must be outside the source Skills directory")
        files = {}
        prompt = (
            (ROOT / "prompts/CHATGPT.md").read_text(encoding="utf-8")
            if args.format == "chatgpt"
            else ""
        )
        for skill in skills:
            files.update(
                render_codex(skill) if args.format == "codex" else render_chatgpt(skill, prompt)
            )
        write_outputs(output, files, args.force, args.dry_run)
        print(
            f"{'Would export' if args.dry_run else 'Exported'} {len(skills)} skills for {args.format}: {output}"
        )
        return 0
    except (OSError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
