#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
GODOT_BIN="${GODOT_BIN:-/Applications/Godot.app/Contents/MacOS/Godot}"
BASE="${1:-$ROOT/src/build/sector_01_cerberus_corridor}"
exec "$GODOT_BIN" --headless --fixed-fps 60 --path "$ROOT/src/engine/physics" --log-file /tmp/momentum-godot-audit.log --script "$ROOT/src/engine/godot_audit_physics.gd" -- "$BASE.physics.glb" "$BASE.physics.json" "${2:-1000}" "${3:-$BASE.audit.json}"
