
# OptiAgent

## Autonomous Dynamic Optimization

OptiAgent is an **agentic optimization system** that automatically selects, executes, validates, monitors, and adapts numerical optimization strategies for user-defined mathematical objective functions.

Instead of requiring the user to manually select an optimization algorithm, OptiAgent uses **Gemini AI with Automatic Function Calling (AFC)** to make strategic optimization decisions.

---

# 🚀 Overview

Traditional optimization systems usually require the user to decide which algorithm to use.

For example:

- Genetic Algorithm
- Particle Swarm Optimization
- Differential Evolution
- Simulated Annealing
- Hill Climbing
- CMA-ES
- Nelder-Mead

Choosing the right algorithm can depend on the characteristics of the optimization problem.

OptiAgent addresses this by introducing an **AI-driven decision layer**.

The user provides:

1. Objective function
2. Number of dimensions
3. Bounds for each variable

OptiAgent then autonomously determines an optimization strategy and executes the optimization process.

---

# 🧠 Agentic Optimization Workflow

```text
                    USER PROBLEM
                         |
                         v
                Function Parser
                         |
                         v
                    AI Planner
                         |
                         v
                  Gemini AI + AFC
                         |
                         v
                Strategy Selection
                         |
                         v
                Optimizer Registry
                         |
                         v
                 Selected Optimizer
                         |
                         v
                Numerical Optimization
                         |
                         v
                Solution Validation
                         |
                         v
              Convergence Monitoring
                         |
                         v
                 Stagnation Detection
                         |
                    +----+----+
                    |         |
                Improving   Stagnating
                    |         |
                    v         v
                 Continue   Adaptation
                              |
                              v
                         Gemini AFC
                              |
                              v
                      New Strategy
                              |
                              v
                       Next Stage

The agent follows the cycle:

Observe
   ↓
Reason
   ↓
Decide
   ↓
Act
   ↓
Validate
   ↓
Monitor
   ↓
Adapt
   ↓
Repeat


---

✨ Key Features

Dynamic mathematical objective functions

Safe mathematical expression parsing

Multiple optimization algorithms

AI-based optimization strategy selection

Gemini Automatic Function Calling (AFC)

Optimizer registry architecture

Independent solution validation

Convergence monitoring

Stagnation detection

Adaptive optimization strategy

Multi-stage optimization

REST API

Web frontend

Optimization history

Convergence history

Global best solution tracking



---

🔬 Supported Optimization Algorithms

OptiAgent currently supports:

1. Particle Swarm Optimization

PSO is a population-based optimization technique inspired by swarm behavior.

2. Differential Evolution

Differential Evolution is a population-based evolutionary optimization algorithm that is effective for continuous optimization.

3. Genetic Algorithm

Genetic Algorithm uses evolutionary concepts such as:

Selection

Crossover

Mutation


4. Simulated Annealing

Simulated Annealing uses probabilistic exploration to escape local minima.

5. Hill Climbing

Hill Climbing iteratively searches for better neighboring solutions.

6. CMA-ES

Covariance Matrix Adaptation Evolution Strategy is designed for difficult continuous optimization problems.

7. Nelder-Mead

Nelder-Mead is a derivative-free optimization method based on a simplex.


---

🎯 Example Optimization Problem

Example objective function:

x1**2 + x2**2

Dimensions:

2

Bounds:

x1 ∈ [-10, 10]
x2 ∈ [-10, 10]

The theoretical optimum is:

x1 = 0
x2 = 0

with:

f(x1, x2) = 0

OptiAgent should therefore search for a solution close to:

[0, 0]


---

🧮 Mathematical Expression Support

OptiAgent provides a restricted mathematical expression parser.

Example:

x1**2 + x2**2

(x1 - 3)**2 + (x2 + 2)**2

sin(x1)**2 + cos(x2)**2

sqrt(x1**2 + x2**2)

Supported mathematical functions include:

sin()
cos()
tan()
exp()
sqrt()
log()
abs()

Supported constants:

pi
e

Variables follow the format:

x1
x2
x3
...


---

🔐 Safe Expression Evaluation

OptiAgent does not directly execute arbitrary Python code supplied by the user.

Instead, mathematical expressions are parsed using Python's Abstract Syntax Tree (AST) system.

Only approved:

Variables

Constants

Operators

Mathematical functions


are allowed.

This prevents arbitrary Python expressions from being executed through the objective-function input.


---

🤖 AI Strategic Decision Making

The AI planner acts as the strategic layer of OptiAgent.

Gemini receives information about:

Objective function

Number of dimensions

Variable bounds

Available optimization algorithms

Current optimization strategy

Optimization status

Validation information

Convergence behavior


Gemini then recommends an optimization strategy.

The selected strategy is passed to the optimizer registry.


---

🔧 Automatic Function Calling

OptiAgent uses Gemini Automatic Function Calling (AFC) to allow the AI planner to select an optimization algorithm through a defined tool interface.

Conceptually:

Gemini
   |
   | AFC
   v
select_optimizer()
   |
   v
Optimizer Registry
   |
   v
Selected Algorithm

This creates an agentic decision-making layer instead of simply asking an AI model to return plain text.


---

🔄 Adaptive Optimization

OptiAgent does not necessarily use a single optimizer for the entire problem.

The system monitors optimization progress.

If the optimization continues to improve:

Continue Current Strategy

If stagnation is detected:

Stagnation
    ↓
Adaptation Engine
    ↓
Gemini AFC
    ↓
New Strategy
    ↓
Next Optimization Stage

This allows OptiAgent to dynamically change strategies during optimization.


---

✅ Solution Validation

The optimization result is independently validated before being accepted.

The validator checks factors such as:

Solution structure

Number of dimensions

Variable bounds

Objective score

Actual objective-function evaluation

Solution reliability


The reported optimizer score is not blindly trusted.

The objective function is independently evaluated at the returned position.


---

📈 Convergence Monitoring

OptiAgent records optimization progress during execution.

For every optimization stage, convergence information can include:

Stage
Algorithm
Iteration
Score

This information can be used to understand how the optimization progressed.

The monitoring system also attempts to detect stagnation.


---

🏗️ System Architecture

+-----------------------+
|       Frontend        |
|      Web Interface    |
+-----------+-----------+
            |
            v
+-----------------------+
|       Flask API       |
|      REST Endpoint    |
+-----------+-----------+
            |
            v
+-----------------------+
|  Optimization Agent  |
+-----------+-----------+
            |
     +------+------+
     |             |
     v             v
 AI Planner    Optimizer
     |             |
     v             v
 Gemini AFC    Registry
                   |
          +--------+--------+
          |        |        |
          v        v        v
        PSO       DE       GA
          |
          +----------------+
                   |
                   v
            Solution Validator
                   |
                   v
            Convergence Monitor
                   |
                   v
            Adaptation Engine


---

📁 Project Structure

OptiAgent/
│
├── backend/
│   │
│   ├── adaptation.py
│   ├── agent.py
│   ├── ai_planner.py
│   ├── api.py
│   ├── benchmark.py
│   ├── candidate_selector.py
│   ├── cma_es.py
│   ├── differential_evolution.py
│   ├── function_parser.py
│   ├── genetic_algorithm.py
│   ├── hill_climbing.py
│   ├── main.py
│   ├── monitor.py
│   ├── nelder_mead.py
│   ├── optimizer.py
│   ├── optimizer_registry.py
│   ├── random_search.py
│   ├── simulated_annealing.py
│   └── solution_validator.py
│
├── data/
│
├── frontend/
│
├── models/
│
├── tests/
│
├── .env
├── .gitignore
├── README.md
└── requirements.txt


---

⚙️ Requirements

The project requires:

Python 3.10+

Gemini API access

Flask

Flask-CORS

Google GenAI SDK

NumPy

SciPy

python-dotenv


Install dependencies using:

pip install -r requirements.txt


---

🔑 Environment Configuration

Create a .env file in the project root.

GEMINI_API_KEY=your_api_key_here

The API key should remain on the backend.

Do not expose the Gemini API key in frontend JavaScript.

Do not commit .env to GitHub.

The .gitignore file should contain:

.env
.venv/
__pycache__/
*.pyc


---

🚀 Running the Backend

From the project root:

.\.venv\Scripts\python.exe backend\api.py

The Flask API should start at:

http://127.0.0.1:5000

Expected output:

============================================================
                 OPTIAGENT API
============================================================

Server: http://127.0.0.1:5000


---

❤️ Health Check

After starting the API, open another PowerShell terminal.

Run:

Invoke-RestMethod http://127.0.0.1:5000/health

Expected response:

status
------
ok

This confirms that the API is running.


---

🌐 Running the Frontend

Open another terminal.

From the project root:

cd frontend
python -m http.server 5500

Then open:

http://127.0.0.1:5500

The frontend should display the API connection status.

For example:

API Online


---

🔌 REST API

Health Endpoint

GET /health

Example:

http://127.0.0.1:5000/health


---

Optimization Endpoint

POST /optimize

Example JSON request:

{
  "objective": "x1**2 + x2**2",
  "dimensions": 2,
  "bounds": [
    [-10, 10],
    [-10, 10]
  ],
  "max_stages": 5,
  "patience": 3
}


---

🧪 Testing the API

PowerShell example:

$body = @{
    objective = "x1**2 + x2**2"
    dimensions = 2
    bounds = @(
        ,@(-10,10)
        ,@(-10,10)
    )
    max_stages = 1
    patience = 3
} | ConvertTo-Json -Depth 10

Invoke-WebRequest `
    -Uri "http://127.0.0.1:5000/optimize" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body


---

🧪 Automated Tests

The project is designed to support automated testing for:

Mathematical expression parsing

Optimization algorithms

Solution validation

API behavior

Agent components


Tests can be executed with:

pytest


---

📊 Optimization Result

A successful optimization returns information such as:

Best Position
Best Score
Strategy History
Stage History
Convergence History

Example conceptual result:

{
  "best_position": [0.001, -0.002],
  "best_score": 0.000005,
  "strategy_history": [
    "Nelder-Mead"
  ]
}


---

🔁 Multi-Stage Optimization

OptiAgent supports multiple optimization stages.

Example:

Stage 1 → Differential Evolution
              ↓
        Stagnation detected
              ↓
Stage 2 → CMA-ES
              ↓
        Improvement
              ↓
Stage 3 → CMA-ES
              ↓
        Convergence

The actual strategy depends on the AI planner's decision and the observed optimization behavior.


---

🎯 Why OptiAgent Is Different

Traditional optimization software:

User
 ↓
Choose Algorithm
 ↓
Run Algorithm
 ↓
Result

OptiAgent:

User
 ↓
Problem
 ↓
AI reasons about strategy
 ↓
Algorithm selected
 ↓
Optimization
 ↓
Independent validation
 ↓
Monitoring
 ↓
Adaptation
 ↓
Potential strategy change
 ↓
Final solution

The key idea is that the system is not simply an optimizer.

It is an agentic optimization framework that combines:

AI Reasoning
+
Numerical Optimization
+
Validation
+
Monitoring
+
Adaptation


---

🌍 Potential Real-World Applications

The architecture can be extended to real-world optimization problems such as:

Smart Logistics

Optimize:

Delivery routes

Vehicle assignment

Travel distance

Delivery time

Fuel usage


Resource Allocation

Optimize:

Workforce allocation

Machine allocation

Budget allocation

Computing resources


Scheduling

Optimize:

Job scheduling

Employee scheduling

Machine scheduling

Task allocation


Engineering Optimization

Optimize:

Design parameters

Manufacturing parameters

Energy consumption

System performance


Operations Research

Optimize:

Cost

Time

Resource utilization

Capacity allocation



---

🔒 Security Considerations

The objective-function parser uses restricted AST evaluation instead of Python's unrestricted eval().

The Gemini API key is stored server-side through environment variables.

For production deployment, additional security should be added, including:

Authentication

Rate limiting

Request validation

HTTPS

Secure secret management

Production WSGI server

Logging and monitoring



---

☁️ Deployment

The current development configuration uses:

Frontend:
http://127.0.0.1:5500

Backend:
http://127.0.0.1:5000

These addresses are local to the development machine.

For public deployment, the frontend and backend should be hosted on publicly accessible infrastructure.

A production architecture can look like:

Internet
                    |
                    v
             Public Frontend
                    |
                    v
             Production API
                    |
          +---------+---------+
          |                   |
          v                   v
    OptiAgent Agent      Gemini API
          |
          v
    Optimization Engine

The Gemini API key must remain on the backend and should never be placed in the public frontend.


---

⚠️ Gemini API Availability

OptiAgent uses Gemini as an external AI planning service.

Gemini API availability can depend on:

Model availability

API quota

Rate limits

Project configuration

Service load


Temporary errors such as:

429 RESOURCE_EXHAUSTED
503 UNAVAILABLE
504 DEADLINE_EXCEEDED

may occur.

These are external service conditions and are separate from the numerical optimization algorithms themselves.


---

📌 Current Development Status

Completed

[x] Objective-function input

[x] Safe mathematical expression parser

[x] Dynamic dimensions

[x] Variable bounds

[x] Multiple optimization algorithms

[x] Optimizer abstraction

[x] Optimizer registry

[x] AI planner

[x] Gemini integration

[x] Gemini Automatic Function Calling

[x] Solution validation

[x] Convergence monitoring

[x] Stagnation detection

[x] Adaptation engine

[x] Multi-stage optimization

[x] Flask REST API

[x] Frontend API connection

[x] Basic optimization UI


Remaining / Improvements

[ ] Automated test suite

[ ] Production deployment

[ ] Benchmark dataset

[ ] Expanded documentation

[ ] Performance benchmarking

[ ] Production security

[ ] Advanced visualization

[ ] Real-world logistics optimization



---

🚧 Limitations

The current system is primarily designed for continuous numerical optimization.

Some real-world optimization problems require additional capabilities such as:

Discrete variables

Integer constraints

Equality constraints

Inequality constraints

Multiple objectives

Large-scale datasets

Real-time external data


These can be added in future versions.


---

🔮 Future Roadmap

Phase 1 — Core Optimization

Multiple optimization algorithms

AI strategy selection

Validation

Monitoring

Adaptation


Phase 2 — Visualization

Convergence graphs

Optimization landscape visualization

Strategy comparison

Performance dashboard


Phase 3 — Real-World Optimization

Vehicle routing

Delivery optimization

Scheduling

Resource allocation


Phase 4 — Production

Cloud deployment

Authentication

Database

Experiment history

API rate limiting

Production monitoring



---

👨‍💻 Development Philosophy

OptiAgent separates responsibilities into independent components.

AI Planner
    ↓
Strategic Decision

Optimizer
    ↓
Numerical Search

Validator
    ↓
Independent Verification

Monitor
    ↓
Progress Analysis

Adaptation Engine
    ↓
Strategy Adjustment

This separation makes the system easier to:

Test

Extend

Debug

Deploy

Replace individual components



---

📜 License

This project is intended for educational, research, experimentation, and demonstration purposes.

A production deployment should include an appropriate open-source or proprietary license depending on the intended use.


---

⭐ Project Summary

OptiAgent — Autonomous Dynamic Optimization

An agentic optimization framework where AI selects optimization strategies, numerical algorithms solve the mathematical problem, independent validation verifies the result, and monitoring plus adaptation allow the system to change strategy when optimization stagnates.

AI
+
Optimization
+
Validation
+
Monitoring
+
Adaptation
=
OptiAgent

