#!/usr/bin/env bash
# Upload files or folders to shrenp.com over SSH — no editor plugin, no password, no FTP quota.
#
#   scripts/deploy.sh word-bubbles index.html sitemap.xml
#   scripts/deploy.sh -n word-bubbles          # dry run: list what would change
#
# Paths are relative to the repo root and land at the same path under public_html.
# Signs in with the deploy key ~/.ssh/shrenp_deploy (cPanel → SSH Access → Manage SSH Keys);
# override with SHRENP_SSH_USER / SHRENP_SSH_HOST / SHRENP_SSH_KEY (env or .env).
set -euo pipefail

cd "$(dirname "$0")/.."
[ -f .env ] && set -a && . ./.env && set +a

HOST="${SHRENP_SSH_HOST:-shrenp.com}"
USER="${SHRENP_SSH_USER:-dqoxg1st3y9x}"
KEY="${SHRENP_SSH_KEY:-$HOME/.ssh/shrenp_deploy}"

dry=""
[ "${1:-}" = "-n" ] && { dry="--dry-run"; shift; }
[ $# -gt 0 ] || { echo "usage: scripts/deploy.sh [-n] <file-or-folder>..." >&2; exit 1; }
for p in "$@"; do [ -e "$p" ] || { echo "not found: $p" >&2; exit 1; }; done

# rsync writes each file under a temporary name and renames it once complete, so a failed
# transfer never leaves a half-written page live. --relative keeps each path as given
# (word-bubbles/x → public_html/word-bubbles/x). Nothing on the server is ever deleted, and
# live databases (*.sqlite) are never overwritten.
rsync -rtz --itemize-changes --relative ${dry:+"$dry"} \
  --exclude .DS_Store --exclude '*.sqlite*' --exclude '*.map' \
  -e "ssh -i $KEY -o IdentitiesOnly=yes -o BatchMode=yes" \
  "${@%/}" "$USER@$HOST:public_html/"
echo "done${dry:+ (dry run)} → https://shrenp.com/"
