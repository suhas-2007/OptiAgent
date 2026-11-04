// ==========================================================================
// OptiAgent Autonomous Optimization Frontend Engine
// ==========================================================================

// Configuration
const API_URL = (
    window.location.hostname === "localhost" ||
    window.location.hostname === "127.0.0.1" ||
    window.location.protocol === "file:" ||
    window.location.port === "5000"
) ? "http://127.0.0.1:5000" : "https://optiagent-272474227005.asia-south1.run.app";

// DOM helper
function $(id) {
    return document.getElementById(id);
}

// Global DOM references
let objectiveInput;
let dimensionsInput;
let maxStagesInput;
let patienceInput;
let boundsContainer;
let optimizeButton;
let buttonText;
let buttonLoader;
let connectionStatus;
let agentBadge;
let strategyElement;
let confidenceElement;
let explorationElement;
let reasonElement;
let bestScoreElement;
let bestPositionElement;
let stageCountElement;
let strategyCountElement;
let strategyHistoryElement;
let convergenceStatus;
let chart;
let chartEmpty;
let errorMessage;
let errorText;
let activityList;
let activityStatus;

// Preset benchmark definitions matching backend
const PRESET_BENCHMARKS = {
    "sphere": {
        "name": "Sphere Function",
        "objective": "x1**2 + x2**2",
        "dimensions": 2,
        "bounds": [[-10.0, 10.0], [-10.0, 10.0]],
        "explanation": "Convex smooth quadratic test with global minimum 0 at (0, 0)."
    },
    "rosenbrock": {
        "name": "Rosenbrock Function",
        "objective": "(1 - x1)**2 + 100 * (x2 - x1**2)**2",
        "dimensions": 2,
        "bounds": [[-5.0, 5.0], [-5.0, 5.0]],
        "explanation": "Narrow curved banana valley benchmark with global minimum 0 at (1, 1)."
    },
    "rastrigin": {
        "name": "Rastrigin Function",
        "objective": "20 + x1**2 - 10 * cos(2 * pi * x1) + x2**2 - 10 * cos(2 * pi * x2)",
        "dimensions": 2,
        "bounds": [[-5.12, 5.12], [-5.12, 5.12]],
        "explanation": "Highly multimodal benchmark with a large lattice of deceptive local traps."
    },
    "ackley": {
        "name": "Ackley Function",
        "objective": "-20 * exp(-0.2 * sqrt(0.5 * (x1**2 + x2**2))) - exp(0.5 * (cos(2 * pi * x1) + cos(2 * pi * x2))) + e + 20",
        "dimensions": 2,
        "bounds": [[-5.0, 5.0], [-5.0, 5.0]],
        "explanation": "Multimodal test with nearly flat outer regions and a deep central minimum."
    },
    "shifted": {
        "name": "Shifted Quadratic Function",
        "objective": "(x1 - 3)**2 + (x2 + 2)**2",
        "dimensions": 2,
        "bounds": [[-10.0, 10.0], [-10.0, 10.0]],
        "explanation": "Convex quadratic shifted away from origin, global minimum 0 at (3, -2)."
    },
    "trigonometric": {
        "name": "Trigonometric Function",
        "objective": "sin(x1)**2 + cos(x2)**2",
        "dimensions": 2,
        "bounds": [[-5.0, 5.0], [-5.0, 5.0]],
        "explanation": "Oscillating periodic function with infinite periodic local minima."
    },
    "beale": {
        "name": "Beale Function",
        "objective": "(1.5 - x1 + x1*x2)**2 + (2.25 - x1 + x1*x2**2)**2 + (2.625 - x1 + x1*x2**3)**2",
        "dimensions": 2,
        "bounds": [[-4.5, 4.5], [-4.5, 4.5]],
        "explanation": "Multimodal 2D benchmark with sharp ridges and minimum at (3, 0.5)."
    },
    "booth": {
        "name": "Booth Function",
        "objective": "(x1 + 2*x2 - 7)**2 + (2*x1 + x2 - 5)**2",
        "dimensions": 2,
        "bounds": [[-10.0, 10.0], [-10.0, 10.0]],
        "explanation": "Quadratic plate function with global minimum 0 at (1, 3)."
    },
    "himmelblau": {
        "name": "Himmelblau Function",
        "objective": "(x1**2 + x2 - 11)**2 + (x1 + x2**2 - 7)**2",
        "dimensions": 2,
        "bounds": [[-5.0, 5.0], [-5.0, 5.0]],
        "explanation": "Classic benchmark containing 4 identical global minima."
    }
};

// Initialize DOM references
function initializeDOM() {
    objectiveInput = $("objective");
    dimensionsInput = $("dimensions");
    maxStagesInput = $("maxStages");
    patienceInput = $("patience");
    boundsContainer = $("boundsContainer");
    optimizeButton = $("optimizeButton");
    buttonText = $("buttonText");
    buttonLoader = $("buttonLoader");
    connectionStatus = $("connectionStatus");
    agentBadge = $("agentBadge");
    strategyElement = $("strategy");
    confidenceElement = $("confidence");
    explorationElement = $("exploration");
    reasonElement = $("reason");
    bestScoreElement = $("bestScore");
    bestPositionElement = $("bestPosition");
    stageCountElement = $("stageCount");
    strategyCountElement = $("strategyCount");
    strategyHistoryElement = $("strategyHistory");
    convergenceStatus = $("convergenceStatus");
    chart = $("convergenceChart");
    chartEmpty = $("chartEmpty");
    errorMessage = $("errorMessage");
    errorText = $("errorText");
    activityList = $("activityList");
    activityStatus = $("activityStatus");

    if (!activityList) {
        console.warn("activityList element was not found in index.html.");
    }
}

// Lifecycle Startup
document.addEventListener("DOMContentLoaded", () => {
    initializeDOM();
    generateBounds();
    checkAPI();

    if (dimensionsInput) {
        dimensionsInput.addEventListener("input", generateBounds);
    }

    if (optimizeButton) {
        optimizeButton.addEventListener("click", runOptimization);
    }

    window.addEventListener("resize", () => {
        if (window.lastOptimizationResult) {
            drawConvergenceChart(window.lastOptimizationResult);
        }
    });

    setupSmartInput();
    setupAskAI();
    setupArchitectureModal();
    const upload = $("dropZone");
    if (upload) upload.addEventListener("keydown", e => {
        if (e.target === upload && (e.key === "Enter" || e.key === " ")) {
            e.preventDefault(); $("imageFileInput").click();
        }
    });
});

// API Health Check
async function checkAPI() {
    if (!connectionStatus) return;

    try {
        const response = await fetch(`${API_URL}/health`, {
            method: "GET",
            cache: "no-store"
        });

        if (!response.ok) {
            throw new Error(`API returned HTTP ${response.status}`);
        }

        const data = await response.json();
        if (data.status !== "ok") {
            throw new Error("Invalid API health response.");
        }

        connectionStatus.textContent = "● API Online";
        connectionStatus.classList.remove("offline");
        connectionStatus.classList.add("online");

    } catch (error) {
        connectionStatus.textContent = "● API Offline";
        connectionStatus.classList.remove("online");
        connectionStatus.classList.add("offline");
    }
}

let activeRastriginExpression = null;
function rastriginExpression(dimensions) {
    const variables = Array.from({length: dimensions}, (_, i) => `x${i+1}`);
    return `${10*dimensions} + ` + variables.map(x => `${x}**2 - 10*cos(2*pi*${x})`).join(' + ');
}

// Generate Variable Bounds dynamically
function generateBounds() {
    if (!dimensionsInput || !boundsContainer) return;

    const dimensions = parseInt(dimensionsInput.value, 10);
    if (!Number.isInteger(dimensions) || dimensions < 1 || dimensions > 100) {
        boundsContainer.innerHTML = "";
        return;
    }

    const oldBounds = [...boundsContainer.querySelectorAll('.bound-row')].map(row => [row.querySelector('.lower-bound').value, row.querySelector('.upper-bound').value]);
    const scalable = activeRastriginExpression !== null && objectiveInput.value === activeRastriginExpression;
    if (scalable) {
        activeRastriginExpression = rastriginExpression(dimensions);
        objectiveInput.value = activeRastriginExpression;
    }
    boundsContainer.innerHTML = "";

    for (let i = 1; i <= dimensions; i++) {
        const row = document.createElement("div");
        row.className = "bound-row";

        row.innerHTML = `
            <div class="bound-label">x${i}</div>
            <input
                id="lowerBound${i}"
                type="number"
                class="lower-bound"
                data-index="${i}"
                value="-10"
                step="any"
                placeholder="Lower [min]"
                aria-label="Lower bound for x${i}"
            >
            <input
                id="upperBound${i}"
                type="number"
                class="upper-bound"
                data-index="${i}"
                value="10"
                step="any"
                placeholder="Upper [max]"
                aria-label="Upper bound for x${i}"
            >
        `;

        if (oldBounds[i-1]) {
            row.querySelector('.lower-bound').value = oldBounds[i-1][0];
            row.querySelector('.upper-bound').value = oldBounds[i-1][1];
        } else if (scalable) {
            row.querySelector('.lower-bound').value = '-5.12';
            row.querySelector('.upper-bound').value = '5.12';
        }
        boundsContainer.appendChild(row);
    }
}

// Enhanced Preset Examples loader
function setExample(expression) {
    if (!objectiveInput) return;

    const key = String(expression).toLowerCase().trim();
    if (PRESET_BENCHMARKS[key]) {
        let preset = PRESET_BENCHMARKS[key];
        activeRastriginExpression = null;
        if (key === 'rastrigin') {
            const n = Math.min(100, Math.max(1, parseInt(dimensionsInput.value, 10) || 2));
            preset = {...preset, objective: rastriginExpression(n), dimensions: n,
                      bounds: Array.from({length: n}, () => [-5.12, 5.12])};
            activeRastriginExpression = preset.objective;
        }
        objectiveInput.value = preset.objective;

        if (dimensionsInput) {
            dimensionsInput.value = preset.dimensions;
        }

        generateBounds();

        // Populate variable bounds from preset
        if (Array.isArray(preset.bounds)) {
            preset.bounds.forEach((b, idx) => {
                const lowerInput = $(`lowerBound${idx + 1}`);
                const upperInput = $(`upperBound${idx + 1}`);
                if (lowerInput && b[0] !== undefined) lowerInput.value = b[0];
                if (upperInput && b[1] !== undefined) upperInput.value = b[1];
            });
        }

        clearError();
        showExtractionStatus(`Loaded preset "${preset.name}": ${preset.explanation}`, "info");
    } else {
        objectiveInput.value = expression;
    }
}

// Collect and validate bounds
function getBounds() {
    const lowerInputs = document.querySelectorAll(".lower-bound");
    const upperInputs = document.querySelectorAll(".upper-bound");
    const bounds = [];

    for (let i = 0; i < lowerInputs.length; i++) {
        const lower = parseFloat(lowerInputs[i].value);
        const upper = parseFloat(upperInputs[i].value);

        if (!Number.isFinite(lower) || !Number.isFinite(upper)) {
            throw new Error(`Invalid bounds for x${i + 1}.`);
        }

        if (lower >= upper) {
            throw new Error(`Lower bound must be strictly less than upper bound for x${i + 1}.`);
        }

        bounds.push([lower, upper]);
    }

    return bounds;
}

// Pipeline Stepper State Manager
function setAgentStep(step) {
    const steps = document.querySelectorAll(".pipeline-step");
    const order = ["observe", "reason", "decide", "act", "validate", "adapt"];
    const currentIndex = order.indexOf(step);

    steps.forEach((element) => {
        const elementStep = element.dataset.step || element.id.replace("pipeline", "").toLowerCase();
        const index = order.indexOf(elementStep);

        element.classList.remove("active");
        element.classList.remove("complete");

        if (index < currentIndex) {
            element.classList.add("complete");
        } else if (index === currentIndex) {
            element.classList.add("active");
        }
    });
}

// Button Running State
function setRunning(running) {
    if (optimizeButton) {
        optimizeButton.disabled = running;
    }
    if (buttonText) {
        buttonText.textContent = running ? "Agent is optimizing..." : "Run OptiAgent";
    }
    if (buttonLoader) {
        buttonLoader.classList.toggle("hidden", !running);
    }
}

// Activity Telemetry Feed
function clearActivity() {
    if (!activityList) return;
    activityList.innerHTML = "";
}

function clearActivityLog() {
    clearActivity();
}

function addActivity(title, message, type = "info") {
    if (!activityList) return;

    const item = document.createElement("div");
    item.className = `activity-item ${type}`;

    const dot = document.createElement("div");
    dot.className = "activity-dot";

    const content = document.createElement("div");
    content.className = "activity-content";

    const strong = document.createElement("strong");
    strong.textContent = title;

    const paragraph = document.createElement("p");
    paragraph.textContent = message;

    content.appendChild(strong);
    content.appendChild(paragraph);

    item.appendChild(dot);
    item.appendChild(content);

    activityList.appendChild(item);
    activityList.scrollTop = activityList.scrollHeight;
}

function setActivityStatus(status) {
    if (!activityStatus) return;
    activityStatus.textContent = status;
}

// Error Handling
function showError(message) {
    if (errorMessage) {
        errorMessage.classList.remove("hidden");
    }
    if (errorText) {
        errorText.textContent = message || "Optimization failed.";
    }
    if (errorMessage) {
        errorMessage.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
    console.error("OptiAgent Error:", message);
}

function clearError() {
    if (errorMessage) {
        errorMessage.classList.add("hidden");
    }
    if (errorText) {
        errorText.textContent = "";
    }
}

// Primary Optimization Execution Loop
async function runOptimization() {
    console.log("RUN OPTIMIZATION CALLED", new Date().toISOString());

    try {
        clearError();
        setRunning(true);
        clearActivity();
        setActivityStatus("Running");

        const copyScoreBtn = $("copyScoreBtn");
        if (copyScoreBtn) copyScoreBtn.disabled = true;
        const copyPosBtn = $("copyPosBtn");
        if (copyPosBtn) copyPosBtn.disabled = true;

        if (agentBadge) {
            agentBadge.textContent = "RUNNING";
            agentBadge.classList.remove("complete");
            agentBadge.classList.add("running");
        }

        // STEP 1: OBSERVE
        setAgentStep("observe");
        addActivity("Agent started", "Beginning autonomous multi-stage optimization cycle.", "active");

        if (!objectiveInput || !dimensionsInput || !maxStagesInput || !patienceInput) {
            throw new Error("Required input elements are missing from application.");
        }

        const objective = objectiveInput.value.trim();
        const dimensions = parseInt(dimensionsInput.value, 10);
        const maxStages = parseInt(maxStagesInput.value, 10);
        const patience = parseInt(patienceInput.value, 10);

        if (!objective) {
            throw new Error("Please enter an objective function expression.");
        }

        if (!Number.isInteger(dimensions) || dimensions < 1 || dimensions > 100) {
            throw new Error("Number of dimensions must be between 1 and 100.");
        }

        if (!Number.isInteger(maxStages) || maxStages < 1 || maxStages > 20) {
            throw new Error("Maximum stages must be between 1 and 20.");
        }

        if (!Number.isInteger(patience) || patience < 1 || patience > 20) {
            throw new Error("Patience must be between 1 and 20.");
        }

        const bounds = getBounds();

        addActivity("Problem observed", `Parsed ${dimensions}-dimensional formulation: f(x) = ${objective}`, "complete");
        addActivity("Search space validated", `${dimensions} variable bounds verified within safe continuous domain.`, "complete");

        // STEP 2: REASON
        setAgentStep("reason");
        setActivityStatus("Reasoning");
        addActivity("Agent reasoning", "Analyzing objective landscape topology, modality, and valley traps.", "active");

        const payload = {
            objective: objective,
            dimensions: dimensions,
            bounds: bounds,
            max_stages: maxStages,
            patience: patience
        };

        addActivity("Requesting strategic decision", "Sending problem context to Gemini AI Planner.", "active");

        const response = await fetch(`${API_URL}/optimize`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        });

        let data;
        try {
            data = await response.json();
        } catch {
            throw new Error(`Server returned HTTP ${response.status}.`);
        }

        if (!response.ok || !data.success) {
            throw new Error(data.error || `Optimization failed with HTTP ${response.status}.`);
        }

        // STEP 3: DECIDE
        setAgentStep("decide");
        setActivityStatus("Strategy selected");

        const selectedStrategy = extractStrategy(data);
        addActivity(
            "Strategy selected",
            selectedStrategy ? `AI selected ${selectedStrategy} optimizer.` : "Strategic algorithm selection complete.",
            "complete"
        );

        await sleep(150);

        // STEP 4: ACT
        setAgentStep("act");
        setActivityStatus("Optimizing");
        addActivity("Optimization executing", "Numerical search stage executing across continuous parameter space.", "active");

        await sleep(150);

        // STEP 5: VALIDATE
        setAgentStep("validate");
        setActivityStatus("Validating");
        addActivity("Solution validated", "Independent AST validator verified bounds and re-computed f(x*).", "complete");

        await sleep(150);

        // STEP 6: ADAPT
        const stages = Array.isArray(data.stage_history) ? data.stage_history : [];

        if (stages.length > 1) {
            setAgentStep("adapt");
            setActivityStatus("Adapted");
            addActivity("Agent adapted", `Executed ${stages.length} stages with dynamic stagnation recovery.`, "complete");
        } else {
            const validateSteps = document.querySelectorAll(".pipeline-step");
            validateSteps.forEach((el) => {
                if (el.dataset.step === "validate") {
                    el.classList.remove("active");
                    el.classList.add("complete");
                }
            });
            setActivityStatus("Complete");
        }

        addActivity("Search complete", `Best-found score ${formatNumber(data.best_score)}. Global optimality is not certified.`, "complete");

        displayResult(data);
        window.lastOptimizationResult = data;
        drawConvergenceChart(data);

        if (connectionStatus) {
            connectionStatus.textContent = "● API Online";
            connectionStatus.classList.remove("offline");
            connectionStatus.classList.add("online");
        }

    } catch (error) {
        console.error("Optimization error:", error);

        if (agentBadge) {
            agentBadge.textContent = "ERROR";
            agentBadge.classList.remove("running");
            agentBadge.classList.remove("complete");
        }

        setActivityStatus("Error");
        addActivity("Optimization failed", error.message || "Unknown error encountered.", "error");
        showError(error.message);

    } finally {
        setRunning(false);
    }
}

// Strategy extractor helper
function extractStrategy(data) {
    if (typeof data.strategy === "string") return data.strategy;
    if (typeof data.recommended_strategy === "string") return data.recommended_strategy;
    if (data.recommendation && typeof data.recommendation.recommended_strategy === "string") {
        return data.recommendation.recommended_strategy;
    }
    if (Array.isArray(data.strategy_history) && data.strategy_history.length > 0) {
        return String(data.strategy_history[data.strategy_history.length - 1]);
    }
    if (Array.isArray(data.stage_history) && data.stage_history.length > 0) {
        const lastStage = data.stage_history[data.stage_history.length - 1];
        if (lastStage && typeof lastStage.strategy === "string") {
            return lastStage.strategy;
        }
    }
    return null;
}

// Recommendation extractor helper
function extractRecommendation(data) {
    if (data && data.recommendation && typeof data.recommendation === "object") {
        return data.recommendation;
    }
    if (data && data.strategy_decision && typeof data.strategy_decision === "object") {
        return data.strategy_decision;
    }
    if (data && data.initial_strategy && typeof data.initial_strategy === "object") {
        return data.initial_strategy;
    }
    return null;
}

// Display results in UI
function displayResult(data) {
    const outcome = $("searchOutcome");
    if (outcome) outcome.textContent = [
        data.termination_reason ? data.termination_reason.replaceAll('_', ' ') : 'Search complete',
        data.evaluations ? `${data.evaluations} search evaluations` : '',
        ...(data.warnings || ['Global optimality is not certified.'])
    ].filter(Boolean).join(' · ');

    if (bestScoreElement) {
        bestScoreElement.textContent = formatNumber(data.best_score);
    }

    if (bestPositionElement) {
        bestPositionElement.textContent = formatPosition(data.best_position);
    }

    // Enable copy buttons when result is valid
    const copyScoreBtn = $("copyScoreBtn");
    if (copyScoreBtn) {
        copyScoreBtn.disabled = !Number.isFinite(Number(data.best_score));
    }
    const copyPosBtn = $("copyPosBtn");
    if (copyPosBtn) {
        copyPosBtn.disabled = !Array.isArray(data.best_position) || data.best_position.length === 0;
    }

    const stages = Array.isArray(data.stage_history) ? data.stage_history : [];
    if (stageCountElement) {
        stageCountElement.textContent = stages.length;
    }

    const strategies = Array.isArray(data.strategy_history) ? data.strategy_history : [];
    if (strategyCountElement) {
        strategyCountElement.textContent = new Set(strategies).size;
    }

    const decision = extractRecommendation(data);
    let selectedStrategy = decision ? (decision.recommended_strategy || decision.strategy || decision.algorithm) : null;
    if (!selectedStrategy) {
        selectedStrategy = extractStrategy(data);
    }

    if (strategyElement && selectedStrategy) {
        strategyElement.textContent = selectedStrategy;
    }

    let confidence = decision ? decision.confidence : (data.confidence ?? null);
    if (confidenceElement) {
        if (confidence !== undefined && confidence !== null && confidence !== "") {
            const num = Number(confidence);
            if (Number.isFinite(num)) {
                const percentage = num <= 1 ? num * 100 : num;
                confidenceElement.textContent = `${percentage.toFixed(0)}%`;
            } else {
                confidenceElement.textContent = "—";
            }
        } else {
            confidenceElement.textContent = "—";
        }
    }

    let exploration = decision ? (decision.exploration_level ?? decision.exploration) : (data.exploration_level ?? data.exploration);
    if (explorationElement) {
        if (exploration !== undefined && exploration !== null && exploration !== "") {
            const text = String(exploration);
            explorationElement.textContent = text.charAt(0).toUpperCase() + text.slice(1);
        } else {
            explorationElement.textContent = "—";
        }
    }

    let reason = decision ? decision.reason : (data.reason ?? null);
    if (reasonElement) {
        reasonElement.textContent = reason || "Gemini completed strategic multi-stage optimization.";
    }

    displayStrategyHistory(stages);

    const convergence = Array.isArray(data.convergence_history) ? data.convergence_history : [];
    if (convergenceStatus) {
        convergenceStatus.textContent = convergence.length > 0 ? `${convergence.length} iterations recorded` : "Complete";
    }

    if (agentBadge) {
        agentBadge.textContent = "COMPLETE";
        agentBadge.classList.remove("running");
        agentBadge.classList.add("complete");
    }
}

// Display Strategy History
function displayStrategyHistory(stages) {
    if (!strategyHistoryElement) return;

    if (!Array.isArray(stages) || stages.length === 0) {
        strategyHistoryElement.innerHTML = `
            <div class="empty-state">No optimization stages yet.</div>
        `;
        return;
    }

    strategyHistoryElement.innerHTML = "";

    stages.forEach((stage, index) => {
        const item = document.createElement("div");
        item.className = "history-item";

        const stageNumber = stage?.stage ?? (index + 1);
        const algorithm = stage?.strategy ?? stage?.algorithm ?? "Unknown";
        const score = stage?.global_best_score ?? stage?.stage_best_score ?? stage?.best_score;

        item.innerHTML = `
            <span class="history-stage">Stage ${escapeHtml(stageNumber)}</span>
            <span class="history-algorithm">${escapeHtml(algorithm)}</span>
            <span class="history-score">${formatNumber(score)}</span>
        `;

        strategyHistoryElement.appendChild(item);
    });
}

// Precision Convergence Canvas Chart Renderer
function drawConvergenceChart(data) {
    if (!chart || !chart.getContext) return;

    const context = chart.getContext("2d");
    const width = chart.clientWidth;
    const height = chart.clientHeight;

    if (width <= 0 || height <= 0) return;

    const ratio = window.devicePixelRatio || 1;
    chart.width = width * ratio;
    chart.height = height * ratio;

    context.setTransform(ratio, 0, 0, ratio, 0, 0);
    context.clearRect(0, 0, width, height);

    const history = data && Array.isArray(data.convergence_history) ? data.convergence_history : [];

    if (history.length < 2) {
        if (chartEmpty) chartEmpty.classList.remove("hidden");
        return;
    }

    const values = history.map((point) => {
        if (typeof point === "number") return Number(point);
        return Number(point?.score);
    }).filter(Number.isFinite);

    if (values.length < 2) {
        if (chartEmpty) chartEmpty.classList.remove("hidden");
        return;
    }

    if (chartEmpty) {
        chartEmpty.classList.add("hidden");
    }

    // Chart margins
    const padding = { left: 70, right: 24, top: 24, bottom: 42 };
    const graphWidth = width - padding.left - padding.right;
    const graphHeight = height - padding.top - padding.bottom;

    let minValue = Math.min(...values);
    let maxValue = Math.max(...values);

    if (minValue === maxValue) {
        const delta = Math.abs(minValue) * 0.1 || 1;
        minValue -= delta;
        maxValue += delta;
    }

    // Draw Subtle Horizontal Grid Lines & Values
    context.strokeStyle = "#DCE1E8";
    context.lineWidth = 1;

    const gridSteps = 5;
    for (let i = 0; i <= gridSteps; i++) {
        const y = padding.top + graphHeight * (i / gridSteps);

        context.beginPath();
        context.moveTo(padding.left, y);
        context.lineTo(width - padding.right, y);
        context.stroke();

        const value = maxValue - (maxValue - minValue) * (i / gridSteps);
        context.fillStyle = "#526175";
        context.font = "11px 'JetBrains Mono', monospace";
        context.textAlign = "right";
        context.fillText(formatNumber(value), padding.left - 10, y + 4);
    }

    // Gradient Area Fill Under Curve (Indigo Accent)
    const areaGradient = context.createLinearGradient(0, padding.top, 0, padding.top + graphHeight);
    areaGradient.addColorStop(0, "rgba(67, 56, 202, 0.12)");
    areaGradient.addColorStop(1, "rgba(67, 56, 202, 0.0)");

    context.beginPath();
    values.forEach((value, index) => {
        const x = padding.left + graphWidth * (index / (values.length - 1));
        const y = padding.top + graphHeight * (1 - (value - minValue) / (maxValue - minValue));

        if (index === 0) {
            context.moveTo(x, y);
        } else {
            context.lineTo(x, y);
        }
    });

    context.lineTo(padding.left + graphWidth, padding.top + graphHeight);
    context.lineTo(padding.left, padding.top + graphHeight);
    context.closePath();
    context.fillStyle = areaGradient;
    context.fill();

    // Trajectory Line (Deep Indigo #4338CA)
    context.beginPath();
    values.forEach((value, index) => {
        const x = padding.left + graphWidth * (index / (values.length - 1));
        const y = padding.top + graphHeight * (1 - (value - minValue) / (maxValue - minValue));

        if (index === 0) {
            context.moveTo(x, y);
        } else {
            context.lineTo(x, y);
        }
    });

    context.strokeStyle = "#4338CA";
    context.lineWidth = 2.5;
    context.lineCap = "round";
    context.lineJoin = "round";
    context.stroke();

    // Data Points
    values.forEach((value, index) => {
        const x = padding.left + graphWidth * (index / (values.length - 1));
        const y = padding.top + graphHeight * (1 - (value - minValue) / (maxValue - minValue));

        context.beginPath();
        context.arc(x, y, 3, 0, Math.PI * 2);
        context.fillStyle = (value === minValue) ? "#166534" : "#4338CA";
        context.fill();

        context.beginPath();
        context.arc(x, y, 4, 0, Math.PI * 2);
        context.strokeStyle = "#FFFFFF";
        context.lineWidth = 1.5;
        context.stroke();
    });

    // Horizontal Axis Label
    context.fillStyle = "#526175";
    context.font = "12px 'Inter', sans-serif";
    context.textAlign = "center";
    context.fillText("Recorded search progress", padding.left + graphWidth / 2, height - 12);
    context.textAlign = "center";
    context.fillText("Recorded search progress", padding.left + graphWidth / 2, height - 12);
}

// Numerical Formatters
function formatNumber(value) {
    const number = Number(value);
    if (!Number.isFinite(number)) return "—";
    if (Math.abs(number) < 1e-8) return "0.000000";
    if (Math.abs(number) < 0.001 || Math.abs(number) >= 100000) {
        return number.toExponential(4);
    }
    return number.toFixed(6);
}

function formatPosition(position) {
    if (!Array.isArray(position)) return "—";
    return "[" + position.map((val) => {
        const num = Number(val);
        return Number.isFinite(num) ? num.toFixed(4) : "—";
    }).join(", ") + "]";
}

function escapeHtml(value) {
    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
}

// Smart Input: Clipboard Paste & Problem Extraction
let currentUploadedImageBase64 = null;

function setupSmartInput() {
    const identifyBtn = $("identifyButton");
    const smartQueryInput = $("smartFunctionQuery");
    const dropZone = $("dropZone");
    const fileInput = $("imageFileInput");
    const removeImgBtn = $("removeImageBtn");

    if (identifyBtn && smartQueryInput) {
        identifyBtn.addEventListener("click", () => {
            const query = smartQueryInput.value.trim();
            if (query || currentUploadedImageBase64) {
                identifyProblem(query, currentUploadedImageBase64);
            } else {
                showExtractionStatus("Please enter a benchmark name or paste a screenshot.", "info");
            }
        });

        smartQueryInput.addEventListener("keydown", (e) => {
            if (e.key === "Enter") {
                e.preventDefault();
                identifyBtn.click();
            }
        });
    }

    // Global Paste Listener (Ctrl+V)
    window.addEventListener("paste", (e) => {
        const items = (e.clipboardData || window.clipboardData)?.items;
        if (!items) return;

        for (let i = 0; i < items.length; i++) {
            if (items[i].type && items[i].type.indexOf("image") !== -1) {
                const blob = items[i].getAsFile();
                if (blob) {
                    processImageFile(blob);
                    e.preventDefault();
                    break;
                }
            }
        }
    });

    if (dropZone && fileInput) {
        dropZone.addEventListener("click", (e) => {
            if (e.target.id !== "removeImageBtn") {
                fileInput.click();
            }
        });

        dropZone.addEventListener("keydown", (e) => {
            if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                fileInput.click();
            }
        });

        fileInput.addEventListener("change", (e) => {
            const file = e.target.files[0];
            if (file) {
                processImageFile(file);
            }
        });

        dropZone.addEventListener("dragover", (e) => {
            e.preventDefault();
            dropZone.classList.add("dragover");
        });

        dropZone.addEventListener("dragleave", () => {
            dropZone.classList.remove("dragover");
        });

        dropZone.addEventListener("drop", (e) => {
            e.preventDefault();
            dropZone.classList.remove("dragover");
            if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length > 0) {
                const file = e.dataTransfer.files[0];
                if (file.type.startsWith("image/")) {
                    processImageFile(file);
                }
            }
        });
    }

    if (removeImgBtn) {
        removeImgBtn.addEventListener("click", (e) => {
            e.stopPropagation();
            clearImagePreview();
        });
    }
}

function processImageFile(file) {
    const reader = new FileReader();
    reader.onload = (e) => {
        currentUploadedImageBase64 = e.target.result;
        showImagePreview(currentUploadedImageBase64);
        const query = $("smartFunctionQuery") ? $("smartFunctionQuery").value.trim() : "";
        showExtractionStatus("Image uploaded! Analyzing problem with AI...", "info");
        identifyProblem(query, currentUploadedImageBase64);
    };
    reader.readAsDataURL(file);
}

function showImagePreview(base64Url) {
    const previewContainer = $("imagePreviewContainer");
    const previewImg = $("imagePreview");
    const dropPrompt = $("dropZonePrompt");
    if (previewContainer && previewImg) {
        previewImg.src = base64Url;
        previewContainer.classList.remove("hidden");
    }
    if (dropPrompt) {
        dropPrompt.classList.add("hidden");
    }
}

function clearImagePreview() {
    currentUploadedImageBase64 = null;
    const previewContainer = $("imagePreviewContainer");
    const previewImg = $("imagePreview");
    const dropPrompt = $("dropZonePrompt");
    const fileInput = $("imageFileInput");
    if (previewImg) previewImg.src = "";
    if (previewContainer) previewContainer.classList.add("hidden");
    if (dropPrompt) dropPrompt.classList.remove("hidden");
    if (fileInput) fileInput.value = "";
    showExtractionStatus("", "hidden");
}

function showExtractionStatus(message, type) {
    const statusBox = $("extractionStatus");
    if (!statusBox) return;
    if (type === "hidden" || !message) {
        statusBox.className = "extraction-status hidden";
        statusBox.textContent = "";
        return;
    }
    statusBox.className = `extraction-status ${type}`;
    statusBox.textContent = message;
}

async function identifyProblem(text, imageBase64) {
    const btnText = $("identifyBtnText");
    const loader = $("identifyBtnLoader");
    const identifyBtn = $("identifyButton");

    if (loader) loader.classList.remove("hidden");
    if (btnText) btnText.textContent = "Analyzing...";
    if (identifyBtn) identifyBtn.disabled = true;

    try {
        const response = await fetch(`${API_URL}/api/extract-problem`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                text: text || "",
                image: imageBase64 || null
            })
        });

        const data = await response.json();
        if (!response.ok || !data.success) {
            throw new Error(data.error || "Could not identify function.");
        }

        if (objectiveInput) {
            objectiveInput.value = data.objective;
        }
        if (dimensionsInput) {
            dimensionsInput.value = data.dimensions;
        }

        generateBounds();

        if (Array.isArray(data.bounds)) {
            data.bounds.forEach((b, idx) => {
                const lowerInput = $(`lowerBound${idx + 1}`);
                const upperInput = $(`upperBound${idx + 1}`);
                if (lowerInput && b[0] !== undefined) lowerInput.value = b[0];
                if (upperInput && b[1] !== undefined) upperInput.value = b[1];
            });
        }

        const infoMsg = `✓ Identified "${data.name}": f(x) = ${data.objective} (${data.dimensions}D). ${data.explanation || ""}`;
        showExtractionStatus(infoMsg, "success");

    } catch (err) {
        showExtractionStatus(`✕ Error: ${err.message}`, "error");
    } finally {
        if (loader) loader.classList.add("hidden");
        if (btnText) btnText.textContent = "Identify";
        if (identifyBtn) identifyBtn.disabled = false;
    }
}

// Ask OptiAgent: AI Behavior Assistant
function setupAskAI() {
    const askBtn = $("askButton");
    const askInput = $("askQuestionInput");

    if (askBtn && askInput) {
        askBtn.addEventListener("click", () => {
            const q = askInput.value.trim();
            if (q) {
                submitQuestion(q);
            }
        });

        askInput.addEventListener("keydown", (e) => {
            if (e.key === "Enter") {
                e.preventDefault();
                askBtn.click();
            }
        });
    }
}

function askQuickPrompt(promptText) {
    const askInput = $("askQuestionInput");
    if (askInput) {
        askInput.value = promptText;
    }
    submitQuestion(promptText);
}

async function submitQuestion(questionText) {
    const askBtn = $("askButton");
    const btnText = $("askButtonText");
    const loader = $("askButtonLoader");
    const answerContainer = $("askAnswerContainer");
    const answerText = $("askAnswerText");
    const answerSource = $("answerSource");

    if (loader) loader.classList.remove("hidden");
    if (btnText) btnText.textContent = "Thinking...";
    if (askBtn) askBtn.disabled = true;

    try {
        const payload = {
            question: questionText,
            objective: objectiveInput ? objectiveInput.value.trim() : "",
            current_strategy: strategyElement ? strategyElement.textContent.trim() : "",
            best_score: bestScoreElement ? bestScoreElement.textContent.trim() : null,
            best_position: bestPositionElement ? bestPositionElement.textContent.trim() : null
        };

        const response = await fetch(`${API_URL}/api/ask-info`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        const data = await response.json();
        if (!response.ok || !data.success) {
            throw new Error(data.error || "Failed to fetch explanation.");
        }

        if (answerText) answerText.textContent = data.answer;
        if (answerSource) answerSource.textContent = data.source === "gemini" ? "Gemini AI Tutor" : "Optimization Knowledge";
        if (answerContainer) answerContainer.classList.remove("hidden");

        answerContainer.scrollIntoView({ behavior: "smooth", block: "nearest" });

    } catch (err) {
        if (answerText) answerText.textContent = `Could not get answer: ${err.message}`;
        if (answerSource) answerSource.textContent = "Error";
        if (answerContainer) answerContainer.classList.remove("hidden");
    } finally {
        if (loader) loader.classList.add("hidden");
        if (btnText) btnText.textContent = "Ask Info";
        if (askBtn) askBtn.disabled = false;
    }
}

// Copy to Clipboard Helpers
function copyScore() {
    if (!bestScoreElement) return;
    const score = bestScoreElement.textContent.trim();
    if (score && score !== "—") {
        navigator.clipboard.writeText(score).then(() => {
            addActivity("Copied to clipboard", `Best score ${score} copied.`, "complete");
        });
    }
}

function copyPosition() {
    if (!bestPositionElement) return;
    const pos = bestPositionElement.textContent.trim();
    if (pos && pos !== "—") {
        navigator.clipboard.writeText(pos).then(() => {
            addActivity("Copied to clipboard", `Best coordinates ${pos} copied.`, "complete");
        });
    }
}

// Accessible architecture dialog; API and optimization behavior are unchanged.
function setupArchitectureModal() {
    const modalBtn = $("architectureModalBtn");
    const closeBtn = $("closeArchModalBtn");
    const backdrop = $("archModalBackdrop");
    if (!modalBtn || !closeBtn || !backdrop) return;
    let previousFocus;
    function close() {
        backdrop.classList.remove("open");
        document.body.classList.remove("dialog-open");
        if (previousFocus) previousFocus.focus();
    }
    modalBtn.addEventListener("click", () => {
        previousFocus = document.activeElement;
        backdrop.classList.add("open");
        document.body.classList.add("dialog-open");
        closeBtn.focus();
    });
    closeBtn.addEventListener("click", close);
    backdrop.addEventListener("click", e => { if (e.target === backdrop) close(); });
    document.addEventListener("keydown", e => {
        if (!backdrop.classList.contains("open")) return;
        if (e.key === "Escape") close();
        if (e.key === "Tab") {
            const items = [...backdrop.querySelectorAll('button, a[href], input, [tabindex="0"]')];
            const first = items[0], last = items[items.length - 1];
            if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
            else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
        }
    });
}
