# HANDOFF-04 — review repair (R1-R4), same Mistral implementation owner

Status: implemented and verified against the assigned criteria (this slice).
Root: C:/Github/ANYsolver, Mode Edit. No branches/commits/pushes/workers/sibling
edits/experimental programme execution.

## Working outcome

All four parent-review repairs applied as a compatible patch; no mechanical,
aliasing, tolerance, geometry-override or retirement changes.

- R1 (src/anysolver/mesh_gen.py, `_validated_shape_weights`): the partition-of-unity
  check now rejects a non-finite weight sum (`not np.isfinite(weight_sum) or abs(...)`),
  so finite mixed-sign weights whose pairwise reduction overflows to +/-inf/NaN can no
  longer pass. The reduction runs under `np.errstate(over/invalid ignore)` in the
  product because the deliberate finiteness check follows. Per-element finiteness,
  array aliasing, zero/negative weights and the 1e-10 rtol=0 threshold unchanged.
- R2 (tests, `test_interpolated_wrench_transfer_and_virtual_work`): beam node now at
  the physically matched `x_b = sum N_i x_i + r`; declared nonzero common origin
  o = [0.7, -0.15, 0.35]; resultant formed from the ACTUAL reported per-node wrenches
  as `sum f_i` and `sum [m_i + (x_i - o) x f_i]` and compared to `-F` and
  `-(M + (x_b - o) x F)` with separate FORCE_SCALE/COUPLE_SCALE (all mixed-unit
  6-vector assertions split the same way). Per-node distribution map kept separately.
  Virtual work now contracts the actual reported master-equivalent wrenches with an
  independent virtual field on the free model (identical node IDs) AND the analytic
  transported-wrench oracle (three legs: beam work = analytic work = -reported work).
- R3 (tests, `test_mutable_weight_refresh_matches_cold_session_parity`): now uses a
  real reused `AnalysisSession` (imported from `anysolver.analysis_session`) on the
  bare zero-stiffness coupling model. `constraint_plan()` reuse hit asserted; separate
  aliased weight update and offset update each rebuild with changed structure_key and
  match cold-session T/u0/independent_dofs exactly; stale pre-update plan rejected via
  `session.output_selection_plan(dofs, old_plan)` (ValueError, existing API);
  diagnostics assert invalidation_reasons["constraint_structure"] == 2,
  counters constraint_builds == 3, constraint_hits == 2, constraint_plan_rejections
  == 1. No cache fix; existing intended behaviour only.
- R4 (tests): the "linear" test now uses the actual 2-node collinear edge weights
  [1-t, t] at t=0.3 (3-node quadratic negative/zero-weight test unchanged); new
  positive shared-node control `test_shared_node_direct_composition_installs_no_mpc_constraints`
  uses the supported direct FEModel composition: `generate_simple_panel_mesh(1, 1, 0.01,
  num_divisions_x=1, num_divisions_y=1)` + standard `BeamElement` (steel, A=0.01,
  Iy=Iz=J=1e-6) on the SAME two shell edge node IDs; asserts exact edge DOF mapping
  identity, audit ok/feasible with mpc_slave_dofs == 0 and production T with
  num_mpc_slave_dofs == 0. No use of the refused `use_shared_nodes=True` flag; no
  eccentric capability restored. Existing self-coupling negative control kept.
- Docs (docs/standard_edge_beam_shell_coupling.md): corrected the wrong
  common-reference phrasing (algebraic sum of nodal couples is not a global moment;
  stated the transported-about-o identity with x_b = sum N_i x_i + r), documented the
  non-finite-sum admission rule, corrected the session claim (real reused
  AnalysisSession parity, structure-key invalidation, stale-plan rejection), and
  updated the coverage list (2-node linear weights, positive shared-node composition,
  common-origin resultants, reported-diagnostics work contraction).

## Changed files (this slice)

- src/anysolver/mesh_gen.py (R1 only; prior-slice dirty changes preserved)
- tests/test_standard_edge_beam_shell_transfer.py (R1-R4 test repairs)
- docs/standard_edge_beam_shell_coupling.md (claims)
- Evidence artifacts: CHECKPOINT-REVIEW.md, review_patch_04.py (exact-match patch
  script), REVIEW-FINAL-*/ (receipt, stdout, stderr), review-final.xml.

Not touched: assembly.py, elements.py, beam_shell_verification.py (prior preserved
work), all unrelated dirty files.

## Checks actually run

- `check.py REVIEW-FINAL 120 -m pytest tests/test_standard_edge_beam_shell_transfer.py
  -q --junitxml=.development/standard-edge-transfer-20261016/review-final.xml`
  (venv python, serial BLAS=1): PASS, exit 0, 16 passed in 1.67s (pytest),
  process wall 3.47s, cumulative check wall 61.0s of 2400s budget.
  Evidence: .development/standard-edge-transfer-20261016/REVIEW-FINAL-20261016T093500479697
  (receipt.json with exact command, source hashes, env, wall accounting; stdout.txt;
  stderr.txt) and review-final.xml (tests="16", failures="0").
- 16 = 14 prior tests (all still pass) + 2 new tests. No failures, no repairs needed
  after the patch; single check attempt, no retries.

## Failures

None. One tooling note: the harness `edit` tool could not match multi-line CRLF
regions, so the multi-line patches were applied with an exact-match assertion script
(review_patch_04.py, CRLF-preserving); the docs file is LF and was patched with a
separate LF script. Both scripts assert count==1 per replacement before writing.

## Not rerun (per brief)

The 39 related + 123 caller + 9 COUP suites were not rerun (previously PASS; the only
product change is a strictly tightening fail-closed admission on non-finite sums, with
no effect on valid weights). Parent will run portable integration. No experimental or
full-catalogue tests consumed.

## Unresolved decisions

None. No pending physical/architectural decision. Mechanical map, common r, aliasing,
tolerances, geometry override and retirement unchanged.
