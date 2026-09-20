#!/usr/bin/env bash
# Install Codex skills or export ChatGPT prompts; requires Python 3.9+.
# Use --help, --list, --category NAME, --skill NAME, --target DIR, or --dry-run.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$SCRIPT_DIR/convert_skills.py" --install "$@"
