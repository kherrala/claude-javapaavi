#!/usr/bin/env bash
# Install the javapaavi plugin into Claude Code via the `claude` CLI.
#
# Usage:
#   ./scripts/setup.sh                 # install from GitHub (kherrala/claude-javapaavi)
#   ./scripts/setup.sh --local         # install from THIS checkout (for local development)
#   ./scripts/setup.sh --scope project # install scope: user (default) | project | local
#
# Requires the `claude` CLI on PATH (Claude Code 2.x). After it finishes, run
# `/reload-plugins` in an active Claude Code session (or restart it) to load the plugin.
set -euo pipefail

MARKETPLACE_NAME="javapaavi-marketplace"
PLUGIN_NAME="javapaavi"
GITHUB_SOURCE="kherrala/claude-javapaavi"

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

SOURCE="$GITHUB_SOURCE"
SCOPE="user"
while [ $# -gt 0 ]; do
  case "$1" in
    --local)        SOURCE="$ROOT"; shift ;;
    --scope)        SCOPE="${2:?--scope needs a value}"; shift 2 ;;
    --scope=*)      SCOPE="${1#*=}"; shift ;;
    -h|--help)      sed -n '2,12p' "$0"; exit 0 ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
done

if ! command -v claude >/dev/null 2>&1; then
  echo "error: the 'claude' CLI is not on your PATH. Install Claude Code first: https://claude.com/claude-code" >&2
  exit 1
fi

echo ">> marketplace: $MARKETPLACE_NAME (source: $SOURCE)"
if claude plugin marketplace list 2>/dev/null | grep -q "$MARKETPLACE_NAME"; then
  echo "   already configured — refreshing from source"
  claude plugin marketplace update "$MARKETPLACE_NAME"
else
  claude plugin marketplace add "$SOURCE" --scope "$SCOPE"
fi

echo ">> installing $PLUGIN_NAME@$MARKETPLACE_NAME (scope: $SCOPE)"
claude plugin install "$PLUGIN_NAME@$MARKETPLACE_NAME" --scope "$SCOPE"

cat <<'NEXT'

Done. To load it into a running Claude Code session:

    /reload-plugins

(or restart Claude Code). Verify with:  claude plugin list
NEXT
