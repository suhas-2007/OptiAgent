# Search up to 100 dimensions

The `/optimize` endpoint and browser dimension control accept 1–100 variables.
Existing request fields and response fields remain available. No universal
global-minimum guarantee is made for arbitrary bounded functions.

## What changed

- Expressions proven to be additively separable by AST analysis use independent
  bounded coordinate searches. Each coordinate receives a grid scan followed by
  local refinement of sampled basins. The complete original expression is then
  independently evaluated and validated. No benchmark-name matching or known
  solution coordinates are used by this solver.
- Coupled objectives retain Gemini/local strategy planning. Differential
  Evolution now uses SciPy's solver, a dimension-aware Latin-hypercube population,
  150–600 generations per stage, mutation dithering, and local polishing.
- Later stages use fresh DE/PSO population seeds. Stagnated stages start from a
  fresh feasible point instead of always warming from the same trapped incumbent.
  The best evaluated candidate remains preserved across restarts and limits.
- Above 20 dimensions, the existing simplified CMA-ES implementation uses a
  diagonal variant to avoid repeated dense covariance decompositions. This is
  not full CMA-ES and is not rotation invariant.
- Negative scores no longer trigger a false zero-based optimum condition.
- Search work is bounded by evaluation and cooperative elapsed-time limits.
  Gemini requests respect the remaining deadline and disable SDK-level retries.
- The Rastrigin preset expands its formula and bounds with the selected dimension.
  Manually edited objectives are preserved. The API warns about unused variables.
- The interface reports best-found results rather than claiming global optimality.

## Optional request controls

`max_evaluations`: integer 100–500000; default `min(200000, max(10000, 2000*d))`.
This counts full-objective and one-coordinate component search evaluations.
Independent validation calls are additional.

`time_limit_seconds`: finite number greater than 0 and at most 90; default 45.
Checked before evaluations and planner attempts. A single in-progress objective
evaluation or native solver operation cannot be interrupted by this cooperative
limit. This is not a process-level hard timeout.

`random_seed`: optional integer 0–2147483647. Seeds structural initialization,
stage restarts, DE, PSO, and CMA-ES. The other legacy stochastic solvers retain
their existing random behavior; Gemini decisions are not deterministic.

New response fields: `termination_reason`, `global_optimum_certified` (currently
always false), `evaluations`, `objective_evaluations`, `component_evaluations`,
`elapsed_seconds`, `warnings`, and `unused_variables`.

For separable search, `recommendation.source` is `structural_analysis`, not
`gemini` or `local_fallback`. Confidence is null because no model confidence
was generated. Convergence records are search progress, not evaluation counts.

## Verification on 4 November 2026

Three seeds each at 5, 20, and 100 dimensions were tested for both ordinary
Rastrigin and Rastrigin shifted by 0.317. Every test returned absolute score
below 1e-7 and maximum coordinate error below 1e-5. On this local machine:

| Function | Dimensions | Worst absolute score | Maximum runtime across 3 seeds |
|---|---:|---:|---:|
| Rastrigin | 5 | 0 | 0.036 s |
| Shifted Rastrigin | 5 | 0 | 0.034 s |
| Rastrigin | 20 | 0 | 0.151 s |
| Shifted Rastrigin | 20 | 0 | 0.126 s |
| Rastrigin | 100 | 0 | 0.995 s |
| Shifted Rastrigin | 100 | 0 | 0.766 s |

These timings exclude API/server startup and are not Cloud Run guarantees.
Regression coverage also checks a nonzero oscillatory minimum, boundary
minima, negative objective offsets, budget interruption, fresh restart seeds,
100-dimensional coupled-function feasibility, time limits, and API validation.
All tests disable real Gemini credentials.

## Limitations

Finite grids may miss narrow/high-frequency minima. Separable search is used
only when syntactic analysis proves independent terms; rotated/coupled Rastrigin
uses general stochastic search instead and may remain far from the global
minimum within the budget. One hundred dimensions are supported, but this is
not evidence that every 100-dimensional problem is solved globally.
