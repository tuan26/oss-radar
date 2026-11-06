#!/usr/bin/env sh
# Chạy OSS Radar không cần Docker (macOS / Linux)
set -e
cd "$(dirname "$0")"
PY=${PYTHON:-python3}
if [ ! -d .venv ]; then
  echo "Tạo môi trường ảo .venv ..."
  "$PY" -m venv .venv
fi
. .venv/bin/activate
pip install -q --disable-pip-version-check -r requirements.txt
export DATA_DIR="${DATA_DIR:-$(pwd)/data}"
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8080}"
echo "OSS Radar chạy tại http://localhost:$PORT  (Ctrl+C để dừng)"
exec python -m uvicorn app.main:app --host "$HOST" --port "$PORT"
