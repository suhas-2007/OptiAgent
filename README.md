# OptiAgent

OptiAgent searches for a minimum of a mathematical expression within bounds. It
can use up to 100 variables and records the score, coordinates, evaluation
counts, and strategy used in each stage.

[Open the dashboard](https://optiagent-frontend-272474227005.asia-south1.run.app/) · [API health](https://optiagent-272474227005.asia-south1.run.app/health)

## Try a function

1. Choose a benchmark or enter a formula using `x1`, `x2`, and so on. Use
   `**` for powers and `*` for multiplication.
2. Set one lower and upper bound per variable. For a first run, choose **Beale**
   at two dimensions with bounds of `[-4.5, 4.5]`. Its minimum is `0` at
   `[3, 0.5]`.
3. Run the search and review the best point, stage history, and stopping reason.
   Use **Download run data** to save the settings and results as JSON.

To search for a maximum, minimize the negated formula. Keep the returned
coordinates and reverse the sign of the score.

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
  "bounds": [[-5, 5], [-5, 5]],
  "max_stages": 5,
  "max_evaluations": 4000,
  "planner_mode": "local",
  "random_seed": 7
}
```

The response includes `best_position`, `best_score`, `stage_history`,
`settings`, and `termination_reason`.

## Reproduce the benchmarks

```sh
python -m pytest tests -q
python optimizer_study.py --output study-results --budget 4000
```

The study compares both restart modes with standalone Differential Evolution
and OptiAgent's CMA-ES. Use the local planner and a recorded seed when comparing
runs. Keep bounds, software versions, and evaluation budgets fixed.

[Study protocol](OPTIMIZER_STUDY.md) · [Search settings and limitations](SCALABLE_SEARCH.md)

## License

[MIT](LICENSE)
