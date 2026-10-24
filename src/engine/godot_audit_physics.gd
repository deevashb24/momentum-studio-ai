extends SceneTree
## Headless physical traversal of the compiler's uncompressed GLB.
## Usage: godot --headless --path src/engine/physics --script ../godot_audit_physics.gd -- GLB MANIFEST [DISTANCE] [REPORT]

var vehicle: CharacterBody3D
var world: Node3D
var points: Array[Vector3] = []
var cumulative: Array[float] = [0.0]
var distance_required := 1000.0
var distance_driven := 0.0
var elapsed := 0.0
var max_tick_ms := 0.0
var max_budget_ms := 4.0
var ticks := 0
var ready_ticks := 0
var done := false
var report_path := ""
var previous_position := Vector3.ZERO
var max_progress := 0.0
var stalled_time := 0.0
var collider_count := 0
var engine_name := ""

func _initialize() -> void:
    call_deferred("setup")

func finish(passed: bool, reason: String) -> void:
    if done:
        return
    done = true
    var report := {"status": "PASSED" if passed else "FAILED", "reason": reason,
        "requested_distance_m": distance_required, "distance_driven_m": distance_driven,
        "route_progress_m": max_progress, "physics_ticks": ticks,
        "max_physics_tick_ms": max_tick_ms, "physics_budget_ms": max_budget_ms,
        "collision_meshes": collider_count, "physics_engine": engine_name,
        "godot_version": Engine.get_version_info().string}
    var serialized := JSON.stringify(report)
    print("__MOMENTUM_PHYSICS_RESULT__" + serialized)
    if not report_path.is_empty():
        var file := FileAccess.open(report_path, FileAccess.WRITE)
        if file == null:
            push_error("Cannot write audit report: " + report_path)
            quit(2)
            return
        file.store_string(serialized + "\n")
    quit(0 if passed else 1)

func setup() -> void:
    var args := OS.get_cmdline_user_args()
    if args.size() < 2:
        finish(false, "Expected GLB and physics manifest paths")
        return
    if args.size() >= 3:
        distance_required = args[2].to_float()
    if args.size() >= 4:
        report_path = args[3]
    if distance_required <= 0.0 or not is_finite(distance_required):
        finish(false, "Distance must be finite and positive")
        return
    engine_name = str(ProjectSettings.get_setting("physics/3d/physics_engine"))
    if engine_name != "Jolt Physics":
        finish(false, "Jolt Physics must be selected by the audit project")
        return
    var manifest = JSON.parse_string(FileAccess.get_file_as_string(args[1]))
    if not manifest is Dictionary or manifest.get("coordinate_system") != "Y_UP_METERS":
        finish(false, "Invalid physics manifest")
        return
    var tracks = manifest.get("tracks", [])
    if tracks.is_empty():
        finish(false, "No track in physics manifest")
        return
    if manifest.get("physics_contracts", {}).get("engine", "JOLT_3D") != "JOLT_3D":
        finish(false, "This runner audits JOLT_3D contracts only")
        return
    max_budget_ms = float(manifest.get("physics_contracts", {}).get("max_physics_tick_ms", 4.0))
    for p in tracks[0].get("points", []):
        points.append(Vector3(p[0], p[1], p[2]))
        if points.size() > 1:
            cumulative.append(cumulative[-1] + points[-1].distance_to(points[-2]))
    if points.size() < 2 or cumulative[-1] < distance_required + 2.0:
        finish(false, "Track is too short for requested traversal plus 2m stopping margin")
        return
    var document := GLTFDocument.new()
    var state := GLTFState.new()
    var error := document.append_from_file(args[0], state)
    if error != OK:
        finish(false, "GLB import failed; use the compiler's .physics.glb (uncompressed)")
        return
    world = document.generate_scene(state)
    if world == null:
        finish(false, "GLB generated no scene")
        return
    root.add_child(world)
    add_collisions(world)
    if collider_count == 0:
        finish(false, "GLB contains no collision meshes")
        return
    vehicle = CharacterBody3D.new()
    vehicle.name = "AuditVehicle"
    vehicle.collision_layer = 4
    vehicle.collision_mask = 3
    vehicle.floor_snap_length = 1.0
    vehicle.floor_max_angle = deg_to_rad(45)
    var collision := CollisionShape3D.new()
    var shape := BoxShape3D.new()
    shape.size = Vector3(1.4, 1.0, 2.4)
    collision.shape = shape
    vehicle.add_child(collision)
    root.add_child(vehicle)
    vehicle.position = points[0] + Vector3(0, 0.55, 0)
    previous_position = vehicle.position

func add_collisions(node: Node) -> void:
    if node is MeshInstance3D and node.mesh != null:
        var body := StaticBody3D.new()
        body.collision_layer = 2 if str(node.name).begins_with("Track_Surface") else 1
        body.collision_mask = 4
        var shape := CollisionShape3D.new()
        shape.shape = node.mesh.create_trimesh_shape()
        body.add_child(shape)
        node.add_child(body)
        collider_count += 1
    for child in node.get_children():
        if not child is StaticBody3D:
            add_collisions(child)

func path_at(distance: float) -> Vector3:
    for i in range(1, cumulative.size()):
        if cumulative[i] >= distance:
            return points[i-1].lerp(points[i], (distance-cumulative[i-1])/maxf(0.00001, cumulative[i]-cumulative[i-1]))
    return points[-1]

func progress(position: Vector3) -> float:
    var closest := INF
    var result := 0.0
    for i in range(points.size()-1):
        var segment := points[i+1]-points[i]
        var t := clampf((position-points[i]).dot(segment)/maxf(segment.length_squared(), 0.00001), 0.0, 1.0)
        var distance := position.distance_squared_to(points[i]+t*segment)
        if distance < closest:
            closest = distance
            result = cumulative[i]+t*segment.length()
    return result

func _physics_process(delta: float) -> bool:
    if vehicle == null or done:
        return false
    ready_ticks += 1
    if ready_ticks < 5:
        return false
    ticks += 1
    elapsed += delta
    var started := Time.get_ticks_usec()
    var route_position := progress(vehicle.position)
    var target := path_at(minf(route_position+4.0, cumulative[-1]))
    var direction := target-vehicle.position
    direction.y = 0.0
    direction = direction.normalized()
    vehicle.velocity.x = direction.x*30.0
    vehicle.velocity.z = direction.z*30.0
    vehicle.velocity.y -= 20.0*delta
    vehicle.move_and_slide()
    for index in range(vehicle.get_slide_collision_count()):
        if absf(vehicle.get_slide_collision(index).get_normal().y) < 0.5:
            finish(false, "Vehicle blocked by collision geometry")
            return false
    distance_driven += vehicle.position.distance_to(previous_position)
    previous_position = vehicle.position
    if route_position > max_progress + 0.01:
        max_progress = route_position
        stalled_time = 0.0
    else:
        stalled_time += delta
    # Four suspension probes use real imported road triangles, excluding vehicle.
    for x in [-0.5, 0.5]:
        for z in [-0.8, 0.8]:
            var origin := vehicle.position + Vector3(x, 0.2, z)
            var query := PhysicsRayQueryParameters3D.create(origin, origin-Vector3(0, 2.0, 0), 2)
            var hit := vehicle.get_world_3d().direct_space_state.intersect_ray(query)
            # The rear probes can be beyond the beginning during initial rollout.
            if hit.is_empty() and max_progress > 2.0:
                finish(false, "Suspension probe lost road support")
                return false
    var tick_ms := maxf(float(Time.get_ticks_usec()-started)/1000.0, Performance.get_monitor(Performance.TIME_PHYSICS_PROCESS)*1000.0)
    max_tick_ms = maxf(max_tick_ms, tick_ms)
    if tick_ms > max_budget_ms:
        finish(false, "Physics tick exceeded contract budget")
    elif vehicle.position.y < path_at(route_position).y-1.0:
        finish(false, "Vehicle fell below road")
    elif stalled_time > 2.0 or elapsed > distance_required/10.0+10.0:
        finish(false, "Vehicle blocked or traversal timed out")
    elif max_progress >= distance_required and distance_driven >= distance_required:
        finish(true, "Requested physical traversal completed with road support")
    return false
