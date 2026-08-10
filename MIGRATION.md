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

## 0.2 extraction boundary

Version 0.2 removes the in-repository copies of material, neutral meshing, and
file-format implementations. Their canonical homes are now:

| Former ANYsolver surface | Canonical implementation |
| --- | --- |
| `anysolver.materials`, material curves | `anymaterial` |
| neutral parts of `anysolver.mesh_gen` | `anymesher` |
| SESAM records/documents/SIF and CalculiX readers/writer | `anyfileio` |

The old ANYsolver imports remain as thin compatibility facades through the
0.2.x line. Solver-owned behavior stays here: FEModel construction, exact MPC
constraints, support-label interpretation, CalculiX execution/provenance and
comparison evaluation. The extraction provenance and import replacements are
recorded here; each extracted package carries its own detailed migration note
and parity tests.

## Included

- Numerical model, element, assembly, linear, modal, buckling, nonlinear, continuation, dynamic, contact, damage, recovery, and validation modules.
- Generated-geometry and headless runtime analysis facades.
- Neutral SESAM-to-`FEModel` adapters and 0.2 compatibility imports over
  `ANYfileio`; SESAM syntax, documents, SIF parsing, and writing live in that
  package.
- FE-only tests, deterministic baseline, benchmarks, qualification scripts, and current solver documentation.

## Excluded

- PULS, machine-learning, training-data, and predictor artifacts.
- Generated reports and quality-control output directories.
- Python bytecode, IDE files, historical result dumps, and obsolete standalone cylinder/demo prototypes.
