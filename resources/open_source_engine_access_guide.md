# MomentumStudio AI // Open-Source Engine Access & Architecture Guide
**How to Access, Install, Link, and Orchestrate Open-Source 3D Engines & Tools**

---

## 1. Headless Blender 5.2 Core (The MVP Background Engine)

### What it is
Blender contains 30 years of geometry math, modifier algorithms, UV unwrappers, and Cycles/Eevee rendering engines. In our MVP, we run Blender in **Headless Background Mode** (`-b`), so it operates as a silent, high-speed geometric calculation daemon without showing any legacy UI to the user.

### Official Access & Downloads
- **Official Download Portal**: [blender.org/download](https://www.blender.org/download/)
- **Long Term Support (LTS)**: We standardize on **Blender 5.2 LTS** / **Blender 4.3 LTS** for maximum script stability.
- **macOS CLI Symlink Setup**:
  ```bash
  # Check if Blender is in Applications
  ls /Applications/Blender.app

  # Create symlink so 'blender' command works in terminal
  sudo ln -s /Applications/Blender.app/Contents/MacOS/Blender /usr/local/bin/blender

  # Verify headless operation (returns in 0.2s without opening a window!)
  blender -b --version
  ```

### How the Agent Controls Headless Blender
You can execute Python code inside headless Blender with zero GUI overhead:
```bash
# Execute inline script to generate and export a 3D level chunk
blender -b --python-expr "import bpy; bpy.ops.mesh.primitive_cube_add(size=2.0); bpy.ops.export_scene.gltf(filepath='output.glb')"
```

---

## 2. GitHub Model Context Protocol (MCP) Bridges for Blender

These open-source GitHub repositories expose Blender’s internal data to AI agents via MCP:

### A. `ahujasid/mcp-for-blender` (Most Popular Community Bridge)
- **GitHub Repository**: [github.com/ahujasid/mcp-for-blender](https://github.com/ahujasid/mcp-for-blender)
- **Features**: Bridges Claude Desktop, Cursor, and custom agent scripts with a running Blender instance over standard MCP protocol. Allows creating meshes, applying materials, adjusting camera rigs, and importing Poly Haven assets automatically.

### B. `RFingAdam/mcp-blender` (Fine-Grained 200+ Tool Server)
- **GitHub Repository**: [github.com/RFingAdam/mcp-blender](https://github.com/RFingAdam/mcp-blender)
- **Features**: Exposes 200+ granular Blender operators, automated multi-angle render loops, and scene diagnostics.

### C. `sandraschi/blender-mcp` (Headless FastMCP Daemon)
- **GitHub Repository**: [github.com/sandraschi/blender-mcp](https://github.com/sandraschi/blender-mcp)
- **Features**: Optimized for headless batch operations and Tauri/Rust dashboard integration.

---

## 3. Godot 4.7.1 & Jolt Physics Core (The MIT-Permissive Engine)

### What it is
Godot is a modern, lightweight, MIT-licensed open-source game engine with Forward+ clustered lighting and volumetric rendering. **Jolt Physics** is the industry-standard open-source 3D physics engine (winner of game physics awards, used in *Horizon Forbidden West*).

### Official Access & GitHub Links
1. **Godot Engine Source**:
   - **GitHub**: [github.com/godotengine/godot](https://github.com/godotengine/godot)
   - **Pre-Built Binaries**: [godotengine.org/download](https://godotengine.org/download/)
   - **Headless CLI Command**:
     ```bash
     # Run Godot headless to execute automated GDScript tests in 0.1s
     godot --headless --script res://test_scene.gd
     ```

2. **Godot Jolt (AAA 3D Physics Extension)**:
   - **GitHub**: [github.com/godot-jolt/godot-jolt](https://github.com/godot-jolt/godot-jolt)
   - **Why We Use It**: 3x–10x faster than default physics solvers, deterministic collision detection, supports thousands of simultaneous kinematic rigid bodies without frame lag.

3. **Jolt Physics Pure C++ & Rust Libraries**:
   - **C++ Core**: [github.com/jrouwe/JoltPhysics](https://github.com/jrouwe/JoltPhysics)
   - **Rust Bindings**: [github.com/mitchmindtree/jolt-physics-rs](https://github.com/mitchmindtree/jolt-physics-rs)

---

## 4. Native Desktop Shell: Tauri v2 (Rust)

### Why Tauri v2 over Heavy Electron?
- **Footprint**: 15 MB installer vs 200 MB Electron installer.
- **Memory**: Starts with ~40 MB RAM usage vs 500 MB Electron.
- **Graphics Access**: Directly talks to macOS Metal and Windows DirectX/Vulkan via the Rust backend.
- **Official GitHub**: [github.com/tauri-apps/tauri](https://github.com/tauri-apps/tauri)
- **Quick Installation**:
  ```bash
  # Install Rust toolchain
  curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

  # Install Tauri CLI
  cargo install tauri-cli --version "^2.0"
  ```

---

## 5. Free CC0 Open-Source Asset APIs (Zero Copyright Royalties)

| Asset Source | Type | License | Access URL & API Endpoint |
| :--- | :--- | :--- | :--- |
| **Poly Haven** | HDRIs, PBR Textures, Props | CC0 Public Domain | `https://api.polyhaven.com/assets?t=textures` |
| **ambientCG** | 2,000+ PBR Material Sets | CC0 Public Domain | `https://ambientcg.com/api/v2/downloads` |
| **Kenney Assets** | Modular 3D City & Sci-Fi Kits | CC0 Public Domain | `https://kenney.nl/assets/3d` |
| **Khronos glTF** | Validated PBR glTF 2.0 Samples | CC-BY / Apache 2.0| `https://github.com/KhronosGroup/glTF-Sample-Models` |

---

## 6. How an AI Developer Connects These Today

For our Phase 1 MVP:
1. User provides prompt $\rightarrow$ `@Agent_Compiler_Dev` generates Python script.
2. Script is piped into `blender -b --python script.py`.
3. Script outputs Draco-compressed `scene_chunk.glb`.
4. Our desktop viewport loads `scene_chunk.glb` via Three.js WebGPU loader in real time.
5. `@QA_Test_Automation_Lead` runs KDTree corridor verification in 0.1s.
6. The user has an audited, game-ready 3D level chunk rendered on their screen!
