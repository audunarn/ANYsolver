# FE solver verification and quality control

This is the maintained verification guide for `anysolver`. Source code and
tests are authoritative; generated reports are evidence for the commit and
environment recorded in them.

## Evidence hierarchy

Use evidence in this order:

1. Current source and tests at the reported Git commit.
2. A fresh full `pytest` run.
3. The analytical/convergence/patch/support/performance QC suite.
4. `scripts/run_fe_verification.py`, which records commands, dependencies,
   warnings, return codes, and family reports.
5. Manifest-driven release gates and the production capability matrix.
6. Frozen local baselines.
7. Executed external-solver reports with solver identity, parsed observables,
   and tolerance-controlled comparisons.

Generated CalculiX-style input decks without matching executed results are
reproducible handoff artifacts, not numerical validation.

## Current 0.2 verification policy

Version 0.2 delegates material behavior, neutral meshing, and interchange
syntax to ANYmaterial, ANYmesher, and ANYfileio. A qualifying ecosystem run
therefore installs those sibling packages, runs their own tests, and then runs
the ANYsolver suite and ecosystem-wiring tests. Compatibility tests must cover
both the historical ANYsolver imports and the canonical package imports.

Pass counts and timings are deliberately not embedded here: they become stale
as tests move to their owning repositories. The generated report under
`reports/verification/` is the evidence for a particular commit. Historical
release evidence remains available in Git history and `CHANGELOG.md`.

## Commands

Run from the repository root.

```powershell
python -m pytest tests -q -p no:cacheprovider
python run_qc.py --no-save
python scripts/run_fe_verification.py --output-dir reports/verification
```

The comprehensive runner covers imports, focused FE tests, full pytest, QC,
baseline generation/comparison, benchmarks, element/member qualification,
modal/mass and buckling validity, plasticity, recovery/resource policy,
capacity workflow, external-reference artifacts, manifest gates, and
mesh/load/boundary-condition verification.

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
`ANYSOLVER_CALCULIX_EXECUTABLE`. Each case runs in an isolated directory. An
executed case passes only when the process succeeds, recognized results are
parsed, and every declared comparison meets tolerance.

## Release-scope artifacts

```powershell
python scripts/run_beam_shell_verification.py `
  --output reports/beam_shell_verification/beam_shell_verification_report.json `
  --markdown reports/beam_shell_verification/beam_shell_verification_report.md `
  --external-reference-report reports/external_references/external_reference_report.json

python scripts/write_production_readiness.py `
  --output-dir reports/production_readiness/current
```

The release manifest consumes the canonical artifacts under
`reports/beam_shell_verification/`, `reports/production_readiness/current/`,
`reports/verification/`, and `reports/external_references/`. Do not replace a
valid executed external report with a deck-only artifact.

## Interpreting results

- `PASS` means the implemented metric met its stated acceptance criterion.
- `XFAIL` records a known unsupported feature, unavailable reference data, or
  external execution still required; it is not a pass.
- External `not_executed` means inputs were generated but no numerical
  comparison was performed.
- A generated report applies only to its recorded commit, dependencies,
  options, and environment.
- Performance values are machine-dependent. Correctness equivalence and
  fallback behavior are gates; a historical speedup number is not.
- Production qualification is narrower than the union of callable APIs. See
  [`README.md`](../README.md) and the generated capability matrix.

Historical numbered or ad-hoc verification directories are not maintained
documentation; rerun the appropriate canonical command instead.
