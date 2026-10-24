#!/bin/bash
# Developer workstation: use installed Python/Blender and the local asset library.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND_PID=""
cleanup() { if [ -n "$BACKEND_PID" ]; then kill "$BACKEND_PID" 2>/dev/null || true; fi; }
trap cleanup EXIT INT TERM
if ! curl -fsS http://127.0.0.1:8018/api/v1/health >/dev/null; then
    (cd "$ROOT/src" && exec "${MOMENTUM_PYTHON:-python3}" -m uvicorn server.app:app --host 127.0.0.1 --port 8018) &
    BACKEND_PID=$!
fi
for i in {1..50}; do
    if curl -fsS http://127.0.0.1:8018/api/v1/health >/dev/null; then break; fi
    sleep 0.1
done
curl -fsS http://127.0.0.1:8018/api/v1/health >/dev/null
cd "$ROOT"
if [ "${1:-}" = "--app" ]; then
    "$ROOT/src-tauri/target/release/bundle/macos/MomentumStudio AI.app/Contents/MacOS/momentum-studio"
else
    cargo tauri dev
fi
