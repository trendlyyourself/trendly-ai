#!/data/data/com.termux/files/usr/bin/bash
set -e

cd "$(dirname "$0")"

if [ ! -f .env ]; then
  cp .env.example .env
fi

python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
