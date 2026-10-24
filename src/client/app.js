/**
 * MomentumStudio AI — 3D Client Workstation Runtime
 * Initializes Three.js WebGL viewport, Draco-compressed glTF loader,
 * interactive OrbitControls, spatial AST inspector, and "Cursor for 3D" agent loop.
 */

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
let scene, camera, renderer, controls, loadedModel = null;
let corridorEnvelopeMesh = null;

// Initialize Three.js Viewport
function initThreeJS() {
  const container = canvas.parentElement;
  const width = container.clientWidth;
  const height = container.clientHeight;

  scene = new THREE.Scene();
  scene.background = new THREE.Color(0x0d0f15);
  scene.fog = new THREE.FogExp2(0x0d0f15, 0.0015);

  camera = new THREE.PerspectiveCamera(60, width / height, 0.1, 5000);
  camera.position.set(0, 75, -120);

  renderer = new THREE.WebGLRenderer({ canvas: canvas, antialias: true });
  renderer.setSize(width, height);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.2;

  // Controls
  if (typeof THREE.OrbitControls !== "undefined") {
    controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.target.set(0, 30, 100);
    controls.maxDistance = 1500;
  }

  // Lighting
  const ambientLight = new THREE.AmbientLight(0x223344, 0.9);
  scene.add(ambientLight);

  const dirLight1 = new THREE.DirectionalLight(0x06b6d4, 1.8);
  dirLight1.position.set(-80, 120, -50);
  scene.add(dirLight1);

  const dirLight2 = new THREE.DirectionalLight(0xf97316, 1.4);
  dirLight2.position.set(80, 90, 150);
  scene.add(dirLight2);

  // Ground Grid
  const gridHelper = new THREE.GridHelper(1000, 50, 0x06b6d4, 0x1e2436);
  gridHelper.position.y = -0.1;
  scene.add(gridHelper);

  // Resize handler
  window.addEventListener("resize", () => {
    const w = container.clientWidth;
    const h = container.clientHeight;
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    renderer.setSize(w, h);
  });

  // Render Loop
  function animate() {
    requestAnimationFrame(animate);
    if (controls) controls.update();
    renderer.render(scene, camera);
  }
  animate();

  // Load Initial Model
  loadGlbModel(`/api/v1/build/sector_01.glb`);
}

// Load Draco-compressed glTF Model
function loadGlbModel(glbUrl) {
  if (typeof THREE.GLTFLoader === "undefined") {
    console.warn("GLTFLoader not loaded from CDN, using fallback geometry");
    renderFallbackScene();
    return;
  }

  const loader = new THREE.GLTFLoader();

  if (typeof THREE.DRACOLoader !== "undefined") {
    const dracoLoader = new THREE.DRACOLoader();
    dracoLoader.setDecoderPath("https://www.gstatic.com/draco/versioned/decoders/1.5.6/");
    loader.setDRACOLoader(dracoLoader);
  }

  loader.load(
    glbUrl,
    (gltf) => {
      if (loadedModel) scene.remove(loadedModel);
      loadedModel = gltf.scene;

      // Apply initial wireframe state
      loadedModel.traverse((child) => {
        if (child.isMesh && child.material) {
          child.material.wireframe = wireframeMode;
        }
      });

      scene.add(loadedModel);
      renderCorridorEnvelope(parseFloat(sliderClearance.value) || 32.0);
    },
    (xhr) => {
      // Progress
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

  const points = [
    new THREE.Vector3(0, 0, 0),
    new THREE.Vector3(0, 8, 150),
    new THREE.Vector3(-18, 14, 300),
    new THREE.Vector3(22, 10, 480),
    new THREE.Vector3(0, 18, 650),
    new THREE.Vector3(0, 24, 850),
  ];

  const curve = new THREE.CatmullRomCurve3(points);
  const tubeGeo = new THREE.TubeGeometry(curve, 64, radius, 16, false);
  const tubeMat = new THREE.MeshBasicMaterial({
    color: 0x06b6d4,
    transparent: true,
    opacity: 0.08,
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
    const res = await fetch(`/api/v1/scenes/${currentSceneName}`);
    if (res.ok) {
      const ast = await res.json();
      astTextarea.value = JSON.stringify(ast, null, 2);

      if (ast.splines && ast.splines[0]) {
        const radius = ast.splines[0].corridor_clearance_radius_m || 32.0;
        sliderClearance.value = radius;
        valClearanceRadius.textContent = `${radius}m`;
        headerClearanceStatus.textContent = `${radius}m (100% CLEAR)`;
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

    const res = await fetch("/api/v1/compile", {
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
        `⚠️ <strong>KDTree Corridor Audit Triggered</strong>: Detected ${data.violations_detected} obstruction(s). Auto-pruned ${data.auto_pruned_count} collision objects outside safe envelope!`
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
    const res = await fetch("/api/v1/agent/prompt", {
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
    bubble.innerHTML = `
      <div class="msg-agent-header">
        <span>MomentumStudio Orchestrator</span>
        <span>${new Date().toLocaleTimeString()}</span>
      </div>
      <div>${text}</div>
    `;
  } else {
    bubble.innerHTML = `<div>${text}</div>`;
  }

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
  if (camera && controls) {
    camera.position.set(0, 75, -120);
    controls.target.set(0, 30, 100);
    controls.update();
  }
});

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
    const res = await fetch("/api/v1/scenes", {
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
    const res = await fetch("/api/v1/recipes/apply", {
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
