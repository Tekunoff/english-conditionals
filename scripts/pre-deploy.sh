#!/usr/bin/env bash
# ============================================================
# pre-deploy.sh — прогоняет автотесты и пушит только если green
# Использование:
#   ./scripts/pre-deploy.sh "Commit message"
# ============================================================
set -e

COMMIT_MSG="${1:-Deploy}"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TESTS_DIR="$REPO_ROOT/tests"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🧪 Запуск автотестов перед деплоем..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cd "$TESTS_DIR"
npx playwright test --reporter=list

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ✅ Все тесты прошли. Деплоим..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cd "$REPO_ROOT"
git add -A
git commit -m "$COMMIT_MSG" || echo "Нечего коммитить — деплоим текущий HEAD"
git push

echo ""
echo "  🚀 Задеплоено: https://tekunoff.github.io/english-conditionals/"
echo ""
