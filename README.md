> **Phase 2 status:** modular assets, native macOS wrapper and Jolt auditor are implemented. See [development and validation notes](resources/phase2_development.md) for verified results and current Blender/DMG blockers. Historical benchmarks below are not current end-to-end measurements.

# MomentumStudio AI // The Autonomous Agent-Native 3D World Studio
**"The Cursor for 3D Game Worlds" — Founded by Deevash (Founder & CEO)**

---

## 1. Executive Mission
**MomentumStudio AI** is a next-generation native desktop application that replaces traditional 10,000-button 3D DCC tools (like Blender and Maya) with an **autonomous, agent-native spatial world compiler**. 

Instead of manual vertex pushing, artists and game developers direct an intelligent team of AI sub-agents to compile, audit, and render game-ready, photorealistic 3D environments with full clustered PBR lighting, Jolt physics, and guaranteed mathematical collision clearance.

---

## 2. Desktop Hub Directory Map

```
~/Desktop/MomentumStudio_AI/
├── README.md                      # Primary company briefing and hub index
├── plans/                         # Master implementation roadmaps and resource requirements
│   ├── 01_master_startup_implementation_plan.md
│   └── 02_resource_requirements_manifest.md
├── resources/                     # Open-source engines, kernels, and asset procurement links
│   └── open_source_engine_access_guide.md
├── team/                          # Org chart, sub-agent employee personas, and responsibilities
│   └── company_org_chart_and_agent_manifest.md
├── journal/                       # Architectural decisions, reasoning logs, and the founder journey
│   └── 01_founding_story_and_architectural_journey.md
├── messages/                      # Asynchronous cross-agent handover logs (Antigravity ↔ ChatGPT)
│   └── 2026-10-23_21-00-00_Antigravity_to_ChatGPT.md
├── daily_reports/                 # Chronological daily status reports and milestone velocity
│   └── 2026-10-23_founding_day_report.md
├── artifacts/                     # Technical specifications, schemas (.world.json), and diagrams
│   └── momentum_studio_system_architecture.md
└── src/                           # Native desktop application source code and MVP prototypes
```

---

## 3. The Tripartite Co-Founder Operating Model

To guarantee continuous 24/7 momentum without being bottlenecked by token or credit limits across any single AI provider, MomentumStudio operates on a **Tripartite Multi-Agent Collaboration Protocol**:

1. **The Founder & CEO (Deevash)**: Sets vision, directs architecture, makes executive product decisions, and commands the team.
2. **Master Orchestrator A (Antigravity / DeepMind)**: Leads system architecture, heavy code generation, test automation, and local execution.
3. **Master Orchestrator B (ChatGPT / Codex / OpenAI)**: Continues active development when Antigravity hits credit limits, reviewing the filesystem, completing features, and documenting progress.

### The Handover Rule
Whenever a session switches between Antigravity and ChatGPT, the active agent **MUST** write a timestamped log to `messages/` (`YYYY-MM-DD_HH-MM-SS_<Agent>_to_<NextAgent>.md`). The receiving agent reads this file first to resume execution with zero context loss.

---

## 4. Current Milestone: Phase 1 MVP Scaffolding
- [x] Founding company repository and desktop hub created.
- [x] Open-source engine access and dependency manifest drafted.
- [x] 8 specialized AI employee roles defined and assigned.
- [x] Cross-agent communication protocol formalized in `messages/`.
- [ ] Tauri v2 native desktop application shell initialization.
- [ ] Headless Blender 5.2 IPC daemon and Godot/Jolt physics bridge.
