#!/bin/bash
# MomentumStudio AI — 1-Click Startup Launcher
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="$SCRIPT_DIR/src"

echo "=========================================================="
echo "🚀 Launching MomentumStudio AI — The Cursor for 3D Game Worlds"
echo "=========================================================="

# 1. Environment Verification
echo "[1/4] Checking 3D Engine Dependencies..."
BLENDER_PATH="/Applications/Blender.app/Contents/MacOS/Blender"
GODOT_PATH="/Applications/Godot.app/Contents/MacOS/Godot"

if [ -f "$BLENDER_PATH" ]; then
    echo "  ✅ Headless Blender 5.2.1 LTS located at $BLENDER_PATH"
else
    echo "  ⚠️ Warning: Blender not found at $BLENDER_PATH. Make sure Blender 5.2.1 LTS is installed."
fi

if [ -f "$GODOT_PATH" ]; then
    echo "  ✅ Godot 4.7.1 LTS located at $GODOT_PATH"
fi

# 2. Pre-compile default scene
echo "[2/4] Verifying default scene compilation..."
if [ ! -f "$SRC_DIR/build/sector_01_cerberus_corridor.glb" ]; then
    echo "  ⚡ Compiling initial sector_01_cerberus_corridor.glb..."
    "$BLENDER_PATH" -b --python-exit-code 1 --python "$SRC_DIR/engine/blender_compile_chunk.py" -- \
        "$SRC_DIR/scenes/sector_01_cerberus_corridor.world.json" \
        "$SRC_DIR/build/sector_01_cerberus_corridor.glb"
fi
echo "  ✅ Draco glTF scene asset verified."

# 3. Start Local HTTP & IPC Engine Daemon
echo "[3/4] Starting MomentumStudio Engine Server on http://127.0.0.1:8018..."
cd "$SRC_DIR"
export PYTHONPATH="$SRC_DIR:$PYTHONPATH"

# Open browser in 1 second
(sleep 1.2 && open "http://127.0.0.1:8018/studio/") &

# Launch FastAPI Server
python3 -m uvicorn server.app:app --host 127.0.0.1 --port 8018 --reload
