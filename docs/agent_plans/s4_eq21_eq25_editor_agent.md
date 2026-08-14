# S4 Eq.21/Eqs.24-25 sole editing-agent plan

## Agent objective

Implement only A1, A2, and the owned implementation-side A3 tests described
in `docs/S4_EQ21_EQ25_CORRECTION_PLAN.md`. Stop and report rather than choosing
a rank/null policy or substituting an unregistered formulation.

## Repository, branch, and exact baseline

- Worktree: `C:\Github\ANYsolver\.perf2-worktrees\s4-reference-core`
- Branch: `codex/s4-reference-core`
- Git base: `cd4831c6352844be7853f2764ada4f72662ab15f`
- Pre-correction source identity: decoded bundle
  `0CA69CFFF1C79EA8892D4F89FDC6E7A72C93BBA7525A4EA2BF9A9DD323DA4577`
- Governing accepted proposal:
  `643D01EC94ACEFE4335CC3BEF9F97AE682D6940108491E0EE63E1EC7D8FF457D`

The six pre-edit file hashes are recorded verbatim in the governing correction
plan. Verify them before the first implementation edit and report any drift.

## Exclusive owned files

This agent may edit exactly these paths and no others:

- `docs/S4_IMPROVED_FORMULATION.md`
- `src/anysolver/shell_formulations/protocol.py`
- `src/anysolver/shell_formulations/q4_common.py`
- `src/anysolver/shell_formulations/mitc4_plus_d_reference.py`
- `src/anysolver/shell_formulations/mitc4_plus_d_scalar.py`
- `tests/test_s4_eq21_eq25_reference.py` (new)

The agent must not edit `tests/test_s4_improved_reference.py`; it is the
unchanged acceptance gate. The coordinator owns all post-correction packet
files and every integration/shared path.

## Required implementation behavior

- Implement literal Eq. (21), including the fixed-center-to-natural double
  covariant transform before addition to membrane rows.
- Implement literal 2025 Eqs. (24)-(25) with outer/barred ties, `lambda`, Q,
  R, S, and direct Appendix-B reciprocal definitions.
- Keep any 2017 Eq. (27) comparison helper explicitly named and non-default;
  never use it as silent fallback.
- Keep all runtime inputs numeric and immutable; do not import ANYgeometry,
  parse documents, or call live geometry anywhere.
- Preserve analytic derivatives and deterministic signatures; do not add a
  numerical tangent, drilling penalty, hourglass energy, gauge, constraint,
  or empirical stabilization.
- Fail closed on invalid/inverted mappings without broadening scientific
  tolerances.

## Excluded files and systems

No edits to package initializers/exports, element records, dispatch,
serialization, recovery, assembly, activity/deletion, nonlinear/session/cache
paths, handoff/native-hybrid branches, integration worktree, or sibling
repositories. No qualification-contract changes or rank-policy choices.

## Tests and deliverable

Create focused tests only in the owned new test file. They must independently
exercise Eq. (21), QRS columnwise values, square/affine/skew/tapered/distorted/
warped cases, direct Appendix-B quantities, shear convention, cyclic/reversal/
rotation covariance, patch/objectivity behavior, scalar/generalized
consistency, deterministic identity, invalid mappings, and absence of geometry
imports.

Run only focused lightweight commands named in the governing plan. Heavy/full
suites, builds, profilers, benchmarks, scaling, and qualification require a
separate PERF lease. Before handoff, run `git diff --check`, report changed
paths and exact test results, and make one atomic child commit containing only
the registered plan files and owned implementation/test files. Do not merge or
cherry-pick it into integration.

