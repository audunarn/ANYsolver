# FE solver verification and quality control

This is the maintained verification guide for `anysolver`. Source code and
tests are authoritative; generated reports are evidence for the commit and
environment recorded in them.

## Evidence hierarchy

Use evidence in this order:

1. Current source and tests at the reported Git commit.
2. Executed tests appropriate to the change; full portable CI at integration.
3. The analytical/convergence/patch/support/performance QC suite.
4. `scripts/run_fe_verification.py`, which records commands, dependencies,
   warnings, return codes, and family reports.
5. Manifest-driven release gates and the production capability matrix.
6. Frozen local baselines.
7. Executed external-solver reports with solver identity, parsed observables,
   and tolerance-controlled comparisons.

Generated CalculiX-style input decks without matching executed results are
reproducible handoff artifacts, not numerical validation.

## Current verification policy

Since version 0.2, ANYsolver delegates material behavior, neutral meshing,
and interchange syntax to ANYmaterial, ANYmesher, and ANYfileio. A qualifying
ecosystem run
therefore installs those sibling packages, runs their own tests, and then runs
the ANYsolver suite and ecosystem-wiring tests. Compatibility tests must cover
both the historical ANYsolver imports and the canonical package imports.

Pass counts and timings are deliberately not embedded here: they become stale
as tests move to their owning repositories. The generated report under
`reports/verification/` is the evidence for a particular commit. Historical
release evidence remains available in Git history and `CHANGELOG.md`.

## Commands

Run from the repository root.

### Development loop

For an ordinary implementation edit, run the changed-behavior tests and one
affected integrated route. Select exact files or node IDs; inspect their scope.
Do not collect the complete suite, rebuild/install a wheel, hash the entire
package graph or replay a qualification campaign after every edit.

```powershell
python scripts/run_portable_ci.py --development `
  tests/test_changed_behavior.py::test_rejection `
  tests/test_affected_route.py --timeout-seconds 180 --memory-limit-mib 1024
```

Replace the example selectors with real tests. Focused mode runs exactly the
requested selectors in one source process, without CI deselections or automatic
dependency inference. Missing files/node IDs, empty selection, collection errors
and test failures fail. Skips/xfails remain visible and are not passes. The printed
temporary directory contains selection, effective runtime/coverage and resource
records. Keep those records with the relevant diff/commands; no separate
qualification package is required for routine development.

Default focused settings are one numerical thread, JIT off, plugin autoload off,
and a 600-second timeout. Use `--jit on` for changed compiled execution; JIT-off
checks cannot replace required compiled parity. Imported ANYsolver modules must
come from this checkout. Observed pools/Numba settings are recorded once after
the run, checked when loaded, and otherwise reported unavailable. The optional
memory ceiling requires `psutil` and samples the owned child process tree;
stricter task-specific time/memory/thread limits always take precedence. Ordinary
CI mode and its default timeout, inventory and matrix are unchanged.

### Coherent integration and promotion

Build and install once per coherent source candidate when its impact warrants
installed verification. Run affected lifecycle/public-consumer checks and one
representative example against that artifact. Prevent source `pythonpath` from
shadowing the installed package and verify actual import locations. Bind results
to the candidate and dependencies; changing artifact bytes changes its identity.
Reuse previous passing campaigns only for unchanged relevant inputs, with an
explicit impact explanation. Do not relabel old execution as a new artifact run.

Broaden testing for changed shared assembly, state, constraints, constitutive
updates, acceleration, public entry points or imports. Include required guard/
preimport and no-feature compatibility checks when affected. An isolated-plugin
development pass does not dismiss a real application/preimport failure.
Preimport metadata-cache and authority guards remain required when imports or
public adapters change; run them through the actual application entry point.
Recorded application failures remain open until that entry point passes; a
focused source guard test alone does not resolve them.

Full portable CI and all named scientific, external, installed-platform,
performance and release gates remain mandatory at their existing boundaries.
These tiers change execution frequency, not tolerances or supported claims.
Focused mode grants no execution authority, replays no consumed authority and
does not qualify or release a capability. Preserve failures. Do not repeat a
passed campaign without changed relevant inputs, a failure or an unresolved issue.

### Faster development, prospective 5 October 2026

Use four execution levels: exact changed-behavior checks after an edit; affected
subsystem checks after a connected slice; full portable CI and impacted installed
checks at integration; named scientific and release campaigns at their existing
acceptance boundaries. This implements the adopted risk-proportionate philosophy;
it does not change frozen registrations, tolerances or execution authorities.

Small named selections make the first level easy to repeat:

```powershell
python scripts/run_portable_ci.py --development-profile runner --timeout-seconds 180
python scripts/run_portable_ci.py --development-profile contact-smoke --timeout-seconds 180
python scripts/run_portable_ci.py --development-profile stiffened-smoke --timeout-seconds 180
```

Profiles expand to recorded exact selectors. They are starting selections, not
automatic dependency analysis or acceptance coverage. Add the changed behavior
and transitive consumers explicitly; broaden for shared operators, lifecycle,
constraints, import policy, or uncertain impact. Skips remain non-execution.
Collection, node setup/call/teardown and total resource time are recorded to
identify where deeper profiling is worthwhile. Work performed inside a test's
call phase still needs targeted profiling to separate preparation from solving.

`--development-cache` opts into checkout/runtime/source-bound compilation
reuse. It is for development only; default runs and CI remain cold.
Cache bindings include content changes and eligible runtime dependency bytes.
Unused unbound installations may coexist, but importing an unbound dependency
or repository helper makes a cached run fail explicitly; rerun cold without the
option. Unsupported cache preparation falls back cold with a recorded reason.
Bytecode reuse is disabled. Opt-in fingerprint preparation is measured separately;
it can outweigh compilation savings, particularly in large environments. Never cache
mutable models, material predecessors, accepted states or solved results to
speed up rollback, restart or independence tests. Use a cold run when testing
compilation/cache behavior or when a registered gate requires one. JIT-off
checks still cannot replace compiled parity.

The current contact/stiffened test intent inventory requires deliberate placement
of new modules. Existing classifications and coverage are preserved; adding a
test requires selecting its execution intent rather than silently extending a
functional campaign. Performance studies remain explicitly selected. The contact
chain mechanics regression uses one fresh-model parity pair; its original two
warm-ups and three alternating timing pairs remain in:

```powershell
$env:ANYSOLVER_RUN_CONTACT_CHAIN_BENCHMARK = '1'
python scripts/run_portable_ci.py --development tests/test_performance_contact_chain_comparison.py --jit on --timeout-seconds 180 --memory-limit-mib 1024
Remove-Item Env:ANYSOLVER_RUN_CONTACT_CHAIN_BENCHMARK
```

That command is an opt-in development benchmark, not qualification authority or
a universal speed claim. Existing stricter resource or campaign contracts win.
Do not enable saved-pose, external or historical campaigns by inheriting their
environment variables during an unrelated run.

Portable workers now include isolated interpreters within the requested worker
ceiling. Fresh-process isolation and complete inventory coverage remain intact.
CI cancels only superseded runs of this Tests workflow for the same PR; main and
manual runs remain independent. Cancellation is retained as cancellation, never
as a pass. Dedicated compiled/backend jobs retain their selectors and now record
effective single-thread/JIT/source settings through the development runtime.

Use observed costs to target further fixture/setup reuse and CI installation
reuse. No percentage development-speed improvement follows from these changes
without matched timing measurements.

### Full verification commands

```powershell
python scripts/run_portable_ci.py --workers 2
python run_qc.py --no-save
python scripts/run_fe_verification.py --output-dir reports/verification
```

The portable runner is the current merge inventory. Raw full-directory pytest
also collects historical machine/authority-bound tests; use those only within
their registered contracts. The comprehensive scientific runner retains its
declared scope and authority requirements.

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
