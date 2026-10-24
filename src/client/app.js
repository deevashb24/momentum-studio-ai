/**
 * MomentumStudio AI — 3D Client Workstation Runtime
 * Initializes Three.js WebGL viewport, Draco-compressed glTF loader,
 * interactive OrbitControls, spatial AST inspector, and "Cursor for 3D" agent loop.
 */

// Embedded desktop assets use a loopback API; browser mode stays same-origin.
const ENGINE_ORIGIN = location.protocol === "http:" || location.protocol === "https:" ? "" : "http://127.0.0.1:8018";
const engineUrl = path => `${ENGINE_ORIGIN}${path}`;
const apiFetch = (path, options) => fetch(engineUrl(path), options);
async function checkEngine() {
  let connected = false;
  try { connected = (await apiFetch("/api/v1/health", {signal: AbortSignal.timeout(2000)})).ok; } catch (_) {}
  document.getElementById("engineStatus").style.display = connected ? "none" : "block";
  document.getElementById("headerEngineStatus").textContent = connected ? "ENGINE CONNECTED" : "ENGINE OFFLINE";
}
checkEngine();
setInterval(checkEngine, 5000);

// DOM Elements
const canvas = document.getElementById("canvas3d");
const hudCompileTime = document.getElementById("hudCompileTime");
const hudMeshCount = document.getElementById("hudMeshCount");
const hudClearance = document.getElementById("hudClearance");
const hudGlbSize = document.getElementById("hudGlbSize");
const headerClearanceStatus = document.getElementById("headerClearanceStatus");
const chatStream = document.getElementById("chatStream");
const agentInput = document.getElementById("agentInput");
const btnSendPrompt = document.getElementById("btnSendPrompt");
const btnTriggerCompile = document.getElementById("btnTriggerCompile");
const btnToggleWireframe = document.getElementById("btnToggleWireframe");
const btnResetCamera = document.getElementById("btnResetCamera");
const sliderClearance = document.getElementById("sliderClearance");
const valClearanceRadius = document.getElementById("valClearanceRadius");
const astTextarea = document.getElementById("astTextarea");
const btnSaveAST = document.getElementById("btnSaveAST");

let currentSceneName = "sector_01_cerberus_corridor";
let wireframeMode = false;
let chaseCameraActive = false;
let showEnvelope = false;
let scene, camera, renderer, controls, loadedModel = null;
let corridorEnvelopeMesh = null;
let physicsGuide = null;
let trackCurve = null;
let vehicleGroup = null;
let vehicleProgress = 0.0;

// Initialize Three.js Viewport
function initThreeJS() {
  const container = canvas.parentElement;
  const width = container.clientWidth;
  const height = container.clientHeight;

  scene = new THREE.Scene();
  scene.background = new THREE.Color(0x0a0c12);
  scene.fog = new THREE.FogExp2(0x0a0c12, 0.0004);

  camera = new THREE.PerspectiveCamera(60, width / height, 0.1, 8000);
  camera.position.set(28, 16, -20);

  renderer = new THREE.WebGLRenderer({ canvas: canvas, antialias: true, alpha: false });
  renderer.setSize(width, height, false);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.outputEncoding = THREE.sRGBEncoding;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.35;

  // Controls
  if (typeof THREE.OrbitControls !== "undefined") {
    controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.target.set(0, 10, 60);
    controls.maxDistance = 2500;
  }

  // Enhanced Cyberpunk Lighting
  const ambientLight = new THREE.AmbientLight(0x1e293b, 1.4);
  scene.add(ambientLight);

  const hemiLight = new THREE.HemisphereLight(0x38bdf8, 0x0f172a, 1.6);
  scene.add(hemiLight);

  const dirLight1 = new THREE.DirectionalLight(0x06b6d4, 2.5);
  dirLight1.position.set(-100, 150, 100);
  scene.add(dirLight1);

  const dirLight2 = new THREE.DirectionalLight(0xf97316, 2.0);
  dirLight2.position.set(120, 120, 450);
  scene.add(dirLight2);

  const dirLight3 = new THREE.DirectionalLight(0xa855f7, 1.8);
  dirLight3.position.set(-80, 130, 800);
  scene.add(dirLight3);

  // Ground Grid
  const gridHelper = new THREE.GridHelper(1400, 70, 0x06b6d4, 0x141824);
  gridHelper.position.y = -0.2;
  scene.add(gridHelper);

  // Resize handler
  const viewportObserver = new ResizeObserver(() => {
    const w = container.clientWidth;
    const h = container.clientHeight;
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    renderer.setSize(w, h, false);
  });
  viewportObserver.observe(container);

  // Setup Vehicle
  initVehicle();

  // Render Loop
  let lastTime = performance.now();
  function animate() {
    requestAnimationFrame(animate);
    const now = performance.now();
    const delta = Math.min((now - lastTime) / 1000, 0.1);
    lastTime = now;

    // Animate Vehicle along track
    if (trackCurve && vehicleGroup) {
      const trackLen = trackCurve.getLength();
      const speed = 45.0; // ~160 km/h traversal
      if (trackLen > 0) {
        vehicleProgress = (vehicleProgress + (speed * delta) / trackLen) % 1.0;
        const pt = trackCurve.getPointAt(vehicleProgress);
        const tangent = trackCurve.getTangentAt(vehicleProgress).normalize();

        vehicleGroup.position.copy(pt);
        const lookTarget = pt.clone().add(tangent);
        vehicleGroup.lookAt(lookTarget);

        if (chaseCameraActive) {
          const camOffset = tangent.clone().multiplyScalar(-18).add(new THREE.Vector3(0, 6.5, 0));
          camera.position.copy(pt).add(camOffset);
          camera.lookAt(pt.clone().add(tangent.clone().multiplyScalar(25)));
          if (controls) controls.target.copy(pt.clone().add(tangent.clone().multiplyScalar(25)));
        }
      }
    }

    if (controls && !chaseCameraActive) {
      controls.update();
    }
    renderer.render(scene, camera);
  }
  animate();

  // Load Initial Model
  loadGlbModel(`/api/v1/build/${currentSceneName}.glb`);
}

// 3D Vehicle Initializer
function initVehicle() {
  if (vehicleGroup) scene.remove(vehicleGroup);
  vehicleGroup = new THREE.Group();

  const carLoader = new THREE.GLTFLoader();
  carLoader.load(
    engineUrl("/assets/kenney/car_kit/Models/GLB format/race-future.glb"),
    (gltf) => {
      const carMesh = gltf.scene;
      carMesh.scale.set(2.4, 2.4, 2.4);
      carMesh.rotation.y = Math.PI; // Face forward
      vehicleGroup.add(carMesh);
    },
    undefined,
    () => {
      // Fallback procedural futuristic speeder
      const bodyGeo = new THREE.BoxGeometry(2.4, 0.8, 4.5);
      const bodyMat = new THREE.MeshStandardMaterial({
        color: 0x06b6d4,
        metalness: 0.85,
        roughness: 0.15,
        emissive: 0x083344
      });
      const body = new THREE.Mesh(bodyGeo, bodyMat);
      body.position.y = 0.5;
      vehicleGroup.add(body);

      const cabinGeo = new THREE.BoxGeometry(1.6, 0.7, 2.0);
      const cabinMat = new THREE.MeshStandardMaterial({
        color: 0x0f172a,
        metalness: 0.9,
        roughness: 0.1
      });
      const cabin = new THREE.Mesh(cabinGeo, cabinMat);
      cabin.position.set(0, 1.1, -0.2);
      vehicleGroup.add(cabin);
    }
  );

  // Dynamic Headlight Spotlights
  const headLightL = new THREE.SpotLight(0x7dd3fc, 5.0, 90, Math.PI / 5, 0.4);
  headLightL.position.set(-0.8, 0.8, 2.2);
  const targetL = new THREE.Object3D();
  targetL.position.set(-0.8, 0.2, 30);
  vehicleGroup.add(targetL);
  headLightL.target = targetL;
  vehicleGroup.add(headLightL);

  const headLightR = new THREE.SpotLight(0x7dd3fc, 5.0, 90, Math.PI / 5, 0.4);
  headLightR.position.set(0.8, 0.8, 2.2);
  const targetR = new THREE.Object3D();
  targetR.position.set(0.8, 0.2, 30);
  vehicleGroup.add(targetR);
  headLightR.target = targetR;
  vehicleGroup.add(headLightR);

  // Taillight glow
  const tailGlow = new THREE.PointLight(0xf97316, 4.0, 18);
  tailGlow.position.set(0, 0.9, -2.2);
  vehicleGroup.add(tailGlow);

  // Cyan Neon Ground Underglow
  const underGlow = new THREE.PointLight(0x06b6d4, 5.0, 14);
  underGlow.position.set(0, 0.3, 0);
  vehicleGroup.add(underGlow);

  scene.add(vehicleGroup);
}

// Load Draco-compressed glTF Model
function frameModel() {
  if (!loadedModel || !controls) return;
  camera.position.set(28, 16, -20);
  controls.target.set(0, 10, 60);
  controls.update();
}

let cachedTrackTexture = null;
let cachedTowerTexture = null;

function getCyberHighwayTexture() {
  if (cachedTrackTexture) return cachedTrackTexture;
  const cvs = document.createElement("canvas");
  cvs.width = 1024;
  cvs.height = 1024;
  const ctx = cvs.getContext("2d");

  // Dark asphalt base
  ctx.fillStyle = "#111622";
  ctx.fillRect(0, 0, 1024, 1024);

  // Road surface noise
  for (let i = 0; i < 4000; i++) {
    const x = Math.random() * 1024;
    const y = Math.random() * 1024;
    const g = 20 + Math.random() * 25;
    ctx.fillStyle = `rgb(${g}, ${g+5}, ${g+15})`;
    ctx.fillRect(x, y, 2, 2);
  }

  // Neon Cyan Edge Strips
  ctx.fillStyle = "#06b6d4";
  ctx.shadowColor = "#06b6d4";
  ctx.shadowBlur = 15;
  ctx.fillRect(20, 0, 32, 1024);
  ctx.fillRect(1024 - 52, 0, 32, 1024);

  // Dashed Highway Centerline (Orange Neon)
  ctx.fillStyle = "#f97316";
  ctx.shadowColor = "#f97316";
  ctx.shadowBlur = 18;
  for (let y = 0; y < 1024; y += 64) {
    ctx.fillRect(504, y + 10, 16, 40);
  }

  cachedTrackTexture = new THREE.CanvasTexture(cvs);
  cachedTrackTexture.wrapS = THREE.RepeatWrapping;
  cachedTrackTexture.wrapT = THREE.RepeatWrapping;
  cachedTrackTexture.repeat.set(1, 40);
  return cachedTrackTexture;
}

function getCyberTowerTexture() {
  if (cachedTowerTexture) return cachedTowerTexture;
  const towerCvs = document.createElement("canvas");
  towerCvs.width = 512;
  towerCvs.height = 512;
  const tCtx = towerCvs.getContext("2d");
  tCtx.fillStyle = "#151926";
  tCtx.fillRect(0, 0, 512, 512);

  for (let y = 16; y < 512; y += 24) {
    for (let x = 16; x < 512; x += 20) {
      if (Math.random() > 0.45) {
        const isCyan = Math.random() > 0.3;
        tCtx.fillStyle = isCyan ? "#38bdf8" : "#fbbf24";
        tCtx.fillRect(x, y, 10, 12);
      }
    }
  }
  cachedTowerTexture = new THREE.CanvasTexture(towerCvs);
  cachedTowerTexture.wrapS = THREE.RepeatWrapping;
  cachedTowerTexture.wrapT = THREE.RepeatWrapping;
  cachedTowerTexture.repeat.set(2, 6);
  return cachedTowerTexture;
}

function enhanceCyberpunkMaterials(model) {
  if (!model) return;
  const trackTex = getCyberHighwayTexture();
  const towerTex = getCyberTowerTexture();

  model.traverse(c => {
    if (c.isMesh) {
      const name = c.name || "";
      if (name.includes("Track_Surface")) {
        c.material = new THREE.MeshStandardMaterial({
          map: trackTex,
          roughness: 0.15,
          metalness: 0.7,
        });
        c.material.needsUpdate = true;
      } else if (name.includes("Tower")) {
        c.material = new THREE.MeshStandardMaterial({
          map: towerTex,
          color: 0x94a3b8,
          roughness: 0.4,
          metalness: 0.6,
          emissive: 0x1e293b,
        });
        c.material.needsUpdate = true;
      } else if (name.includes("TransitTube")) {
        c.material = new THREE.MeshStandardMaterial({
          color: 0x06b6d4,
          emissive: 0x06b6d4,
          emissiveIntensity: 1.5,
          roughness: 0.2,
          metalness: 0.8
        });
      } else if (name.includes("light")) {
        c.material = new THREE.MeshStandardMaterial({
          color: 0x38bdf8,
          emissive: 0x38bdf8,
          emissiveIntensity: 2.0
        });
      } else if (name.includes("barrier")) {
        c.material = new THREE.MeshStandardMaterial({
          color: 0xf97316,
          roughness: 0.3
        });
      }
    }
  });
}

function loadGlbModel(glbUrl) {
  physicsGuide = null;
  trackCurve = null;
  apiFetch(glbUrl.split("?")[0].replace(/\.glb$/, ".physics.json")).then(res => res.ok ? res.json() : null).then(data => {
    physicsGuide = data?.tracks?.[0]?.points || null;
    if (physicsGuide && physicsGuide.length >= 2) {
      const vectors = physicsGuide.map(p => new THREE.Vector3(p[0], p[1] + 0.35, p[2]));
      trackCurve = new THREE.CatmullRomCurve3(vectors);
      trackCurve.curveType = "catmullrom";
      trackCurve.tension = 0.2;
    }
    renderCorridorEnvelope(parseFloat(sliderClearance.value) || 32.0);
  }).catch(() => {});

  if (typeof THREE.GLTFLoader === "undefined") {
    console.warn("GLTFLoader unavailable");
    renderFallbackScene();
    return;
  }

  const loader = new THREE.GLTFLoader();

  if (typeof THREE.DRACOLoader !== "undefined") {
    const dracoLoader = new THREE.DRACOLoader();
    dracoLoader.setDecoderPath(new URL("vendor/draco/", location.href).href);
    loader.setDRACOLoader(dracoLoader);
  }

  loader.load(
    engineUrl(glbUrl),
    (gltf) => {
      if (loadedModel) scene.remove(loadedModel);
      loadedModel = gltf.scene;

      // Apply initial wireframe state
      loadedModel.traverse((child) => {
        if (child.isMesh && child.material) {
          child.material.wireframe = wireframeMode;
          // Ensure materials respond to lighting
          if (child.material.roughness !== undefined && child.material.roughness === 0) {
            child.material.roughness = 0.3;
          }
        }
      });

      // Enhance materials with PBR reflectivity, textures, and glowing emission
      enhanceCyberpunkMaterials(loadedModel);

      scene.add(loadedModel);
      let meshCount = 0;
      loadedModel.traverse(child => { if (child.isMesh) meshCount++; });
      hudMeshCount.textContent = `${meshCount} Meshes`;
      frameModel();
      renderCorridorEnvelope(parseFloat(sliderClearance.value) || 32.0);
    },
    (xhr) => {
      if (xhr.total) hudGlbSize.textContent = `${(xhr.total / 1024).toFixed(1)} KB`;
    },
    (err) => {
      console.warn("Failed to load GLB:", err);
      renderFallbackScene();
    }
  );
}

// Visual 3D Corridor Clearance Envelope
function renderCorridorEnvelope(radius) {
  if (corridorEnvelopeMesh) scene.remove(corridorEnvelopeMesh);
  corridorEnvelopeMesh = null;

  if (!showEnvelope || !physicsGuide || physicsGuide.length < 2) return;
  const curve = new THREE.CurvePath();
  for (let i = 1; i < physicsGuide.length; i++) {
    curve.add(new THREE.LineCurve3(new THREE.Vector3(...physicsGuide[i-1]), new THREE.Vector3(...physicsGuide[i])));
  }
  const tubeGeo = new THREE.TubeGeometry(curve, 64, radius, 16, false);
  const tubeMat = new THREE.MeshBasicMaterial({
    color: 0x06b6d4,
    transparent: true,
    opacity: 0.12,
    wireframe: true,
  });

  corridorEnvelopeMesh = new THREE.Mesh(tubeGeo, tubeMat);
  scene.add(corridorEnvelopeMesh);
}

// Fallback Procedural Cyberpunk Scene if GLTFLoader is blocked
function renderFallbackScene() {
  if (loadedModel) scene.remove(loadedModel);
  const group = new THREE.Group();

  // Track
  const trackGeo = new THREE.BoxGeometry(14, 1, 800);
  const trackMat = new THREE.MeshStandardMaterial({ color: 0x111622, roughness: 0.2, metalness: 0.8 });
  const track = new THREE.Mesh(trackGeo, trackMat);
  track.position.set(0, 0, 400);
  group.add(track);

  // Megatowers
  for (let i = 0; i < 16; i++) {
    const side = i % 2 === 0 ? -1 : 1;
    const x = side * (38.5 + (i % 3) * 12);
    const z = Math.floor(i / 2) * 90;
    const height = 120 + (i % 4) * 30;

    const bGeo = new THREE.BoxGeometry(24, height, 32);
    const bMat = new THREE.MeshStandardMaterial({
      color: 0x151924,
      roughness: 0.5,
      metalness: 0.5,
    });
    const bMesh = new THREE.Mesh(bGeo, bMat);
    bMesh.position.set(x, height / 2, z);
    group.add(bMesh);
  }

  loadedModel = group;
  scene.add(loadedModel);
  renderCorridorEnvelope(parseFloat(sliderClearance.value) || 32.0);
}

// Fetch Active Scene AST
async function fetchSceneAST() {
  try {
    const res = await apiFetch(`/api/v1/scenes/${currentSceneName}`);
    if (res.ok) {
      const ast = await res.json();
      astTextarea.value = JSON.stringify(ast, null, 2);

      if (ast.splines && ast.splines[0]) {
        const radius = ast.splines[0].corridor_clearance_radius_m || 32.0;
        document.getElementById("astSplineCount").textContent = `${ast.splines[0].points.length} Anchors`;
        sliderClearance.value = radius;
        valClearanceRadius.textContent = `${radius}m`;
        headerClearanceStatus.textContent = `${radius}m envelope`;
      }
    }
  } catch (err) {
    console.error("Failed to fetch scene AST:", err);
  }
}

// Trigger Headless Blender Compilation
async function triggerCompilation(injectObstruction = false) {
  hudCompileTime.textContent = "Compiling...";
  hudCompileTime.style.color = "var(--accent-orange)";

  try {
    let rawAst = null;
    try {
      rawAst = JSON.parse(astTextarea.value);
    } catch (e) {}

    const res = await apiFetch("/api/v1/compile", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        scene_name: currentSceneName,
        inject_obstruction: injectObstruction,
        min_clearance_m: parseFloat(sliderClearance.value) || 32.0,
        raw_ast: rawAst,
      }),
    });

    if (!res.ok) {
      const err = await res.json();
      appendMessage("agent", `Compilation error: ${err.detail || "Failed to compile"}`);
      return;
    }

    const data = await res.json();
    hudCompileTime.textContent = `${data.compile_time_ms} ms`;
    hudCompileTime.style.color = "var(--accent-emerald)";
    hudMeshCount.textContent = `${data.objects_retained} Objects`;
    hudClearance.textContent = `${data.corridor_clearance_percent}% Pass`;
    hudGlbSize.textContent = `${(data.glb_bytes / 1024).toFixed(1)} KB`;

    headerClearanceStatus.textContent = `${data.min_clearance_m}m (${data.corridor_clearance_percent}% CLEAR)`;

    if (data.auto_pruned_count > 0) {
      appendMessage(
        "agent",
        `⚠️ <strong>Corridor Corridor Audit Triggered</strong>: Detected ${data.violations_detected} obstruction(s). Auto-pruned ${data.auto_pruned_count} collision objects outside safe envelope!`
      );
    } else {
      appendMessage(
        "agent",
        `⚡ <strong>Headless Blender 5.2.1 Compiled in ${data.compile_time_ms} ms</strong>: Draco glTF regenerated with ${data.objects_retained} objects and 100% clearance!`
      );
    }

    // Reload glTF
    loadGlbModel(`${data.glb_url}?t=${Date.now()}`);
  } catch (err) {
    console.error("Compile failed:", err);
    hudCompileTime.textContent = "Error";
    hudCompileTime.style.color = "var(--accent-rose)";
  }
}

// Send Agent Natural Language Prompt
async function sendAgentPrompt() {
  const prompt = agentInput.value.trim();
  if (!prompt) return;

  appendMessage("user", prompt);
  agentInput.value = "";
  agentInput.disabled = true;
  btnSendPrompt.disabled = true;

  try {
    const res = await apiFetch("/api/v1/agent/prompt", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        prompt: prompt,
        current_scene_name: currentSceneName,
      }),
    });

    if (!res.ok) {
      appendMessage("agent", "Error communicating with spatial reasoning agent.");
      return;
    }

    const data = await res.json();
    appendMessage(
      "agent",
      `<strong>${data.agent_thought}</strong><br>• Action: ${data.action_taken}<br>• Compiled in: ${data.compilation.compile_time_ms} ms`
    );

    // Update AST in editor and reload scene
    if (data.ast_snapshot) {
      astTextarea.value = JSON.stringify(data.ast_snapshot, null, 2);
    }

    hudCompileTime.textContent = `${data.compilation.compile_time_ms} ms`;
    hudMeshCount.textContent = `${data.compilation.objects_retained} Objects`;
    hudClearance.textContent = `${data.compilation.corridor_clearance_percent}% Pass`;
    hudGlbSize.textContent = `${(data.compilation.glb_bytes / 1024).toFixed(1)} KB`;

    loadGlbModel(`${data.compilation.glb_url}?t=${Date.now()}`);
  } catch (err) {
    console.error("Agent prompt error:", err);
    appendMessage("agent", "Failed to connect to agent backend.");
  } finally {
    agentInput.disabled = false;
    btnSendPrompt.disabled = false;
    agentInput.focus();
  }
}

// Append Chat Message
function appendMessage(sender, text) {
  const bubble = document.createElement("div");
  bubble.className = `message-bubble ${sender === "user" ? "msg-user" : "msg-agent"}`;

  if (sender === "agent") {
    const header = document.createElement("div");
    header.className = "msg-agent-header";
    header.textContent = `MomentumStudio Orchestrator · ${new Date().toLocaleTimeString()}`;
    bubble.appendChild(header);
  }
  const content = document.createElement("div");
  content.textContent = sender === "agent" ? text.replace(/<\/?strong>/g, "") : text;
  bubble.appendChild(content);

  chatStream.appendChild(bubble);
  chatStream.scrollTop = chatStream.scrollHeight;
}

// Event Listeners
btnTriggerCompile.addEventListener("click", () => triggerCompilation(false));

btnToggleWireframe.addEventListener("click", () => {
  wireframeMode = !wireframeMode;
  btnToggleWireframe.style.color = wireframeMode ? "var(--accent-orange)" : "var(--text-main)";
  if (loadedModel) {
    loadedModel.traverse((child) => {
      if (child.isMesh && child.material) {
        child.material.wireframe = wireframeMode;
      }
    });
  }
});

btnResetCamera.addEventListener("click", () => {
  chaseCameraActive = false;
  const btnChase = document.getElementById("btnChaseCamera");
  if (btnChase) {
    btnChase.innerHTML = "<span>🎥 Follow Car: OFF</span>";
    btnChase.style.borderColor = "var(--accent-orange)";
    btnChase.style.color = "var(--accent-orange)";
  }
  if (camera && controls) {
    frameModel();
  }
});

const btnChaseCamera = document.getElementById("btnChaseCamera");
if (btnChaseCamera) {
  btnChaseCamera.addEventListener("click", () => {
    chaseCameraActive = !chaseCameraActive;
    btnChaseCamera.innerHTML = chaseCameraActive ? "<span>🎥 Follow Car: ON</span>" : "<span>🎥 Follow Car: OFF</span>";
    btnChaseCamera.style.borderColor = chaseCameraActive ? "var(--accent-emerald)" : "var(--accent-orange)";
    btnChaseCamera.style.color = chaseCameraActive ? "var(--accent-emerald)" : "var(--accent-orange)";
  });
}

const btnToggleEnvelope = document.getElementById("btnToggleEnvelope");
if (btnToggleEnvelope) {
  btnToggleEnvelope.addEventListener("click", () => {
    showEnvelope = !showEnvelope;
    btnToggleEnvelope.innerHTML = showEnvelope ? "<span>🛡️ Envelope: ON</span>" : "<span>🛡️ Envelope: OFF</span>";
    btnToggleEnvelope.style.borderColor = showEnvelope ? "var(--accent-cyan)" : "var(--border-subtle)";
    btnToggleEnvelope.style.color = showEnvelope ? "var(--accent-cyan)" : "var(--text-muted)";
    renderCorridorEnvelope(parseFloat(sliderClearance.value) || 32.0);
  });
}

sliderClearance.addEventListener("input", (e) => {
  const val = e.target.value;
  valClearanceRadius.textContent = `${val}m`;
  renderCorridorEnvelope(parseFloat(val));
});

sliderClearance.addEventListener("change", () => {
  triggerCompilation(false);
});

btnSendPrompt.addEventListener("click", sendAgentPrompt);
agentInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") sendAgentPrompt();
});

document.querySelectorAll(".prompt-chip").forEach((chip) => {
  chip.addEventListener("click", () => {
    agentInput.value = chip.dataset.prompt;
    sendAgentPrompt();
  });
});

btnSaveAST.addEventListener("click", async () => {
  try {
    const parsed = JSON.parse(astTextarea.value);
    const res = await apiFetch("/api/v1/scenes", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        scene_name: currentSceneName,
        ast_data: parsed,
      }),
    });
    if (res.ok) {
      appendMessage("agent", "Spatial AST saved to disk. Recompiling...");
      triggerCompilation(false);
    }
  } catch (err) {
    appendMessage("agent", "Invalid JSON syntax in AST editor. Please fix formatting.");
  }
});

// Boot
window.addEventListener("DOMContentLoaded", () => {
  initThreeJS();
  fetchSceneAST();
});

// Procedural Shader Recipe Handler
async function applyShaderRecipe(recipeId, targetSlot = "track") {
  try {
    const res = await apiFetch("/api/v1/recipes/apply", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        scene_name: currentSceneName,
        recipe_id: recipeId,
        target_slot: targetSlot,
      }),
    });
    if (res.ok) {
      const data = await res.json();
      const label = document.getElementById("activeRecipeLabel");
      if (label) label.textContent = recipeId;
      appendMessage(
        "agent",
        `🎨 <strong>Procedural Shader Recipe Applied</strong>: Switched ${targetSlot} to <em>${recipeId}</em>. Headless Blender compiled in ${data.compilation.compile_time_ms} ms!`
      );
      loadGlbModel(`${data.compilation.glb_url}?t=${Date.now()}`);
      fetchSceneAST();
    }
  } catch (err) {
    console.error("Failed to apply recipe:", err);
  }
}

document.querySelectorAll(".btn-recipe").forEach((btn) => {
  btn.addEventListener("click", () => {
    const recipe = btn.dataset.recipe;
    applyShaderRecipe(recipe, recipe === "BrutalistConcrete" ? "towers" : "track");
  });
});

// Jolt Physics Audit Handler
const btnAuditPhysics = document.getElementById("btnAuditPhysics");
const hudPhysics = document.getElementById("hudPhysics");

async function triggerPhysicsAudit(distance) {
  const reqDist = distance || 900.0;
  if (hudPhysics) {
    hudPhysics.textContent = "Auditing...";
    hudPhysics.style.color = "var(--accent-orange)";
  }
  try {
    const res = await fetch("/api/v1/physics/audit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        scene_name: currentSceneName,
        distance_m: reqDist,
      }),
    });
    if (res.ok) {
      const data = await res.json();
      if (hudPhysics) {
        hudPhysics.textContent = data.distance_driven_m.toFixed(1) + "m (" + data.max_physics_tick_ms.toFixed(2) + "ms)";
        hudPhysics.style.color = data.status === "PASSED" ? "var(--accent-emerald)" : "var(--accent-rose)";
      }
      appendMessage(
        "agent",
        "🚗 <strong>Godot 4.7.1 Jolt Physics Audit</strong>: " + data.status + " — " + data.reason + ". Driven " + data.distance_driven_m.toFixed(1) + "m over " + data.collision_meshes + " meshes (Max tick: " + data.max_physics_tick_ms.toFixed(3) + "ms / 4.0ms budget)."
      );
    }
  } catch (err) {
    console.error("Physics audit error:", err);
    if (hudPhysics) {
      hudPhysics.textContent = "Audit Error";
      hudPhysics.style.color = "var(--accent-rose)";
    }
  }
}

if (btnAuditPhysics) {
  btnAuditPhysics.addEventListener("click", () => triggerPhysicsAudit(900.0));
}
