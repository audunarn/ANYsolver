# Migration to ANYsolver

ANYsolver is a curated snapshot, not a filtered-history import.

## Provenance

- Numerical solver source: `audunarn/ANYintelligent` starting at `96ec92e00e977415c5fed71eee39d1484f6dd068`, finalized at `9e4c59f` by the annotated tag `pre-anysolver-transfer-2026-07-22`.
- Headless runtime source: `audunarn/ANYstructure` at `738004fb1ac1cf033e71099e2a4057c5319ab878`.
- Target seed: `audunarn/ANYsolver` at `f9e80c7113be8b3aa217f36302eb075fe845459a`.

## Import changes

| Previous import | Replacement |
| --- | --- |
| `fe_solver` | `anysolver` |
| `anystruct.fe_solver_backend` | `anysolver` |
| `anystruct.fe_solver` | `anysolver.runtime` |
| `anystruct.fe_runtime_solver` | `anystruct.fem_integration` |

There is intentionally no `fe_solver` compatibility package.

## Included

- Numerical model, element, assembly, linear, modal, buckling, nonlinear, continuation, dynamic, contact, damage, recovery, and validation modules.
- Generated-geometry and headless runtime analysis facades.
- SESAM formatted FEM and SIF support.
- FE-only tests, deterministic baseline, benchmarks, qualification scripts, and current solver documentation.

## Excluded

- PULS, machine-learning, training-data, and predictor artifacts.
- Generated reports and quality-control output directories.
- Python bytecode, IDE files, historical result dumps, and obsolete standalone cylinder/demo prototypes.
