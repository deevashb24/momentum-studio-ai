# MomentumStudio AI — Phase 2 handoff

Recorded 2026-10-24 18:22:23 IST by Codex.

Implemented all three requested code tracks:

- Catalog-backed modular instancing: GLB preference, cached templates, spline-aligned streetlights/barriers/access apron and rooftop industrial tanks. Production export has 96 objects including 71 modular placements across 4 imported asset types.
- Tauri v2 native macOS ARM64 app: built and opened successfully, about 10.78 MiB. Frontend libraries and decoder are bundled locally; native menus and backend connection were verified. The ZIP contains the developer app, not Python/Blender/Godot/assets.
- Headless Jolt auditor: runtime GLB import, real triangle collision, gravity-driven kinematic body, four suspension probes, blockage detection, physical distance, route progress and measured tick budget.

Validation:

- 33 tests pass: 29 Python/unit/API tests (API subprocess boundary stubbed) plus 4 native Godot/Jolt regression cases (valid kilometre, gap, wall and short route).
- Actual production scene: 900m physical traversal passed; observed max tick 0.564ms against 4ms budget. Its tessellated route is 917.785m; a 1,000m request correctly fails as too short.
- Separate 1,100m compiled validation scene: 1,000m traversal passed, 1,000.516m driven, 0.632ms max observed tick.
- Deliberately removed road section: failure at about 399m with lost suspension support.
- Live Blender compilation: 359.75ms total for 96 objects; compressed GLB 72,104 bytes. Export alone took about 39ms. The previous briefing's 39ms is not an end-to-end compile benchmark.
- Injected tower obstruction: one tower pruned, and its rooftop tank was not instantiated; 94 objects retained.
- JavaScript syntax, Rust formatting and git whitespace checks passed.

Remaining blockers and scope limits:

1. Headless Blender 5.2.1 exits 139 during Metal initialization before executing Python. The open Blender bridge works, but the API's separate process still fails. Opt-in native Blender/API checks: 5 failures, 24 passes before adding the four new Godot tests. Do not call the Compile button end-to-end verified.
2. DMG creation fails with `hdiutil: create failed - Device not configured`. The native .app is packaged as ZIP instead. No Apple Developer ID signing/notarization was attempted.
3. This is a developer desktop wrapper. Run `./scripts/run_desktop.sh --app` from the repository to launch the local backend and built app. The standalone .app expects the API at 127.0.0.1:8018.
4. Godot's sandbox app-data-directory warning is nonfatal to these runs; reports and exit codes were verified. Timing results are observed measurements, not universal frame-time guarantees.
5. The compiler supports POLY/BEZIER tracks and megatower zones; NURBS is explicitly rejected, other zone generators remain unimplemented. The physics runner audits the first track. Procedural Blender shaders are not preserved as arbitrary node graphs in glTF.

Other fixes: consistent Y-up AST/glTF and Z-up Blender coordinates; full mesh-bounds clearance against route segments; recipe-slot bindings; correct asset-catalog path; timeout/error handling; preserved agent clearance edits; invalid scene-name/AST rejection; temporary test scene isolation; safe text rendering; UI startup telemetry no longer fabricates a successful audit or compile time.

Source and reproducible commands: `resources/phase2_development.md` in the repository. Continue with the headless Blender startup issue, then rerun `PYTHONPATH=src python3 -m pytest src/tests --run-blender -q` and the full native Compile flow.
