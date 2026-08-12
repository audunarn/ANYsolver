# S4 numeric-handoff and director specialist plan

## Objective and source inputs

Implement the geometry-runtime-independent provenance and per-corner director
contract required by the S4 improved plan and live-baseline addendum. Use the
read-only public ANYgeometry 0.2.x/ANYmesh/ANYfem contracts only for cold
compatibility fixtures.

## Repository, branch, and base

- Repository: `C:\Github\ANYsolver`
- Specialist branch/worktree: `codex/s4-geometry-handoff` in an isolated
  worktree created from the registered integration baseline.
- Base: ANYsolver `61e2f45ae2ca4fa87a6e149b0f89fabf209e5279` plus the registered planning
  commit.
- Sibling repositories are strictly read-only.

## Owned paths

- `docs/S4_GEOMETRY_HANDOFF.md`
- `src/anysolver/shell_formulations/director_field.py`
- `src/anysolver/shell_formulations/geometry_provenance.py`
- `src/anysolver/shell_formulations/mitc4_plus_d_quality.py`
- `tests/test_s4_geometry_handoff.py`
- `tests/test_s4_director_field.py`
- `scripts/check_s4_geometry_handoff.py`

The coordinator owns all existing shared modules, exports, serialization,
AnalysisSession integration, and runtime dispatch.

## Exclusions and ownership

Do not import ANYgeometry in production modules; parse/migrate geometry
documents; store live geometry objects; use geometry IDs as FE numbering;
average across sheets/parts/creases/intersections; infer coupling from
coincidence; or touch native-hybrid activity/assembly files.

## Milestones and definition of done

1. Document the schema-4 forward neutral numeric handoff, model-bound source
   identity, audit states, orientation, lineage, attachment/junction intent,
   tolerance separation, and stale-mesh policy.
2. Add compact immutable provenance header/tables/indices and deterministic
   fingerprints with `>=0.2,<0.3` compatibility metadata.
3. Add validated `(4,3)` element-corner directors and deterministic
   translation/rotation/numbering-invariant, crease/sheet/part-aware mesh
   reconstruction with explicit provenance/quality diagnostics.
4. Add wrong-model, stale, ambiguous lineage, audit, orientation, sharp-fold,
   separate-part, serialization, and zero-live-call tests.
5. Commit an atomic passing change and report exact commands and upstream
   activation gaps.

## Verification and performance

Focused tests and small linear-scaling checks only without a lease. Large
scaling/memory measurements require a performance lease. Ensure model-level
tables plus integer element indices; no repeated UUID/checksum strings.

## Dependencies and risks

Public `ShellElement` wiring and AnalysisSession keys are coordinator work.
Native-hybrid checkouts are dirty; inspect only stable public contracts and do
not couple tests to uncommitted internals.
