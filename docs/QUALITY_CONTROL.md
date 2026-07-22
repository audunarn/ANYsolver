# FE solver verification and quality control

This is the maintained verification guide for `anysolver`. It describes how
evidence is produced and records the latest checks performed against the
current workspace. The implementation and tests remain authoritative; report
files are dated snapshots.

## Evidence hierarchy

Use evidence in this order:

1. Current source and tests at the reported Git commit.
2. A fresh full `pytest` run.
3. The 18-case analytical/convergence/patch/support/performance QC suite.
4. `scripts/run_fe_verification.py`, which records commands, dependencies,
   warnings, return codes, and family reports in JSON and Markdown.
5. The manifest-driven release gates and generated production capability
   matrix.
6. Frozen local baselines and executed external-solver comparisons.

Generated CalculiX-style input decks without matching executed results are
reproducible handoff artifacts, not numerical validation.

## Current checked status

Workspace audit on 2026-07-22 at commit `0d98e40`:

- `pytest --collect-only`: 418 test cases collected;
- full `pytest`: 418/418 passed in 99.63 s;
- `python run_qc.py --no-save`: 18/18 passed;
- focused latest-development regression set (SESAM, corotational, arc length,
  nonlinear impact, and quadratic-beam nonlinear response): 62/62 passed;
- comprehensive `scripts/run_fe_verification.py`: 18/18 command families
  passed, including the manifest-driven beam-shell release gate.

The corresponding canonical report is
`reports/verification/fe_verification_report.md`. Future cleanup or release
runs must replace this dated evidence rather than infer status from it.

## Commands

Run from the repository root.

### Full tests

```powershell
python -m pytest tests -q -p no:cacheprovider
```

### Analytical QC

```powershell
python run_qc.py --no-save
```

The QC suite contains 18 checks across analytical solutions, convergence,
patch behavior, boundary conditions, solver comparison, large-mesh smoke, and
ill-conditioning behavior.

### Solver-wide verification

```powershell
python scripts/run_fe_verification.py --output-dir reports/verification
```

The comprehensive runner covers imports, focused FE tests, full pytest, QC,
baseline generation/comparison, infrastructure benchmarks, S4 and element
qualification, beam/member validity, modal/mass and buckling validity,
plasticity/tangent qualification, recovery/resource policy, capacity workflow,
external-reference artifacts, beam-shell manifest gates, and mesh/load/BC
verification.

Use `--quick`, `--skip-full`, or a family flag only for development diagnosis.
A partial run must not replace full release evidence.

### Release-scope artifacts

```powershell
python scripts/run_beam_shell_verification.py `
  --output reports/beam_shell_verification/beam_shell_verification_report.json `
  --markdown reports/beam_shell_verification/beam_shell_verification_report.md

python scripts/write_production_readiness.py `
  --output-dir reports/production_readiness/current
```

The release manifest expects canonical artifacts in
`reports/beam_shell_verification/`, `reports/production_readiness/current/`,
`reports/verification_quick_current/`, and `reports/external_references/`.

## Coverage map

| Family | Principal evidence |
| --- | --- |
| Core algebra | DOF order, separated K/M/F/KG assembly, sparse checks, factorization caching, multi-RHS equivalence. |
| Constraints | Supports, prescribed values, multilevel/circular-MPC rejection, eccentric/interpolated coupling, reactions, free-free nullspace. |
| Shells | T3/T6/Q4/Q8/Q8R shapes, rigid modes, patch tests, pressure/mass/geometric stiffness, locking/distortion metrics, local/global stresses. |
| Beams | Linear/quadratic Timoshenko response, axes/orientation, torsion, consistent mass, Euler/Wagner buckling, nonlinear tangent, and fiber plasticity. |
| Modal/buckling | Constrained and free-free modes, point mass, sparse shift-invert, repeated roots, beam and shell reference loads. |
| Nonlinear capacity | DNV curves, layered shell plasticity, beam fibers, von Karman/corotational paths, load programs, displacement control, arc length, and imperfections. |
| Transient/contact | Newmark/HHT-alpha, pressure patches, energy/impulse checks, shell/beam sphere contact, event subdivision, nonlinear impact, damage/erosion. |
| Recovery/resources | Selected components, threaded deterministic recovery, history modes, memory estimation/limits, and provenance. |
| Workflows/interchange | Normalized generated geometry, capacity workflow, SESAM FEM round trip/import, transforms/orientation, and SIF load-case stress isolation. |
| Release scope | Stable verification IDs, PASS/XFAIL separation, production capability matrix, limitations, and evidence manifest. |

## Interpreting results

- `PASS` means the implemented metric met its stated acceptance criterion.
- `XFAIL` records a known unsupported feature, unavailable reference data, or
  external execution still required; it is not a pass.
- A generated report applies only to the commit, dependencies, options, and
  environment recorded in that report.
- Performance values are machine-dependent. Correctness equivalence and
  fallback behavior are gates; a historic speedup number is not.
- Production qualification is narrower than the union of callable APIs. See
  [`README.md`](README.md) and the generated capability matrix.

## Canonical report locations

- `reports/verification/`: comprehensive current verification run.
- `reports/beam_shell_verification/beam_shell_verification_report.*`: stable
  case-ID release gates.
- `reports/production_readiness/current/`: capability matrix and scope.
- `reports/verification_package/release_evidence_manifest.*`: expected release
  artifact inventory.

Historical numbered or ad-hoc verification directories should not be retained
as maintained documentation; rerun the appropriate canonical command instead.
