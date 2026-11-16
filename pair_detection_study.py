"""Compare pair detection under an equal wall-clock cap on two 100D objectives."""
import argparse
from contextlib import redirect_stdout
import os
from pathlib import Path
from unittest.mock import patch

from optimizer_study import run, write_csv
from backend import agent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--seeds', nargs='+', type=int, default=[7, 41, 87])
    options = parser.parse_args()
    original = agent.additive_components

    def ignore_pairs(objective, dimensions, *, pairs=False):
        return None if pairs else original(objective, dimensions)

    rows = []
    options.output.parent.mkdir(parents=True, exist_ok=True)
    with open(os.devnull, 'w') as quiet:
        for name in ('rotated_rastrigin', 'coupled_quadratic'):
            seeds = options.seeds if name == 'rotated_rastrigin' else options.seeds[:1]
            for seed in seeds:
                for enabled in (True, False):
                    with patch.object(agent, 'additive_components', original if enabled else ignore_pairs):
                        with redirect_stdout(quiet):
                            row = run(name, 100, seed, 'adaptive_uniform', 100000, 10, 10, 3)
                    rows.append(dict(pair_detection=enabled, **row))
                    write_csv(options.output, rows)
                    print(name, seed, enabled, row['error'], row['termination'], flush=True)


if __name__ == '__main__':
    main()
