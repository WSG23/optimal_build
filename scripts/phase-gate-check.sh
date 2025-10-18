#!/bin/bash
# Phase gate quality check before major milestone transitions
# Run this before completing any phase to ensure code quality standards are met

set -e

echo "🚦 Running Phase Gate Quality Check..."
echo ""
echo "This verifies the codebase is ready for phase transition by running:"
echo "  - Code formatting checks (Black, Prettier)"
echo "  - Linting (Ruff, Flake8, ESLint)"
echo "  - Coding rules verification"
echo "  - Test suite"
echo ""

if make verify; then
    echo ""
    echo "✅ Phase gate PASSED - Code quality standards met"
    echo "   Ready for phase transition"
    echo ""
    exit 0
else
    echo ""
    echo "❌ Phase gate FAILED - Code quality violations detected"
    echo ""
    echo "Fix violations before completing phase transition:"
    echo "  1. Run 'make format' to auto-fix formatting"
    echo "  2. Run 'make verify' to see remaining issues"
    echo "  3. Fix any remaining violations manually"
    echo "  4. Re-run this script"
    echo ""
    exit 1
fi
