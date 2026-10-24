# Phase 2 development and validation

The compiler now instantiates Kenney streetlights, construction barriers, driveway
aprons and industrial rooftop tanks. Catalog lookup prefers GLB over duplicate
FBX/OBJ variants; the catalog's 666 entries are file variants, not 666 unique models.
The catalog contains tanks rather than a named air-conditioning asset.

## Coordinate and clearance contract

World AST, glTF and Godot use metres, Y up and +Z forward. Blender receives
`(x, -z, y)`. POLY and cubic BEZIER tracks are tessellated consistently for road
geometry, placements and the exported physics manifest. NURBS is explicitly
unsupported. Tower zones now respect their anchor spline and material binding;
unsupported zone generators are not silently rendered as more towers.

Roadside modules sit outside the requested clearance envelope. Mesh bounds are
checked against every segment of the compiled route using a conservative expanded
AABB intersection test. This can reject extra objects near corners, but fixes the
old center-only, sparse-anchor test. Road surface triangles are deliberately exempt
from obstacle clearance. This is clearance for the compiled tessellation, not a
proof for an infinitely precise curve or arbitrary simulation dynamics.

Each imported module is baked to a bottom-centered mesh template once per compile,
then instances share mesh data. Scaling is uniform; generated towers remain
procedural geometry. The compiled scene is isolated from the user's existing scene
when used in a live Blender session. Shader graphs remain Blender-specific: glTF
exports supported material properties, not arbitrary Noise/Voronoi node programs.

## Native macOS workstation

Install Python requirements with `python3 -m pip install -r requirements.txt` in a
project environment. Keep the existing asset library in `assets/`.

```bash
./scripts/run_desktop.sh          # launches local backend and cargo tauri dev
cargo tauri build --bundles app  # build the macOS app
./scripts/run_desktop.sh --app   # backend + built native app
cargo tauri build --bundles dmg  # needs a working macOS disk-image service
```

The app embeds `src/client` and vendored Three.js/Draco with their license files.
It is a developer workstation wrapper: Python, the backend source, asset library,
Blender and Godot are external dependencies, not bundled standalone runtimes.
Launching the `.app` directly requires the backend on `127.0.0.1:8018`; a visible
message explains when it is unavailable. The launcher only stops a backend it
started itself. No Apple Developer ID signing/notarization was attempted.

macOS configuration follows the [Tauri v2 configuration reference](https://v2.tauri.app/reference/config/).
The app uses native menus, local assets, a restrictive content policy and explicitly
allowed desktop origins for the HTTP API. The API should remain loopback-only.

## Compile and audit

```bash
/Applications/Blender.app/Contents/MacOS/Blender -b --python-exit-code 1 \
  --python src/engine/blender_compile_chunk.py -- \
  src/scenes/sector_01_cerberus_corridor.world.json \
  src/build/sector_01_cerberus_corridor.glb

./scripts/audit_physics.sh "$PWD/src/build/sector_01_cerberus_corridor" 900
```

Compilation creates the compressed viewport `.glb`, an uncompressed `.physics.glb`
and a `.physics.json` manifest. The uncompressed artifact is required by this
Godot import workflow. The physics runner uses
[GLTFDocument](https://docs.godotengine.org/en/stable/classes/class_gltfdocument.html),
creates static triangle collision shapes from the imported meshes, and moves a
CharacterBody3D with gravity and four suspension ray probes. It checks support,
blocking collisions, progress, elapsed simulation time and the physics tick budget.
It audits the first track in the manifest. Timing is an observed maximum in this
headless run, not a guarantee of frame rate on every user's machine.

The production route is about 918m, so a requested 1,000m audit fails explicitly.
For a 1,000m traversal, compile `src/scenes/physics_1000m_validation.world.json`
(1,100m road including stopping margin), then run:

```bash
./scripts/audit_physics.sh "$PWD/src/build/physics_1000m_validation" 1000
```

## Tests and known environment blockers

```bash
PYTHONPATH=src python3 -m pytest src/tests -q
PYTHONPATH=src python3 -m pytest src/tests --run-blender -q
```

The default API tests use a subprocess stub and temporary copies of scenes, so
tests never mutate the production scene. Four Godot tests run actual native Jolt
physics against generated GLB fixtures: a valid kilometre, a gap, a blocking wall
and a too-short route. They skip if Godot is absent. `--run-blender` replaces the
API subprocess stub with native headless Blender.

On this Codex execution host, headless Blender 5.2.1 crashes with exit 139 in Metal
initialization before Python starts. Live Blender bridge compilation succeeded.
The native Blender/API integration tests therefore remain failing; opening Blender
does not repair the separate subprocess startup. The API reports errors instead
of inventing a successful result. Resolve this host/Blender startup issue before
considering the app's Compile button verified end to end.

The `.app` build and launch succeeded. DMG creation failed in `hdiutil` with
`Device not configured`; an app ZIP is provided for this development handoff.
Godot emitted an application-data-directory permission warning in this sandbox;
the audit reports and exit codes were still produced successfully.
