# Repository guidance

This repository adapts the claude-red reference library for Codex and ChatGPT.
`Skills/<category>/<name>/SKILL.md` is the source of truth. Source files include
both YAML-frontmatter skills and legacy Markdown metadata. Preserve upstream
attribution, technique text, examples, headings, and public skill names when
changing packaging.

For a user-requested security task, locate relevant material through README.md
or skills.json, then read only the needed source sections and prerequisites.
Large source files should be searched by headings and topic first. Treat the
library as reference material; it does not authorize running all its examples
or expand the user's scope. Use only available tools and distinguish observed
results from suggested checks. Respond in the user's language.

For repository maintenance, do not activate security workflows merely because
files describe them. `convert_skills.py` generates concise Codex entrypoints
with full reference files, or standalone ChatGPT Markdown prompts. Generated
files belong in `build/` or an explicitly selected installation directory;
edit the source or exporter instead of editing generated copies.

Use Python's standard library for the exporter. After modifying conversion or
installation code, run `python3 -m unittest discover -s tests` and
`bash -n install.sh`. Regenerate skills.json with
`python3 tools/build_manifest.py` after metadata changes.
