#!/usr/bin/env bash
# Run locally only when ready to create your private GitHub repository.
set -euo pipefail
cd "$(dirname "$0")/.."
command -v gh >/dev/null 2>&1 || { echo '需要 GitHub CLI (gh)。也可以在 github.com/new 手动创建仓库。'; exit 1; }
gh auth status
if [ ! -d .git ]; then
  git init -b main
  git add .
  git commit -m "Build personalized League draft coach MVP"
fi
gh repo create lol-draft-coach --private --source . --remote origin --push
