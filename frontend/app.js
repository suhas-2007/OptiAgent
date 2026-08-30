// ======================================================
// OPTIAGENT FRONTEND
// ======================================================

// ======================================================
// CONFIGURATION
// ======================================================

const API_URL = "https://optiagent-api.onrender.com";


// ======================================================
// DOM HELPERS
// ======================================================

function $(id) {
    return document.getElementById(id);
}


// ======================================================
// DOM REFERENCES
// ======================================================

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


// ======================================================
// INITIALIZE DOM
// ======================================================

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

    // --------------------------------------------------
    // Important compatibility aliases
    // --------------------------------------------------

    // Some older versions of the application used
    // activityLog instead of activityList.
    //
    // We intentionally use activityList everywhere.
    // This prevents:
    // Cannot set properties of null
    // --------------------------------------------------

    if (!activityList) {
        console.warn(
            "activityList element was not found in index.html."
        );
    }
}


// ======================================================
// STARTUP
// ======================================================

document.addEventListener(
    "DOMContentLoaded",
    () => {

        initializeDOM();

        generateBounds();

        checkAPI();

        if (dimensionsInput) {

            dimensionsInput.addEventListener(
                "input",
                generateBounds
            );
        }

        if (optimizeButton) {

            optimizeButton.addEventListener(
                "click",
                runOptimization
            );
        }

        window.addEventListener(
            "resize",
            () => {

                drawConvergenceChart(
                    window.lastOptimizationResult
                );
            }
        );
    }
);


// ======================================================
// API HEALTH
// ======================================================

async function checkAPI() {

    if (!connectionStatus) {
        return;
    }

    try {

        const response =
            await fetch(
                `${API_URL}/health`,
                {
                    method: "GET",
                    cache: "no-store"
                }
            );

        if (!response.ok) {

            throw new Error(
                `API returned HTTP ${response.status}`
            );
        }

        const data =
            await response.json();

        console.log(
            "OptiAgent API health:",
            data
        );

        if (data.status !== "ok") {

            throw new Error(
                "Invalid API health response."
            );
        }

        connectionStatus.textContent =
            "● API Online";

        connectionStatus.classList.remove(
            "offline"
        );

        connectionStatus.classList.add(
            "online"
        );

    } catch (error) {

        console.error(
            "API health check failed:",
            error
        );

        connectionStatus.textContent =
            "● API Offline";

        connectionStatus.classList.remove(
            "online"
        );

        connectionStatus.classList.add(
            "offline"
        );
    }
}


// ======================================================
// GENERATE BOUNDS
// ======================================================

function generateBounds() {

    if (
        !dimensionsInput ||
        !boundsContainer
    ) {
        return;
    }

    const dimensions =
        parseInt(
            dimensionsInput.value,
            10
        );

    if (
        !Number.isInteger(dimensions) ||
        dimensions < 1 ||
        dimensions > 50
    ) {

        boundsContainer.innerHTML =
            "";

        return;
    }

    boundsContainer.innerHTML =
        "";

    for (
        let i = 1;
        i <= dimensions;
        i++
    ) {

        const row =
            document.createElement(
                "div"
            );

        row.className =
            "bound-row";

        row.innerHTML = `
            <span class="bound-label">
                x${i}
            </span>

            <input
                type="number"
                class="lower-bound"
                data-index="${i}"
                value="-10"
                step="any"
                placeholder="Lower"
            >

            <input
                type="number"
                class="upper-bound"
                data-index="${i}"
                value="10"
                step="any"
                placeholder="Upper"
            >
        `;

        boundsContainer.appendChild(
            row
        );
    }
}


// ======================================================
// EXAMPLES
// ======================================================

function setExample(expression) {

    if (!objectiveInput) {
        return;
    }

    objectiveInput.value =
        expression;
}


// ======================================================
// GET BOUNDS
// ======================================================

function getBounds() {

    const lowerInputs =
        document.querySelectorAll(
            ".lower-bound"
        );

    const upperInputs =
        document.querySelectorAll(
            ".upper-bound"
        );

    const bounds = [];

    for (
        let i = 0;
        i < lowerInputs.length;
        i++
    ) {

        const lower =
            parseFloat(
                lowerInputs[i].value
            );

        const upper =
            parseFloat(
                upperInputs[i].value
            );

        if (
            !Number.isFinite(lower) ||
            !Number.isFinite(upper)
        ) {

            throw new Error(
                `Invalid bounds for x${i + 1}.`
            );
        }

        if (lower >= upper) {

            throw new Error(
                `Lower bound must be less than ` +
                `upper bound for x${i + 1}.`
            );
        }

        bounds.push([
            lower,
            upper
        ]);
    }

    return bounds;
}


// ======================================================
// AGENT PIPELINE
// ======================================================

function setAgentStep(step) {

    const steps =
        document.querySelectorAll(
            ".pipeline-step"
        );

    const order = [
        "observe",
        "reason",
        "decide",
        "act",
        "validate",
        "adapt"
    ];

    const currentIndex =
        order.indexOf(step);

    steps.forEach(
        element => {

            const elementStep =
                element.dataset.step;

            const index =
                order.indexOf(
                    elementStep
                );

            element.classList.remove(
                "active"
            );

            element.classList.remove(
                "complete"
            );

            if (
                index < currentIndex
            ) {

                element.classList.add(
                    "complete"
                );
            }

            if (
                index === currentIndex
            ) {

                element.classList.add(
                    "active"
                );
            }
        }
    );
}


// ======================================================
// BUTTON STATE
// ======================================================

function setRunning(running) {

    if (optimizeButton) {

        optimizeButton.disabled =
            running;
    }

    if (buttonText) {

        buttonText.textContent =
            running
                ? "Agent is optimizing..."
                : "Run OptiAgent";
    }

    if (buttonLoader) {

        buttonLoader.classList.toggle(
            "hidden",
            !running
        );
    }
}


// ======================================================
// ACTIVITY
// ======================================================

function clearActivity() {

    if (!activityList) {
        return;
    }

    activityList.innerHTML =
        "";
}


function clearActivityLog() {

    // Compatibility function.
    // Both old and new calls now operate
    // on the same activityList element.

    clearActivity();
}


function addActivity(
    title,
    message,
    type = "info"
) {

    if (!activityList) {

        console.warn(
            "Cannot display activity: " +
            "activityList element is missing."
        );

        return;
    }

    const item =
        document.createElement(
            "div"
        );

    item.className =
        `activity-item ${type}`;

    const dot =
        document.createElement(
            "div"
        );

    dot.className =
        "activity-dot";

    const content =
        document.createElement(
            "div"
        );

    content.className =
        "activity-content";

    const strong =
        document.createElement(
            "strong"
        );

    strong.textContent =
        title;

    const paragraph =
        document.createElement(
            "p"
        );

    paragraph.textContent =
        message;

    content.appendChild(
        strong
    );

    content.appendChild(
        paragraph
    );

    item.appendChild(
        dot
    );

    item.appendChild(
        content
    );

    activityList.appendChild(
        item
    );

    activityList.scrollTop =
        activityList.scrollHeight;
}


function setActivityStatus(status) {

    if (!activityStatus) {
        return;
    }

    activityStatus.textContent =
        status;
}


// ======================================================
// ERROR PANEL
// ======================================================

function showError(message) {

    if (errorMessage) {

        errorMessage.classList.remove(
            "hidden"
        );
    }

    if (errorText) {

        errorText.textContent =
            message ||
            "Optimization failed.";
    }

    console.error(
        "OptiAgent Error:",
        message
    );
}


function clearError() {

    if (errorMessage) {

        errorMessage.classList.add(
            "hidden"
        );
    }

    if (errorText) {

        errorText.textContent =
            "";
    }
}


// ======================================================
// RUN OPTIMIZATION
// ======================================================

async function runOptimization() {

    console.log(
        "RUN OPTIMIZATION CALLED",
        new Date().toISOString()
    );
    try {

        clearError();

        setRunning(true);

        clearActivity();

        setActivityStatus(
            "Running"
        );

        if (agentBadge) {

            agentBadge.textContent =
                "Running";

            agentBadge.classList.remove(
                "complete"
            );

            agentBadge.classList.add(
                "running"
            );
        }


        // ==================================================
        // OBSERVE
        // ==================================================

        setAgentStep(
            "observe"
        );

        addActivity(
            "Agent started",
            "Beginning autonomous optimization.",
            "active"
        );


        // ==================================================
        // INPUT
        // ==================================================

        if (
            !objectiveInput ||
            !dimensionsInput ||
            !maxStagesInput ||
            !patienceInput
        ) {

            throw new Error(
                "Required input elements are missing from index.html."
            );
        }

        const objective =
            objectiveInput.value.trim();

        const dimensions =
            parseInt(
                dimensionsInput.value,
                10
            );

        const maxStages =
            parseInt(
                maxStagesInput.value,
                10
            );

        const patience =
            parseInt(
                patienceInput.value,
                10
            );


        if (!objective) {

            throw new Error(
                "Please enter an objective function."
            );
        }


        if (
            !Number.isInteger(dimensions) ||
            dimensions < 1 ||
            dimensions > 50
        ) {

            throw new Error(
                "Number of dimensions must be between 1 and 50."
            );
        }


        if (
            !Number.isInteger(maxStages) ||
            maxStages < 1 ||
            maxStages > 20
        ) {

            throw new Error(
                "Maximum stages must be between 1 and 20."
            );
        }


        if (
            !Number.isInteger(patience) ||
            patience < 1 ||
            patience > 20
        ) {

            throw new Error(
                "Patience must be between 1 and 20."
            );
        }


        const bounds =
            getBounds();


        addActivity(
            "Problem observed",
            `Received a ${dimensions}-dimensional optimization problem.`,
            "complete"
        );


        addActivity(
            "Search space identified",
            `${dimensions} variable bounds validated successfully.`,
            "complete"
        );


        // ==================================================
        // REASON
        // ==================================================

        setAgentStep(
            "reason"
        );

        setActivityStatus(
            "Reasoning"
        );

        addActivity(
            "Agent reasoning",
            "Analyzing the objective function and search space.",
            "active"
        );


        // ==================================================
        // PAYLOAD
        // ==================================================

        const payload = {

            objective:
                objective,

            dimensions:
                dimensions,

            bounds:
                bounds,

            max_stages:
                maxStages,

            patience:
                patience
        };


        // ==================================================
        // GEMINI REQUEST
        // ==================================================

        addActivity(
            "Requesting strategic decision",
            "Sending the optimization problem to the AI planner.",
            "active"
        );


        const response =
            await fetch(
                `${API_URL}/optimize`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify(
                            payload
                        )
                }
            );


        let data;


        try {

            data =
                await response.json();

        } catch {

            throw new Error(
                `Server returned HTTP ${response.status}.`
            );
        }


        console.log(
            "OptiAgent API result:",
            data
        );


        // ==================================================
        // API ERROR
        // ==================================================

        if (
            !response.ok ||
            !data.success
        ) {

            throw new Error(
                data.error ||
                `Optimization failed with HTTP ${response.status}.`
            );
        }


        // ==================================================
        // DECIDE
        // ==================================================

        setAgentStep(
            "decide"
        );

        setActivityStatus(
            "Strategy selected"
        );


        const selectedStrategy =
            extractStrategy(
                data
            );


        addActivity(
            "Strategy selected",
            selectedStrategy
                ? `AI selected ${selectedStrategy}.`
                : "Gemini successfully selected an optimization strategy.",
            "complete"
        );


        await sleep(150);


        // ==================================================
        // ACT
        // ==================================================

        setAgentStep(
            "act"
        );

        setActivityStatus(
            "Optimizing"
        );

        addActivity(
            "Optimization executing",
            "The selected numerical optimizer is searching the solution space.",
            "active"
        );


        await sleep(150);


        // ==================================================
        // VALIDATE
        // ==================================================

        setAgentStep(
            "validate"
        );

        setActivityStatus(
            "Validating"
        );

        addActivity(
            "Solution validated",
            "Checking the optimizer result and objective score.",
            "complete"
        );


        await sleep(150);


        // ==================================================
        // ADAPT
        // ==================================================

        const stages =
            Array.isArray(
                data.stage_history
            )
                ? data.stage_history
                : [];


        if (
            stages.length > 1
        ) {

            setAgentStep(
                "adapt"
            );

            setActivityStatus(
                "Adapted"
            );

            addActivity(
                "Agent adapted",
                `${stages.length} optimization stages were executed.`,
                "complete"
            );

        } else {

            // Mark validate complete
            const validateSteps =
                document.querySelectorAll(
                    ".pipeline-step"
                );

            validateSteps.forEach(
                element => {

                    if (
                        element.dataset.step ===
                        "validate"
                    ) {

                        element.classList.remove(
                            "active"
                        );

                        element.classList.add(
                            "complete"
                        );
                    }
                }
            );

            setActivityStatus(
                "Complete"
            );
        }


        // ==================================================
        // COMPLETE
        // ==================================================

        addActivity(
            "Optimization complete",
            "Best solution obtained and results are ready.",
            "complete"
        );


        // ==================================================
        // DISPLAY RESULT
        // ==================================================

        displayResult(
            data
        );


        window.lastOptimizationResult =
            data;


        drawConvergenceChart(
            data
        );


        // ==================================================
        // API STATUS
        // ==================================================

        if (connectionStatus) {

            connectionStatus.textContent =
                "● API Online";

            connectionStatus.classList.remove(
                "offline"
            );

            connectionStatus.classList.add(
                "online"
            );
        }


    } catch (error) {

        console.error(
            "Optimization error:",
            error
        );


        if (agentBadge) {

            agentBadge.textContent =
                "Error";

            agentBadge.classList.remove(
                "running"
            );

            agentBadge.classList.remove(
                "complete"
            );
        }


        setActivityStatus(
            "Error"
        );


        addActivity(
            "Optimization failed",
            error.message ||
            "Unknown error",
            "error"
        );


        showError(
            error.message
        );


    } finally {

        setRunning(
            false
        );
    }
}


// ======================================================
// EXTRACT STRATEGY
// ======================================================

function extractStrategy(data) {

    // --------------------------------------------------
    // Direct strategy
    // --------------------------------------------------

    if (
        typeof data.strategy ===
        "string"
    ) {

        return data.strategy;
    }


    // --------------------------------------------------
    // Direct recommended strategy
    // --------------------------------------------------

    if (
        typeof data.recommended_strategy ===
        "string"
    ) {

        return data.recommended_strategy;
    }


    // --------------------------------------------------
    // Gemini recommendation
    // --------------------------------------------------

    if (
        data.recommendation &&
        typeof data.recommendation
            .recommended_strategy ===
        "string"
    ) {

        return data.recommendation
            .recommended_strategy;
    }


    // --------------------------------------------------
    // Strategy history
    // --------------------------------------------------

    if (
        Array.isArray(
            data.strategy_history
        ) &&
        data.strategy_history.length > 0
    ) {

        return String(
            data.strategy_history[
            data.strategy_history.length - 1
            ]
        );
    }


    // --------------------------------------------------
    // Stage history
    // --------------------------------------------------

    if (
        Array.isArray(
            data.stage_history
        ) &&
        data.stage_history.length > 0
    ) {

        const lastStage =
            data.stage_history[
            data.stage_history.length - 1
            ];

        if (
            lastStage &&
            typeof lastStage.strategy ===
            "string"
        ) {

            return lastStage.strategy;
        }
    }


    return null;
}


// ======================================================
// EXTRACT RECOMMENDATION
// ======================================================

function extractRecommendation(data) {

    if (
        data &&
        data.recommendation &&
        typeof data.recommendation ===
        "object"
    ) {

        return data.recommendation;
    }


    if (
        data &&
        data.strategy_decision &&
        typeof data.strategy_decision ===
        "object"
    ) {

        return data.strategy_decision;
    }


    if (
        data &&
        data.initial_strategy &&
        typeof data.initial_strategy ===
        "object"
    ) {

        return data.initial_strategy;
    }


    return null;
}


// ======================================================
// DISPLAY RESULT
// ======================================================

function displayResult(data) {

    console.log(
        "Displaying OptiAgent result:",
        data
    );


    // ==================================================
    // BASIC RESULT
    // ==================================================

    if (bestScoreElement) {

        bestScoreElement.textContent =
            formatNumber(
                data.best_score
            );
    }


    if (bestPositionElement) {

        bestPositionElement.textContent =
            formatPosition(
                data.best_position
            );
    }


    // ==================================================
    // STAGES
    // ==================================================

    const stages =
        Array.isArray(
            data.stage_history
        )
            ? data.stage_history
            : [];


    if (stageCountElement) {

        stageCountElement.textContent =
            stages.length;
    }


    // ==================================================
    // STRATEGIES
    // ==================================================

    const strategies =
        Array.isArray(
            data.strategy_history
        )
            ? data.strategy_history
            : [];


    if (strategyCountElement) {

        strategyCountElement.textContent =
            new Set(
                strategies
            ).size;
    }


    // ==================================================
    // GEMINI RECOMMENDATION
    // ==================================================

    const decision =
        extractRecommendation(
            data
        );


    console.log(
        "Gemini recommendation:",
        decision
    );


    // ==================================================
    // STRATEGY
    // ==================================================

    let selectedStrategy =
        null;


    if (decision) {

        selectedStrategy =
            decision.recommended_strategy ||
            decision.strategy ||
            decision.algorithm;
    }


    if (
        !selectedStrategy
    ) {

        selectedStrategy =
            extractStrategy(
                data
            );
    }


    if (
        strategyElement &&
        selectedStrategy
    ) {

        strategyElement.textContent =
            selectedStrategy;
    }


    // ==================================================
    // CONFIDENCE
    // ==================================================

    let confidence =
        null;


    if (decision) {

        confidence =
            decision.confidence;
    }


    if (
        confidence ===
        undefined ||
        confidence ===
        null
    ) {

        confidence =
            data.confidence;
    }


    if (
        confidenceElement
    ) {

        if (
            confidence !==
            undefined &&
            confidence !==
            null &&
            confidence !== ""
        ) {

            const number =
                Number(
                    confidence
                );


            if (
                Number.isFinite(
                    number
                )) {

                const percentage =
                    number <= 1
                        ? number * 100
                        : number;


                confidenceElement.textContent =
                    `${percentage.toFixed(0)}%`;

            } else {

                confidenceElement.textContent =
                    "—";
            }

        } else {

            confidenceElement.textContent =
                "—";
        }
    }


    // ==================================================
    // EXPLORATION
    // ==================================================

    let exploration =
        null;


    if (decision) {

        exploration =
            decision.exploration_level ??
            decision.exploration;
    }


    if (
        exploration ===
        undefined ||
        exploration ===
        null
    ) {

        exploration =
            data.exploration_level ??
            data.exploration;
    }


    if (
        explorationElement
    ) {

        if (
            exploration !==
            undefined &&
            exploration !==
            null &&
            exploration !== ""
        ) {

            const text =
                String(
                    exploration
                );


            explorationElement.textContent =
                text.charAt(0).toUpperCase()
                +
                text.slice(1);

        } else {

            explorationElement.textContent =
                "—";
        }
    }


    // ==================================================
    // AI REASON
    // ==================================================

    let reason =
        null;


    if (decision) {

        reason =
            decision.reason;
    }


    if (
        !reason &&
        data.reason
    ) {

        reason =
            data.reason;
    }


    if (reasonElement) {

        reasonElement.textContent =
            reason ||
            "Gemini completed the strategic decision.";
    }


    // ==================================================
    // STRATEGY HISTORY
    // ==================================================

    displayStrategyHistory(
        stages
    );


    // ==================================================
    // CONVERGENCE
    // ==================================================

    const convergence =
        Array.isArray(
            data.convergence_history
        )
            ? data.convergence_history
            : [];


    if (convergenceStatus) {

        convergenceStatus.textContent =
            convergence.length > 0
                ? `${convergence.length} iterations recorded`
                : "Optimization completed";
    }


    // ==================================================
    // AGENT BADGE
    // ==================================================

    if (agentBadge) {

        agentBadge.textContent =
            "Complete";

        agentBadge.classList.remove(
            "running"
        );

        agentBadge.classList.add(
            "complete"
        );
    }
}


// ======================================================
// STRATEGY HISTORY
// ======================================================

function displayStrategyHistory(
    stages
) {

    if (!strategyHistoryElement) {
        return;
    }


    if (
        !Array.isArray(stages) ||
        stages.length === 0
    ) {

        strategyHistoryElement.innerHTML =
            `
            <div class="empty-state">
                No optimization stages yet.
            </div>
            `;

        return;
    }


    strategyHistoryElement.innerHTML =
        "";


    stages.forEach(
        (
            stage,
            index
        ) => {

            const item =
                document.createElement(
                    "div"
                );

            item.className =
                "history-item";


            const stageNumber =
                stage?.stage ??
                index + 1;


            const algorithm =
                stage?.strategy ??
                stage?.algorithm ??
                "Unknown";


            const score =
                stage?.global_best_score ??
                stage?.stage_best_score ??
                stage?.best_score;


            item.innerHTML = `
                <span class="history-stage">
                    Stage ${escapeHtml(stageNumber)}
                </span>

                <span class="history-algorithm">
                    ${escapeHtml(algorithm)}
                </span>

                <span class="history-score">
                    ${formatNumber(score)}
                </span>
            `;


            strategyHistoryElement.appendChild(
                item
            );
        }
    );
}


// ======================================================
// CONVERGENCE CHART
// ======================================================

function drawConvergenceChart(
    data
) {

    if (
        !chart ||
        !chart.getContext
    ) {

        return;
    }


    const context =
        chart.getContext(
            "2d"
        );


    const width =
        chart.clientWidth;


    const height =
        chart.clientHeight;


    if (
        width <= 0 ||
        height <= 0
    ) {

        return;
    }


    const ratio =
        window.devicePixelRatio ||
        1;


    chart.width =
        width * ratio;


    chart.height =
        height * ratio;


    context.setTransform(
        ratio,
        0,
        0,
        ratio,
        0,
        0
    );


    context.clearRect(
        0,
        0,
        width,
        height
    );


    const history =
        data &&
            Array.isArray(
                data.convergence_history
            )
            ? data.convergence_history
            : [];


    if (
        history.length < 2
    ) {

        if (chartEmpty) {

            chartEmpty.classList.remove(
                "hidden"
            );
        }

        return;
    }


    const values =
        history
            .map(
                point => {

                    if (
                        typeof point ===
                        "number"
                    ) {

                        return Number(
                            point
                        );
                    }


                    return Number(
                        point?.score
                    );
                }
            )
            .filter(
                Number.isFinite
            );


    if (
        values.length < 2
    ) {

        if (chartEmpty) {

            chartEmpty.classList.remove(
                "hidden"
            );
        }

        return;
    }


    if (chartEmpty) {

        chartEmpty.classList.add(
            "hidden"
        );
    }


    // ==================================================
    // GRAPH DIMENSIONS
    // ==================================================

    const padding = {

        left: 65,

        right: 20,

        top: 20,

        bottom: 40
    };


    const graphWidth =
        width -
        padding.left -
        padding.right;


    const graphHeight =
        height -
        padding.top -
        padding.bottom;


    // ==================================================
    // RANGE
    // ==================================================

    let minValue =
        Math.min(
            ...values
        );


    let maxValue =
        Math.max(
            ...values
        );


    if (
        minValue ===
        maxValue
    ) {

        const delta =
            Math.abs(
                minValue
            ) * 0.1 ||
            1;


        minValue -=
            delta;


        maxValue +=
            delta;
    }
    // ==================================================
    // GRID
    // ==================================================

    context.strokeStyle =
        "#1d314b";

    context.lineWidth =
        1;


    for (
        let i = 0;
        i <= 5;
        i++
    ) {

        const y =
            padding.top +
            graphHeight *
            (
                i / 5
            );


        context.beginPath();


        context.moveTo(
            padding.left,
            y
        );


        context.lineTo(
            width -
            padding.right,
            y
        );


        context.stroke();


        const value =
            maxValue -
            (
                maxValue -
                minValue
            ) *
            (
                i / 5
            );


        context.fillStyle =
            "#8fa4bd";


        context.font =
            "10px sans-serif";


        context.textAlign =
            "right";


        context.fillText(
            formatNumber(
                value
            ),
            padding.left - 8,
            y + 3
        );
    }


    // ==================================================
    // LINE
    // ==================================================

    context.beginPath();


    values.forEach(
        (
            value,
            index
        ) => {

            const x =
                padding.left +
                graphWidth *
                (
                    index /
                    (
                        values.length -
                        1
                    )
                );


            const y =
                padding.top +
                graphHeight *
                (
                    1 -
                    (
                        value -
                        minValue
                    ) /
                    (
                        maxValue -
                        minValue
                    )
                );


            if (
                index === 0
            ) {

                context.moveTo(
                    x,
                    y
                );

            } else {

                context.lineTo(
                    x,
                    y
                );
            }
        }
    );


    context.strokeStyle =
        "#55d6be";

    context.lineWidth =
        2.5;

    context.stroke();


    // ==================================================
    // POINTS
    // ==================================================

    values.forEach(
        (
            value,
            index
        ) => {

            const x =
                padding.left +
                graphWidth *
                (
                    index /
                    (
                        values.length -
                        1
                    )
                );


            const y =
                padding.top +
                graphHeight *
                (
                    1 -
                    (
                        value -
                        minValue
                    ) /
                    (
                        maxValue -
                        minValue
                    )
                );


            context.beginPath();


            context.arc(
                x,
                y,
                2.5,
                0,
                Math.PI * 2
            );


            context.fillStyle =
                "#6ea8ff";

            context.fill();
        }
    );


    // ==================================================
    // AXIS LABEL
    // ==================================================

    context.fillStyle =
        "#8fa4bd";

    context.font =
        "10px sans-serif";

    context.textAlign =
        "center";


    context.fillText(
        "Optimization Iteration",
        width / 2,
        height - 12
    );
}


// ======================================================
// FORMAT NUMBER
// ======================================================

function formatNumber(value) {

    const number =
        Number(value);


    if (
        !Number.isFinite(number)
    ) {

        return "—";
    }


    if (
        Math.abs(number) <
        1e-8
    ) {

        return "0.000000";
    }


    if (
        Math.abs(number) <
        0.001 ||
        Math.abs(number) >=
        100000
    ) {

        return number.toExponential(
            4
        );
    }


    return number.toFixed(
        6
    );
}


// ======================================================
// FORMAT POSITION
// ======================================================

function formatPosition(
    position
) {

    if (
        !Array.isArray(position)
    ) {

        return "—";
    }


    return (
        "[" +
        position
            .map(
                value => {

                    const number =
                        Number(
                            value
                        );

                    return Number.isFinite(
                        number
                    )
                        ? number.toFixed(4)
                        : "—";
                }
            )
            .join(", ") +
        "]"
    );
}


// ======================================================
// ESCAPE HTML
// ======================================================

function escapeHtml(
    value
) {

    return String(
        value
    )
        .replace(
            /&/g,
            "&amp;"
        )
        .replace(
            /</g,
            "&lt;"
        )
        .replace(
            />/g,
            "&gt;"
        )
        .replace(
            /"/g,
            "&quot;"
        )
        .replace(
            /'/g,
            "&#039;"
        );
}


// ======================================================
// SLEEP
// ======================================================

function sleep(
    milliseconds
) {

    return new Promise(
        resolve =>
            setTimeout(
                resolve,
                milliseconds
            )
    );
}