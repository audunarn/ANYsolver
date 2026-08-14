# S4 compiled-batch and qualification specialist plan

## Objective and source inputs

Build the dedicated improved-Q4 compiled kernels and independent focused
qualification infrastructure from the shared operators defined by the S4
reference-core specialist. Follow the attached plan, live-baseline addendum,
and existing Sol Ultra performance architecture.

## Repository, branch, and base

- Repository: `C:\Github\ANYsolver`
- Specialist branch/worktree: `codex/s4-batch-qualification` in an isolated
  worktree created from the registered integration baseline.
- Base: ANYsolver `61e2f45ae2ca4fa87a6e149b0f89fabf209e5279` plus the registered planning
  commit.
- Sibling repositories are read-only.

## Owned paths

- `src/anysolver/shell_formulations/mitc4_plus_d_batch.py`
- `src/anysolver/shell_formulations/mitc4_plus_d_recovery.py`
- `tests/test_s4_improved_batch.py`
- `tests/test_s4_improved_recovery.py`
- `tests/test_s4_improved_qualification.py`
- `scripts/run_s4_improved_qualification.py`
- `scripts/benchmark_s4_improved.py`
- `scripts/compare_s4_improved.py`
- `docs/S4_REDUCED_RESEARCH.md`

The coordinator owns all existing shared assembly, scatter, nonlinear-state,
recovery, public export, and runtime files plus final report generation.

## Exclusions and ownership

Do not edit native-hybrid-owned activity/deletion/assembly paths; implement a
public reduced element; add hourglass/drilling coefficients; query live
geometry; use per-element Python loops in primary kernels; or weaken references
and tolerances. No external result may be fabricated.

## Milestones and definition of done

1. Freeze focused algebra/patch/distortion/mass/recovery cases and tolerances.
2. Implement contiguous homogeneous improved-Q4 batch data and compiled K/M,
   residual/tangent, KG, material-pack, and recovery kernels as shared
   reference operators become available; exact no-Numba fallback remains the
   improved theory.
3. Prove scalar/compiled parity and zero geometry calls in timed kernels.
4. Add qualification/benchmark scripts with explicit path activation,
   fallback reasons, memory, paired samples, and unavailable-external status.
5. Document why reduced integration remains a future sibling formulation.
6. Commit atomic passing slices and report commands, performance-lease needs,
   and unresolved integration gates.

## Verification and performance

Focused small parity tests may run without a lease. Full qualification,
11-sample benchmarks, profilers, memory/scaling campaigns, and large
regressions require an explicit performance lease from the ecosystem boss.

## Dependencies and risks

Compiled kernels depend on the reference-core interfaces and may need a
coordinated follow-up after that commit is integrated. Shared CSR/reduced
scatter and persistent-state wiring are coordinator-owned final-integration
work. Do not duplicate those systems in this branch.
