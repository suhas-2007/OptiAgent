# Comparing search strategies in OptiAgent

## How to explain the change

OptiAgent minimizes a mathematical expression inside bounds. It keeps the best
point it has evaluated. If a run goes several stages without meaningful
improvement, it changes strategy on the next stage and starts from a new point.

Open **Search settings** and choose **Restart sampling**. **Uniform** starts from
one random point. **Diverse** tries up to 16 candidates, with some spread across
the bounds and some near the best point so far. It starts from the lowest-scoring
candidate and keeps the previous best as a safety net. Every trial counts toward
the same budget. The stage log shows how many candidates it tried. This choice
applies to objectives with interacting variables. Independent coordinates keep
their existing search.

## Reproduce the comparison

From the project root with the requirements installed:

```text
python optimizer_study.py --output study-results --budget 4000
```

The script compares two versions of OptiAgent, standalone Differential
Evolution, and the CMA-ES implementation bundled with OptiAgent. Above 20
dimensions that CMA-ES implementation uses diagonal covariance. The adaptive
versions also use local refinement and can exploit independent coordinates.
The comparison measures the full workflows. The uniform-versus-diverse
comparison isolates the restart policy.

The default matrix uses three seeds at 2, 20, and 100 dimensions on Sphere,
Rosenbrock, Rastrigin, Beale, and shifted, pairwise-rotated Rastrigin.
Beale beyond 2D is a sum of 2D copies. All five objectives have a known minimum
score of zero within the bounds. The study uses the local planner and restart
patience of one to exercise restarts. Each solver has the same search-call cap
and a time limit. Some runs use fewer calls if they stop early.

Read `summary.csv` for median error, success rate, and median calls to reach
`1e-6` among successful runs. `runs.csv` has one row per experiment with the
seed, settings, stop reason, runtime, and call counts. A component evaluation
can be much cheaper than evaluating the whole objective. Read the full-objective
and component counts alongside totals. Score validation and analytic gradient
calls are outside the objective-call cap. Treat runs stopped by time as
time-limited results.

For a larger study, pass more seeds and report the spread as well as the
median. The rotated test mixes pairs of variables. Performance on it does not
establish performance on arbitrary high-dimensional objectives.
