#!/bin/bash
# Install git hooks for code quality enforcement
# Run this after cloning the repository

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOOKS_DIR="$REPO_ROOT/.git-hooks"
GIT_HOOKS_DIR="$REPO_ROOT/.git/hooks"

echo "🔧 Installing git hooks..."
echo ""

# Create symlinks for hooks
if [ -f "$HOOKS_DIR/pre-push" ]; then
    ln -sf "../../.git-hooks/pre-push" "$GIT_HOOKS_DIR/pre-push"
    chmod +x "$GIT_HOOKS_DIR/pre-push"
    echo "✅ Installed pre-push hook"
else
    echo "⚠️  Warning: pre-push hook not found in $HOOKS_DIR"
fi

echo ""
echo "✅ Git hooks installed successfully!"
echo ""
echo "These hooks will:"
echo "  - Run formatting checks before push"
echo "  - Run linting before push"
echo "  - Check coding rules before push"
echo ""
echo "To bypass (not recommended):"
echo "  SKIP_PRE_PUSH_CHECKS=1 git push"
echo ""
