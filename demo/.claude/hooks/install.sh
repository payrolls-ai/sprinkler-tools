#!/usr/bin/env bash
# .claude/hooks/install.sh
# One-time setup: link the hooks into .git/hooks
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
HOOKS_SRC="$REPO_ROOT/.claude/hooks"
HOOKS_DST="$REPO_ROOT/.git/hooks"

mkdir -p "$HOOKS_DST"

for hook in pre-commit; do
    src="$HOOKS_SRC/$hook"
    dst="$HOOKS_DST/$hook"
    if [ -f "$dst" ] && [ ! -L "$dst" ]; then
        echo "⚠ $dst already exists and is not a symlink — skipping"
        continue
    fi
    ln -sf "$src" "$dst"
    chmod +x "$src"
    echo "✓ Installed $hook"
done

echo ""
echo "Hooks installed. Test with:  git commit --allow-empty -m 'test'"
