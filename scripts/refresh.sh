#!/usr/bin/env bash
# Refresh the local reference corpus used to (re-)distill the javapaavi skills.
# The corpus itself is gitignored — only the resulting SKILL.md edits should be
# committed.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [ ! -d .venv ]; then
  echo ">> creating virtualenv"
  python3 -m venv .venv
  .venv/bin/pip install --quiet beautifulsoup4 requests lxml
fi

echo ">> scraping blog into plugins/javapaavi/reference/posts/"
.venv/bin/python scripts/scrape_blog.py --out plugins/javapaavi/reference/posts

cat <<'NEXT'

Corpus refreshed. Next step:
  Open this repo in Claude Code and ask the assistant to:

    "Refresh the five javapaavi skills from the reference/posts/ corpus.
     Bias toward post-2022 content and explicitly note where Petri's
     thinking has evolved versus older posts."

The reference/posts/ directory is .gitignored — only the SKILL.md edits
should be committed.
NEXT
