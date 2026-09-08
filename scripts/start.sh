#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -c 'import sys; assert sys.version_info >= (3,11), "需要 Python 3.11 或更高版本"'
if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
if [ ! -f .venv/.draft-coach-installed ] || ! cmp -s requirements.lock .venv/.draft-coach-installed; then
  .venv/bin/python -m pip install -r requirements.lock
  cp requirements.lock .venv/.draft-coach-installed
fi
if [ ! -f .env ]; then cp .env.example .env; fi
if [ ! -f frontend/out/index.html ]; then
  if ! command -v npm >/dev/null 2>&1; then
    echo '需要 Node.js 22.13+ 来构建网页。安装后重新运行。'
    exit 1
  fi
  (cd frontend && npm ci && npm run build:local)
fi
echo 'Draft Coach: http://127.0.0.1:8000'
echo '按 Ctrl+C 停止。修改 .env 后需要重新启动。'
exec .venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
