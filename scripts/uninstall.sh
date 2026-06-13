#!/usr/bin/env bash
# Remove the javapaavi plugin and its marketplace from Claude Code.
#
# Usage:
#   ./scripts/uninstall.sh                 # uninstall plugin + remove marketplace (scope: user)
#   ./scripts/uninstall.sh --keep-marketplace
#   ./scripts/uninstall.sh --scope project
#
# After it finishes, run `/reload-plugins` in an active Claude Code session (or restart it).
set -euo pipefail

MARKETPLACE_NAME="javapaavi-marketplace"
PLUGIN_NAME="javapaavi"

SCOPE="user"
KEEP_MARKETPLACE=0
while [ $# -gt 0 ]; do
  case "$1" in
    --keep-marketplace) KEEP_MARKETPLACE=1; shift ;;
    --scope)            SCOPE="${2:?--scope needs a value}"; shift 2 ;;
    --scope=*)          SCOPE="${1#*=}"; shift ;;
    -h|--help)          sed -n '2,9p' "$0"; exit 0 ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
done

if ! command -v claude >/dev/null 2>&1; then
  echo "error: the 'claude' CLI is not on your PATH." >&2
  exit 1
fi

echo ">> uninstalling $PLUGIN_NAME (scope: $SCOPE)"
claude plugin uninstall "$PLUGIN_NAME" --scope "$SCOPE" || echo "   (plugin was not installed)"

if [ "$KEEP_MARKETPLACE" -eq 0 ]; then
  echo ">> removing marketplace $MARKETPLACE_NAME"
  claude plugin marketplace remove "$MARKETPLACE_NAME" || echo "   (marketplace was not configured)"
fi

cat <<'NEXT'

Removed. Run /reload-plugins in a running Claude Code session (or restart it).
NEXT
