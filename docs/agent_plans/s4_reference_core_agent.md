# S4 reference-core specialist plan

## Objective and source inputs

Implement the clean-room scalar/reference foundation for the full 2 x 2
MITC4+/D element, following
`ANYsolver_S4_improved_Codex_plan_geometry_0_2.md`, its live-baseline addendum,
the existing ANYsolver contracts, and primary MITC4+/D publications only.

## Repository, branch, and base

- Repository: `C:\Github\ANYsolver`
- Specialist branch/worktree: `codex/s4-reference-core` in an isolated
  worktree created from the registered integration baseline.
- Base: ANYsolver `61e2f45ae2ca4fa87a6e149b0f89fabf209e5279` plus the registered planning
  commit.
- Sibling repositories are read-only.

## Owned paths

- `docs/S4_IMPROVED_FORMULATION.md`
- `src/anysolver/shell_formulations/protocol.py`
- `src/anysolver/shell_formulations/q4_common.py`
- `src/anysolver/shell_formulations/mitc4_plus_d_reference.py`
- `src/anysolver/shell_formulations/mitc4_plus_d_scalar.py`
- `tests/test_s4_improved_reference.py`

The coordinator owns package exports and every existing shared module,
including `elements.py`, `fe_core.py`, assembly, nonlinear-performance,
state, recovery, and runtime normalization.

## Exclusions and ownership

Do not edit ANYgeometry/ANYmesh/ANYfem, parse geometry documents, copy another
solver, introduce penalty drilling/hourglass behavior, use a numerical
production tangent, or touch activity/deletion/assembly hot paths.

## Milestones and definition of done

1. Map primary paper notation and all sign/frame conventions before production
   code.
2. Add immutable Q4 reference data and deterministic quality validation.
3. Implement shared 2 x 2 operators, physical `/D` drilling enrichment,
   MITC4+ membrane, MITC4 shear, scalar linear stiffness, consistent mass, and
   scalar residual/tangent primitives supported by the established equations.
4. Add algebra, patch, rank, rigid-motion, symmetry, mass, cyclic-numbering,
   warped-element, and finite-difference-oracle tests.
5. Commit an atomic passing change and report exact commands, scope, and any
   equation blocker without substituting legacy theory.

## Verification and performance

Run only focused lightweight tests without a lease. Heavy sweeps, profilers,
full qualification, and benchmarks require a performance lease. Record scalar
operator timings for later comparison but make no performance claim.

## Dependencies and risks

The batch specialist consumes these operators; coordinate interface changes
with the coordinator. The main risk is incomplete access to an essential
primary equation. Treat that as a precise blocker, not permission to invent or
fall back.
