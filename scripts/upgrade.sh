#!/usr/bin/env bash
# Upgrade an already-installed javapaavi plugin to the latest version.
#
# Usage:
#   ./scripts/upgrade.sh                 # refresh marketplace + update plugin (scope: user)
#   ./scripts/upgrade.sh --scope project # update scope: user (default) | project | local | managed
#
# Requires the `claude` CLI on PATH. After it finishes, run `/reload-plugins`
# in an active Claude Code session (or restart it) to apply the update.
set -euo pipefail

MARKETPLACE_NAME="javapaavi-marketplace"
PLUGIN_NAME="javapaavi"

SCOPE="user"
while [ $# -gt 0 ]; do
  case "$1" in
    --scope)   SCOPE="${2:?--scope needs a value}"; shift 2 ;;
    --scope=*) SCOPE="${1#*=}"; shift ;;
    -h|--help) sed -n '2,11p' "$0"; exit 0 ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
done

if ! command -v claude >/dev/null 2>&1; then
  echo "error: the 'claude' CLI is not on your PATH. Install Claude Code first: https://claude.com/claude-code" >&2
  exit 1
fi

if ! claude plugin marketplace list 2>/dev/null | grep -q "$MARKETPLACE_NAME"; then
  echo "error: marketplace '$MARKETPLACE_NAME' is not configured — run ./scripts/setup.sh first." >&2
  exit 1
fi

echo ">> refreshing marketplace $MARKETPLACE_NAME from source"
claude plugin marketplace update "$MARKETPLACE_NAME"

echo ">> updating $PLUGIN_NAME@$MARKETPLACE_NAME (scope: $SCOPE)"
claude plugin update "$PLUGIN_NAME@$MARKETPLACE_NAME" --scope "$SCOPE"

cat <<'NEXT'

Updated. A restart is required to apply — in a running session run:

    /reload-plugins

(or restart Claude Code). Verify with:  claude plugin list
NEXT
