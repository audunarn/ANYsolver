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
6. Frozen local baselines.
7. Executed external-solver reports with solver identity, parsed observables,
   and tolerance-controlled comparisons.

Generated CalculiX-style input decks without matching executed results are
reproducible handoff artifacts, not numerical validation.

## Recorded 0.1.3 release-candidate evidence

Checks on 2026-07-28 against the finalized `0.1.3` release-candidate source:

- independent full `pytest`: 504/504 passed in 214.26 s;
- comprehensive-run focused FE tests: 156/156 passed;
- analytical quality control: 18/18 checks passed and 4/4 demonstration
  cases completed;
- comprehensive `scripts/run_fe_verification.py` with explicit CalculiX
  execution: 18/18 command families passed;
- frozen-baseline generation/comparison: passed without failures or warnings;
- beam/shell verification ledger: 128 `PASS` and the existing two expected
  `XFAIL` cases;
- three real CalculiX 2.22 comparisons passed using
  `C:\Program Files\FreeCAD 1.1\bin\ccx.exe` (SHA-256
  `59b8fbc2eb90eec60e5e4c80014baf0f1cb6c892288ad8ba24f5e5235feb2774`);
- wheel and source distribution build plus `twine check`: passed;
- isolated wheel installation reported version `0.1.3` from the temporary
  environment, exposed the public runtime-analysis selection API, and
  completed representative flat-panel, closed-cylinder, and nonlinear
  follower-pressure solves without either source repository on `PYTHONPATH`.

The `0.1.3` release is required for the completed generated-geometry runtime
bridge and its ANYstructure integration. PyPI `0.1.2` is immutable and does not
contain the follower-pressure runtime field or
`resolve_runtime_analysis()`.

## Recorded 0.1.2 release-candidate evidence

Checks on 2026-07-28 against the `0.1.2` release-candidate source:

- full `pytest`: 495/495 passed (209.00 s against the finalized versioned
  source);
- focused FE verification set: 156/156 passed;
- `python run_qc.py --test-cases --no-save`: 18/18 QC checks and 4/4
  demonstration cases passed;
- comprehensive `scripts/run_fe_verification.py` with explicit CalculiX
  execution: 18/18 command families passed;
- frozen-baseline comparison: passed with no failures or warnings;
- focused follower-pressure/corotational mechanics tests: 72/72 passed;
- focused unified recovery/runtime qualification groups passed, including an
  actual low-yield plastic-shell solve recovered from committed material
  history;
- residual shell/beam field initialization, zero-load equilibration,
  field/restart provenance, exact stage-boundary commits, persistent
  multi-stage plastic history, and displacement-control rollback passed with
  acceleration both enabled and disabled;
- analytical plane-stress tangent qualification passed across elastic,
  yielding, hardening, unloading, and stable near-singular paths. Maximum
  analytical/oracle relative error was `1.34e-9`; the warmed 512-point
  material batch was `2.65x` faster than the numerical derivative in this
  run;
- the analytical and numerical tangents both required 15 total Newton
  iterations in the eight-element plastic-shell benchmark. Relative
  displacement, reaction, and committed-state differences were `1.61e-15`,
  `4.50e-14`, and `1.16e-14`;
- an executable CalculiX 2.22 run passed all three declared reference cases:
  plate center displacement and maximum von Mises errors were 3.00% and
  3.32%, plate force imbalance was 0.00184 N, column buckling-factor error was
  0.799%, and cylinder radial-displacement and maximum von Mises errors were
  4.38% and 4.27%;
- the four-command external-evidence/manifest integration run passed and
  retained the 128 `PASS` / two expected `XFAIL`
  beam/shell result.
- stale non-executed external-report schemas are replaced deterministically;
  invalid executed evidence is preserved and fails closed. The focused
  external/VVR regression group passed 14/14;
- wheel and source distribution build plus `twine check`: passed. The wheel
  imported from an isolated target with both runtime and package metadata at
  `0.1.2`, completed representative flat-panel and cylinder solves, completed
  shell initial-field equilibration, and retained a maximum analytical/oracle
  tangent error of `1.34e-9`.

This evidence qualified the then-current `0.1.2` source snapshot. Distribution
metadata, archive contents, and isolated-wheel execution are checked separately
when the release artifacts are built; publishing remains a distinct, manually
approved action.

The later generated-geometry runtime bridge follow-up (shear/torsion routing,
follower-pressure guards, corotational arc length, and committed-history
prestress resultants) is not represented by the numbered snapshot above until
the release verification and distribution checks are rerun against the final
source.

## Recorded 0.1.1 release evidence

Workspace audit on 2026-07-25 against the `0.1.1` release-candidate working
tree based on tagged commit `6623291` (Windows 11, Python 3.13.9):

- full `pytest`: 417/417 passed (183.18 s in the canonical runner);
- focused FE verification set: 151/151 passed;
- `python run_qc.py --no-save`: 18/18 passed;
- comprehensive `scripts/run_fe_verification.py`: 18/18 command families
  passed;
- manifest-driven beam/shell verification: 128 `PASS` and the two existing
  expected `XFAIL` cases (`COUP-011` nonmatching coupling and `MAT-004`
  kinematic hardening);
- frozen-baseline comparison: passed with no failures or warnings;
- wheel and source distribution build plus `twine check`: passed;
- the wheel imported from an isolated target environment and completed
  representative production flat-panel, cylinder, and adaptively refined B3
  cylinder solves.

The `0.1.1` external-reference family generated three valid CalculiX handoff
decks. It did not execute CalculiX, so the historical `0.1.1` evidence makes no
external numerical-agreement claim. The executed comparison listed in the
`0.1.2` section above belongs to the later release-candidate sweep.

The comprehensive test, QC, manifest, baseline, benchmark, and
external-artifact results are recorded in
`reports/verification/fe_verification_report.md`. The distribution build,
`twine check`, isolated-wheel import, and wheel-only representative solves
listed above were separately performed release checks; they are not embedded
in that canonical runner report. Future cleanup or release runs must replace
this dated evidence rather than infer status from it.

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

To execute the external reference family as part of the comprehensive run:

```powershell
python scripts/run_fe_verification.py `
  --execute-calculix `
  --calculix "C:\path\to\ccx.exe" `
  --output-dir reports/verification
```

The executable can instead be discovered from `PATH` or
`ANYSOLVER_CALCULIX_EXECUTABLE`. `--calculix-timeout` controls the per-case
limit, and repeatable `--calculix-arg` values support wrapper commands.

### External CalculiX references

Deck-only handoff:

```powershell
python scripts/run_external_references.py `
  --output reports/external_references/external_reference_report.json `
  --markdown reports/external_references/external_reference_report.md
```

Executed comparison:

```powershell
python scripts/run_external_references.py `
  --execute `
  --calculix "C:\path\to\ccx.exe" `
  --output reports/external_references/external_reference_report.json `
  --markdown reports/external_references/external_reference_report.md `
  --run-dir reports/external_references/runs
```

Each case runs in an isolated directory after stale result files are removed.
The report records the executable path, version probe and SHA-256, command,
timeout, return code, logs, parsed ASCII FRD/DAT fields, and every declared
comparison. Deck-only status is `not_executed`. Executed status is `passed`
only when CalculiX returns successfully, recognized results are parsed, and
all comparisons meet tolerance.

### Release-scope artifacts

```powershell
python scripts/run_beam_shell_verification.py `
  --output reports/beam_shell_verification/beam_shell_verification_report.json `
  --markdown reports/beam_shell_verification/beam_shell_verification_report.md `
  --external-reference-report reports/external_references/external_reference_report.json

python scripts/write_production_readiness.py `
  --output-dir reports/production_readiness/current

python scripts/run_fe_verification.py --quick `
  --output-dir reports/verification_quick_current
```

The release manifest expects canonical artifacts in
`reports/beam_shell_verification/`, `reports/production_readiness/current/`,
`reports/verification_quick_current/`, and `reports/external_references/`.
Passing the external report explicitly lets the manifest consume and preserve
executed evidence; it must not replace a valid executed report with a
deck-only artifact.

## Coverage map

| Family | Principal evidence |
| --- | --- |
| Core algebra | DOF order, separated K/M/F/KG assembly, sparse checks, factorization caching, multi-RHS equivalence. |
| Constraints | Supports, prescribed values, multilevel/circular-MPC rejection, eccentric/interpolated coupling, reactions, free-free nullspace. |
| Shells | T3/T6/Q4/Q8 shapes, rigid modes, patch tests, dead/current-area follower pressure, exact pressure-load tangent, Mindlin N/M/H initial-stress stiffness, locking/distortion metrics, and local/global stresses; Q8R remains explicitly experimental. |
| Beams | Linear and straight-sided quadratic Timoshenko response, axes/orientation, torsion, consistent mass, Euler/Wagner buckling, nonlinear tangent, and fiber plasticity. |
| Modal/buckling | Constrained and free-free modes, point mass, sparse shift-invert, repeated roots, beam and shell reference loads. |
| Nonlinear capacity | DNV curves, layered shell plasticity, beam fibers, von Karman/corotational paths, rotated/consistent corotational tangents, follower-pressure Newton and arc-length paths, load programs, displacement control, and imperfections. |
| Transient/contact | Newmark/HHT-alpha, pressure patches, energy/impulse checks, shell/beam sphere contact, event subdivision, nonlinear impact, damage/erosion. |
| Recovery/resources | Committed shell-layer/beam-fiber recovery, explicitly labelled elastic fallback, corotational objectivity, component provenance, guarded Q4/Q8 patch fits, discontinuity regions, selected components, deterministic threading, memory estimation/limits, and provenance. |
| Workflows/interchange | Normalized generated geometry; balanced axial/bending/shear/torsional runtime loads; guarded follower-pressure routing; corotational arc length; committed-history prestress with Gauss-point resultants and provenance; capacity workflow; SESAM FEM round trip/import; transforms/orientation; and SIF load-case stress isolation. |
| Release scope | Stable verification IDs, PASS/XFAIL separation, production capability matrix, limitations, and evidence manifest. |

## Interpreting results

- `PASS` means the implemented metric met its stated acceptance criterion.
- `XFAIL` records a known unsupported feature, unavailable reference data, or
  external execution still required; it is not a pass.
- External `not_executed` means inputs were generated but no numerical
  comparison was performed. It must never be presented as `PASS`.
- An external `passed` result is limited to the solver executable, deck,
  parsed quantities, tolerances, and provenance recorded in that report.
- A generated report applies only to the commit, dependencies, options, and
  environment recorded in that report.
- Performance values are machine-dependent. Correctness equivalence and
  fallback behavior are gates; a historic speedup number is not.
- Production qualification is narrower than the union of callable APIs. See
  [`README.md`](../README.md) and the generated capability matrix.

## Canonical report locations

- `reports/verification/`: comprehensive current verification run.
- `reports/beam_shell_verification/beam_shell_verification_report.*`: stable
  case-ID release gates.
- `reports/production_readiness/current/`: capability matrix and scope.
- `reports/verification_package/release_evidence_manifest.*`: expected release
  artifact inventory.

Historical numbered or ad-hoc verification directories should not be retained
as maintained documentation; rerun the appropriate canonical command instead.
