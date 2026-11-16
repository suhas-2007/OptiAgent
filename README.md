# OptiAgent

OptiAgent searches for a minimum of a mathematical expression within bounds. It
can use up to 100 variables and records the score, coordinates, evaluation
counts, and strategy used in each stage.

[Open the dashboard](https://optiagent-frontend-272474227005.asia-south1.run.app/) · [API health](https://optiagent-272474227005.asia-south1.run.app/health)

## Why this project exists

An optimizer that works well on a smooth bowl can get stuck on a function with
many local minima. OptiAgent lets you define the problem once and inspect how
the search responds to its structure and to stalled progress. The central
research question is whether that workflow reaches better results than a
fixed optimizer under a comparable budget.

## Try a function

1. Choose a benchmark or enter a formula using `x1`, `x2`, and so on. Use
   `**` for powers and `*` for multiplication.
2. Set one lower and upper bound per variable. For a first run, choose **Beale**
   at two dimensions with bounds of `[-4.5, 4.5]`. Its minimum is `0` at
   `[3, 0.5]`.
3. Choose **Minimize** or **Maximize**, then run the search. Review the best
   point, stage history, and stopping reason.
   Use **Download run data** to save the settings and results as JSON.

Enter the original formula in either mode. The dashboard and JSON export
show scores in the original formula's units.

The parser accepts arithmetic, parentheses, and `sin`, `cos`, `tan`, `exp`,
`sqrt`, `log`, and `abs`. It recognizes the constants `pi` and `e`. Bounds
must be finite and increasing. Choose bounds compatible with the function's
domain, such as positive inputs to `log`.

| Presets | Dimensions |
| --- | --- |
| Sphere, Rastrigin, Ackley, Shifted Quadratic, Trigonometric | 1–100 |
| Rosenbrock | 2–100 |
| Beale, Booth, Himmelblau | Standard at 2D. Other dimensions use sums of independent 2D copies, with a squared term for an extra variable. |

## How the search works

The API parses the formula into a restricted expression tree. If the formula
is a sum of independent terms, OptiAgent searches the individual coordinates
or disjoint variable pairs and then evaluates the assembled point with the
original formula. For example, `(x1+x2)**2 + (x3-x4)**2` has two independent
pairs. Adding a term involving `x2` and `x3` sends it through the general search.

For objectives with more widely interacting variables, the planner chooses a
numerical optimizer. Gemini can make that choice when configured. The local
planner is also available. Stages share an evaluation budget. When progress
stalls, the general search can restart and switch optimizers. The optional
**Diverse** restart samples points across the bounds and near the incumbent.
**Uniform** is the default.

The validator checks the candidate's bounds and recalculates its score. The
result is the best verified point found within the budget. The search can miss
a better point elsewhere inside the bounds.

### What happens during a run

```text
Browser form
    ↓
Flask API validates the expression and bounds
    ↓
Check for independent coordinates or pairs
    ↓
Search components, or use local refinement and a selected optimizer
    ↓
Recalculate the best score and check bounds
    ↓
Record the stage, then continue until a run limit is reached
    ↓
Return results and convergence history to the browser
```

The registry contains Differential Evolution, CMA-ES, Particle Swarm
Optimization, Genetic Algorithm, Simulated Annealing, Hill Climbing, and
Nelder-Mead. Local refinement can use expression derivatives where supported.
The dashboard shows the returned stage records after the request completes.

### Search settings

| Setting | What it controls |
| --- | --- |
| Max stages | Up to 50 search stages. A run may stop earlier. |
| Restart patience | Consecutive stages without meaningful improvement before a restart in the general search. |
| Evaluation limit | Total search calls. Component and full-objective calls are reported separately. |
| Time limit | Up to 90 seconds of search, checked cooperatively. |
| Random seed | Repeats comparable local-planner runs when the evaluation budget determines the stop. |
| Restart sampling | Uniform or Diverse sampling for restarts in the general search. |

## Run locally

Use Python 3.11 or newer.

```sh
python -m pip install -r requirements.txt
python -m flask --app backend.api run --port 5000
```

In a second terminal, serve the frontend and open
`http://127.0.0.1:8000`.

```sh
python -m http.server 8000 --directory frontend
```

The local planner works without credentials. To enable Gemini locally, copy
`.env.example` to `.env` and set `GEMINI_API_KEY`.

## API example

Send this JSON to `POST /optimize` on the backend at
`http://127.0.0.1:5000`.

```json
{
  "objective": "(x1-3)**2 + (x2-0.5)**2",
  "dimensions": 2,
  "direction": "minimize",
  "bounds": [[-5, 5], [-5, 5]],
  "max_stages": 5,
  "max_evaluations": 4000,
  "planner_mode": "local",
  "random_seed": 7
}
```

The response includes `best_position`, `best_score`, `stage_history`,
`settings`, and `termination_reason`.

## Where to read the code

| Path | Purpose |
| --- | --- |
| [frontend/](frontend/) | HTML, CSS, and JavaScript for configuration, convergence, and export. |
| [backend/api.py](backend/api.py) | Flask routes, request validation, and JSON responses. |
| [backend/function_parser.py](backend/function_parser.py) | Restricted evaluation of mathematical expressions. |
| [backend/search.py](backend/search.py) | Evaluation accounting and search over independent coordinates or pairs. |
| [backend/agent.py](backend/agent.py) | Stage loop, planner decisions, restarts, and result validation. |
| [backend/optimizer_registry.py](backend/optimizer_registry.py) | Creates the numerical optimizer selected for a stage. |
| [optimizer_study.py](optimizer_study.py) | Runs the seeded comparison and writes CSV summaries. |

The frontend uses plain browser APIs. Flask handles requests, NumPy stores
search vectors, SciPy provides numerical solvers, and Gunicorn serves the
deployed API. Gemini is optional.

## Reproduce the benchmarks

```sh
python -m pytest tests -q
python optimizer_study.py --output study-results --budget 4000
```

The study compares both restart modes with standalone Differential Evolution
and OptiAgent's CMA-ES. Use the local planner and a recorded seed when comparing
runs. Keep bounds, software versions, and evaluation budgets fixed.

[Study protocol](OPTIMIZER_STUDY.md) · [Search settings and limitations](SCALABLE_SEARCH.md)

## Results

The original comparison ran 180 trials across five functions, three dimensions
(2D, 20D, and 100D), and three seeds per method. A run passed if its score
was within `1e-6` of the known minimum. Each run had a cap of 4,000 search
calls and five stages for the adaptive methods.

| Method | Runs that reached the target |
| --- | ---: |
| OptiAgent with Uniform restart | 39/45 |
| OptiAgent with Diverse restart | 39/45 |
| Standalone Differential Evolution | 15/45 |
| Standalone OptiAgent CMA-ES | 20/45 |

The two restart modes tied on target hits. The adaptive workflows also use
local refinement and can search independent terms separately, so this table
compares whole workflows. These counts predate the independent-pair search
and describe that earlier version of OptiAgent.

### Follow-up at 100 dimensions

On shifted, pairwise-rotated Rastrigin, both original restart modes had a
median error of about `49.75` from the known minimum of `0`. After adding
independent-pair search, three local runs with seeds 7, 41, and 87 finished
10 stages within a 100,000-call cap. Their errors ranged from `1.78e-15` to
`2.13e-14`. This follow-up used a larger budget and tested an objective
that splits into independent pairs.

### Equal-time check

Both modes used a 10-second limit and a 100,000-call cap at 100D. Lower error
is better. The known minimum for both objectives is zero.

| Objective | Seeds | Median error with pair detection | Median error without it |
| --- | ---: | ---: | ---: |
| Shifted, pairwise-rotated Rastrigin | 3 | `1.78e-14` | `49.75` |
| Fully coupled quadratic | 1 | `2.80e-26` | `2.80e-26` |

The Rastrigin errors with pair detection ranged from `1.07e-14` to `1.99`.
The quadratic is a control: both settings used the general optimizer.
These are local timings from a small set of runs. Two-variable component
calls cost less than full-objective calls. The CSV records both counts.

```sh
python pair_detection_study.py --output study-results/pair-detection.csv
```

## License

[MIT](LICENSE)
