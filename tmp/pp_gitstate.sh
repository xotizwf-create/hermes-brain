#!/usr/bin/env bash
set -uo pipefail
cd /var/www/prostye-postavki/app || exit 1
echo "branch: $(git rev-parse --abbrev-ref HEAD)"
echo "--- status ---"
git status --porcelain | head -10
echo "--- last 6 local ---"
git log --oneline -6
echo "--- local-only commits (HEAD not on origin/Создание-документов) ---"
git log --oneline origin/Создание-документов..HEAD | head -20
echo "--- origin-only commits (origin ahead of HEAD) ---"
git log --oneline HEAD..origin/Создание-документов | head -20
echo "--- merge-base ---"
git merge-base HEAD origin/Создание-документов | head -1
