# Founder's Procurement & Operational Boundary Guide
**Company:** MomentumStudio AI  
**Founder:** Deevash  
**Chief AI Architect:** Antigravity Master Orchestrator  
**Document Version:** 1.0 (MVP Milestone)  
**Date:** October 23, 2026  

---

## 1. Executive Summary & Purpose

MomentumStudio AI ("The Cursor for 3D Game Worlds") is built as an autonomous, agent-native desktop studio. It replaces traditional 10,000-button 3D DCC software (Blender, Maya, 3ds Max) with an intent-driven spatial world compiler. 

To execute this startup at venture scale with maximum capital efficiency, the technical division of labor must be crystal clear. This guide outlines:
1. **Resource Procurement:** Exact steps for the founder to obtain, link, and configure every software, engine, asset, and API dependency.
2. **Operational Matrix:** A transparent, non-negotiable boundary detailing **What the AI Agent CAN Do** versus **What the AI Agent CANNOT Do (Founder Responsibilities)**.

---

## 2. Resource Procurement Guide (Founder Action Items)

### 2.1 3D Engines & CLI Binaries (Zero Cost — Already on Mac!)
Both required 3D engines are already installed in `/Applications/` on your Mac. You simply need to symlink them so the terminal and automated daemons can execute them globally.

#### Blender 5.2.1 LTS
- **Location on Mac:** `/Applications/Blender.app/Contents/MacOS/Blender`
- **CLI Symlink Command (Run in Terminal):**
  ```bash
  sudo ln -sf /Applications/Blender.app/Contents/MacOS/Blender /usr/local/bin/blender
  # Verify installation:
  blender --version
  ```
- **Purpose:** Headless procedural geometry generation, KDTree spline corridor collision auditing, Draco `.glb` mesh compression, and Cycles/Eevee baking.

#### Godot 4.7.1 LTS
- **Location on Mac:** `/Applications/Godot.app/Contents/MacOS/Godot`
- **CLI Symlink Command (Run in Terminal):**
  ```bash
  sudo ln -sf /Applications/Godot.app/Contents/MacOS/Godot /usr/local/bin/godot
  # Verify installation:
  godot --version
  ```
- **Purpose:** Headless physics simulation testing, dynamic light pooling validation (6 lights max), 60 FPS viewport rendering, and multiplatform game exports (macOS, Windows, Linux, WebGL).

---

### 2.2 Native Desktop Application Packaging (Zero Cost)
To bundle MomentumStudio into a standalone macOS native `.app` and `.dmg` that runs with native performance without needing a browser window:

#### Rust & Tauri CLI
- **Installation Command:**
  ```bash
  # 1. Install Rust compiler (if not already installed):
  curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
  source "$HOME/.cargo/env"

  # 2. Install Tauri CLI:
  cargo install tauri-cli --version "^2.0.0"
  ```
- **Why Tauri v2?** Tauri uses WebKit on macOS, producing ultra-lightweight binaries (<15 MB vs Electron's 200 MB), sub-50ms cold starts, and zero RAM bloat.

---

### 2.3 CC0 Open Source 3D Asset Libraries (Zero Cost, 100% Commercial Cleared)
The agent needs pre-indexed modular 3D assets to assemble into macro game worlds. All of these are 100% free and CC0 Public Domain:

1. **Kenney Game Assets (CC0):**
   - **URL:** [https://kenney.nl/assets](https://kenney.nl/assets)
   - **Key Packs:** *Sci-Fi Kit*, *City Kit Commercial*, *Nature Kit*, *Car Kit*.
   - **Procurement:** Download the all-in-one ZIP (~500 MB) and place it into `~/Desktop/MomentumStudio_AI/assets/kenney/`.
2. **Poly Haven (CC0 PBR Textures & HDRI Skylights):**
   - **URL:** [https://polyhaven.com](https://polyhaven.com)
   - **API Endpoint:** `https://api.polyhaven.com/assets` (The agent can query this directly via script!).
3. **ambientCG (CC0 PBR Materials):**
   - **URL:** [https://ambientcg.com](https://ambientcg.com)
   - High-resolution asphalt, rusted metal, wet concrete, and cyber holographic materials.

---

### 2.4 AI Spatial Reasoning APIs (Low Cost / Free Tier)
To give MomentumStudio natural language comprehension ("Cursor for 3D"):

1. **Google Gemini 2.5 Flash / Pro API Key:**
   - **How to get:** Go to [Google AI Studio](https://aistudio.google.com/), click **Create API Key**, and copy the token.
   - **Cost:** Free tier includes 15 RPM; paid tier is ~$0.075 per 1M input tokens (almost free).
   - **Setup:** Add to your environment:
     ```bash
     export GEMINI_API_KEY="AIzaSy..."
     ```
2. **Anthropic Claude 3.7 Sonnet / OpenAI API Key (Optional Alternative):**
   - For spatial JSON planning and complex geometry math validation.

---

## 3. Transparent Operational Matrix: What AI CAN Do vs. What AI CANNOT Do

| Capability Domain | What the AI Agent CAN Do (100% Autonomous) | What the AI Agent CANNOT Do (Founder Action Required) |
| :--- | :--- | :--- |
| **Code & Architecture** | • Write 100% of Python, JavaScript, HTML/CSS, GDScript, and C++ code.<br>• Architect schemas, JSON-RPC IPC sockets, and FastAPI servers.<br>• Implement 3D KDTree spatial algorithms and Draco compression. | • Cannot decide the ultimate product-market vision without founder feedback.<br>• Cannot modify code outside workspace without user permissions. |
| **Engine Automation** | • Run headless Blender (`bpy`) and Godot (`--headless`) scripts in background.<br>• Generate 3D procedural meshes, track curves, and light fixtures.<br>• Audit scene geometry for clearance and light budgets. | • Cannot physically click inside an active Blender GUI interactive window (operates via CLI/IPC).<br>• Cannot resolve native macOS display driver faults. |
| **Financial & Accounts** | • Calculate unit economics, server costs, and token consumption.<br>• Design Stripe webhook logic and pricing tier architectures. | • **CANNOT enter credit cards or pay bills**.<br>• **CANNOT sign up for paid subscriptions** (OpenAI, Google Cloud, Apple Dev).<br>• **CANNOT open bank accounts (Mercury, Brex)**. |
| **Auth & Security** | • Write zero-trust auth middleware, JWT generators, and crypto signing.<br>• Encrypt local IPC sockets and validate CORS allowlists. | • **CANNOT solve CAPTCHAs or MFA/SMS prompts**.<br>• **CANNOT access personal accounts without user-provided API tokens**. |
| **macOS & Deployment** | • Compile and launch local HTTP daemons, WebSockets, and Three.js clients.<br>• Author Tauri desktop config files (`tauri.conf.json`).<br>• Push structured Git commits to GitHub. | • **CANNOT sign macOS apps with Apple Developer ID** ($99/yr Apple certificate required for Gatekeeper).<br>• **CANNOT bypass Apple notarization without founder credentials**. |
| **Hardware Limits** | • Monitor RAM usage and optimize algorithms to run under 100ms.<br>• Partition 60-sector scenes into streaming 3-chunk windows. | • **CANNOT upgrade physical RAM or GPU cores** on your Mac.<br>• Cannot prevent thermal throttling if rendering 8K Cycles scenes for hours. |

---

## 4. Immediate Founder Checklist (Next 10 Minutes)

1. [ ] **Link CLI Binaries:** Run the two `sudo ln -sf` commands above for Blender and Godot.
2. [ ] **Set API Key:** Export your `GEMINI_API_KEY` into your shell configuration (`~/.zshrc`).
3. [ ] **Launch Studio MVP:** Run `./run_studio.sh` inside `~/Desktop/MomentumStudio_AI/src/` to verify local operation.
4. [ ] **Sync with GitHub:** Review the automated GitHub repository push.

---
*Authored autonomously by Antigravity Master Orchestrator for Founder Deevash.*
