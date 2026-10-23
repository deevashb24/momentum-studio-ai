# MomentumStudio AI // Resource Requirements Manifest
**Complete Hardware, Software, API & Open-Source Stack Specifications**

---

## 1. Core Software & Runtime Stack

| Component | Technology | Version | Purpose / Architecture | License |
| :--- | :--- | :--- | :--- | :--- |
| **Desktop Shell** | **Tauri v2** | `v2.x` | Native macOS (Metal) & Windows (DirectX/Vulkan) window host with Rust backend | MIT / Apache 2.0 |
| **System Language** | **Rust** | `1.80+` | Memory-safe, high-speed IPC sockets, FFI bindings, and multithreaded spatial indexing | MIT / Apache 2.0 |
| **Frontend UI** | **Next.js 16 / React 19** | `16.x / 19.x` | High-density developer interface (Tailwind CSS v4 + Lucide icons) | MIT |
| **3D WebGPU Viewport** | **Three.js / WebGPU** | `r170+` | Hardware-accelerated local 3D rendering inside the native desktop window | MIT |
| **Headless 3D Core** | **Blender 5.2.1 LTS** | `5.2.1` | Headless background daemon for modifier DAG evaluation, mesh operations, and Draco glTF export | GPL v3 (IPC-isolated) |
| **Physics Engine** | **Jolt Physics** | `v5.2+` | AAA-grade rigid-body, ragdoll, and kinematic collision physics (C++ / `jolt-physics-rs`) | MIT |
| **Target Game Engine** | **Godot Engine** | `4.7.1-stable` | Reference game engine for real-time playtesting, scene verification, and 1-click export | MIT |

---

## 2. AI Model & API Infrastructure

| Model / Service | Role in MomentumStudio | Access Method / Environment Variable |
| :--- | :--- | :--- |
| **Anthropic Claude 3.7 Sonnet / 3.5 Sonnet** | Primary Code & Spatial AST Compiler (Deep thinking & complex Python script synthesis) | `ANTHROPIC_API_KEY` |
| **Google Gemini 2.5 / 2.0 Pro** | Multimodal Spatial Critic (Orthogonal screenshot analysis, visual QA, silhouette verification) | `GEMINI_API_KEY` |
| **Seedance 2.5 (ByteDance / SeaDance)** | Generative Concept Video Engine (Photorealistic mood generation & cinematic trailer synthesis) | Web API / Session Key |
| **Local LLM Fallback (Ollama / MLX)** | Offline generation on Apple Silicon / RTX workstations (Llama 3.3 70B / Qwen 2.5 Coder) | Local Socket (`http://127.0.0.1:11434`) |

---

## 3. Open-Source Asset Hubs & Free Texture Resources

To give users an immediate rich library of materials, HDRIs, and props without licensing royalties:

1. **Poly Haven (`polyhaven.com`)**:
   - 100% CC0 (Public Domain) HDRIs, 1K–8K PBR materials (Albedo, Normal, Roughness, AO), and modular 3D models.
   - Accessible via direct API (`https://api.polyhaven.com/assets`).
2. **ambientCG (`ambientcg.com`)**:
   - 2,000+ free CC0 PBR material sets (asphalt, concrete, metals, glass, stone) in PNG/JPG formats.
3. **Kenney Game Assets (`kenney.nl`)**:
   - 1,000+ CC0 modular low-poly kit pieces (sci-fi city kits, road kits, space kits) perfect for procedural blockout prototyping.
4. **Khronos glTF Sample Models**:
   - Reference Draco-compressed glTF 2.0 models for importer verification.

---

## 4. Hardware Development Specifications

- **Target Workstation (Recommended)**:
  - Apple Silicon Mac (M1 Pro / M2 Pro / M3 Max / M4 with 32GB+ Unified Memory).
  - PC: Intel i7/i9 or AMD Ryzen 9, 32GB RAM, NVIDIA RTX 3080/4080/5090 with 16GB+ VRAM.
- **Minimum Viable Hardware**:
  - 16GB RAM, integrated GPU capable of WebGPU / Metal 2.0.
