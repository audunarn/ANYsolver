# Handoff — standard element-edge beam-shell coupling implementation

Label: **implemented and verified against the assigned owner criteria**
(worker evidence; parent acceptance pending). Resume continuation of the same
authorised Mistral Edit ownership; head 95c33512 unchanged, no commits, pushes,
branch changes or workers. Pre-existing dirty work (including assembly.py)
untouched and preserved.

## Changed files (owned boundary only)

- `src/anysolver/elements.py` — `CoupledBeamShellElement`: constructor
  validates explicit eccentricity (shape (3,), finite, aliasing preserved);
  `_eccentricity_vector` validates explicit and geometry-derived r;
  `get_mpc_constraints` raises ValueError on missing beam/shell node instead
  of silently returning []. Mechanical map unchanged.
- `src/anysolver/mesh_gen.py` — `InterpolatedBeamShellMPCElement`: new
  module constant `COUPLING_PARTITION_OF_UNITY_ATOL = 1e-10` (parent-adopted,
  absolute, rtol=0, no renormalization); constructor validates weight count /
  1-D shape / finiteness / partition of unity and offset shape/finiteness
  (aliasing preserved); `get_mpc_constraints` revalidates the aliased mutable
  inputs at emission, raises on missing beam node and on any missing shell
  master (including zero-weight masters), keeps duplicate-master merging and
  zero/negative-weight validity. No zip truncation.
- `src/anysolver/beam_shell_verification.py` — COUP-012 catalogue label
  corrected to "Actual eccentric one-to-one MPC affine-field reproduction"
  (fixture and case count unchanged).
- `tests/test_standard_edge_beam_shell_transfer.py` — new (14 tests).
- `docs/standard_edge_beam_shell_coupling.md` — new coupling guide.
- Evidence only under `.development/standard-edge-transfer-20261016/`
  (CHECKPOINT.md, postpatch_selected.py, postpatch-selected-report.json,
  old_vs_new_admission.py, old_mesh_gen_head.py, check receipts).

No coordinate-consistency rejection was added (explicit offsets remain
algebraic overrides per PARENT_DECISIONS.md). No changes to assembly.py,
constraint_audit.py, runtime.py, pytest configuration or any excluded file.

## Checks actually run (check.py, serial BLAS 1, retired opt-in disabled)

| Label | Status | Wall | Result |
|---|---|---|---|
| NEW-TESTS-DEBUG / -DEBUG2 | FAIL (debug iterations) | 4.95s / 3.71s | fixed test-harness issues (fixed-master virtual work; bad POU example) |
| NEW-TESTS | PASS | 3.43s | 14 passed (new module) |
| AFFECTED-SUITES | PASS | 5.26s | 39 passed (test_constraint_audit, test_analysis_session, test_static_batch_coupled_acceleration_guards) |
| POSTPATCH-COUP-SELECTED | PASS | 18.58s | COUP-005/007/012/013/014/015/016/018/019 all PASS (report: postpatch-selected-report.json) |
| ELEMENT-USER-SUITES | PASS | 16.74s | 123 passed (test_submodel_transfer, test_fe_solver_anystructure_fem_mode, test_fe_solver_theory, test_prepared_static_contracts, test_e4_pl_workflow_parity) |
| OLD-VS-NEW-ADMISSION | PASS | 1.31s (after 0.40s FAIL: standalone module registration) | HEAD admitted all five malformed inputs; patched classes reject all five |

Cumulative check wall per receipts: 57.40s (includes 3.03s pre-edit baseline).
Owner check wall consumed this session ~54.4s of the 1196.96s remaining
allowance; ~1142s remains for parent verification. Per-process cap 600s
respected. Baseline was NOT rerun (inputs unchanged until my edits).

## Regression demonstration (new tests fail old implementation)

`old_vs_new_admission.py` loads HEAD `mesh_gen.py` standalone and shows, on
identical inputs: count-mismatch weights, partition-of-unity violation
(sum 0.99), non-finite weights were all admitted by HEAD and are rejected
now; missing beam node returned [] silently at HEAD and raises now; missing
zero-weight master was silently skipped at HEAD and raises now.

## Verification coverage delivered (new module, production paths only)

Actual `build_constraint_transformation` T and
`compute_constraint_force_diagnostics` with independent oracles, dimensionless
residuals <= 1e-10 against stated scales (translation 1 m, rotation 1e-3 rad,
force 1e3 N, couple 1e3 Nm, work 1e3 Nm): affine u/theta fields with common
offset (linear and quadratic weights incl. negative and zero), infinitesimal
rigid-motion consistency on a physically matched record, frame covariance,
edge-reversal invariance, corner shared by two edges with unique slave
ownership (12 slave DOFs, audit ok), endpoint degeneration to the one-to-one
map, shared-node self-coupling rejected by the audit, wrench transfer
(master-equivalent = -N_i [F, M + r x F], internal K u - F sign documented,
support bucket separation), virtual work through production T, malformed
rejection through audit/assembly with no partial emission, post-construction
corruption rejection at emission, constructor aliasing, and mutable-update
refresh vs cold-session parity (exact T equality).

## Unresolved decisions and remaining work

- None blocking. No contract blocker encountered; parent POU decision and
  no-coordinate-rejection decision were implementable as stated.
- Not run by owner (out of selected set / parent reserve): COUP-017
  production Q8/Q8R suite (its ANYmesher-generated weights pass the same POU
  admission; COUP-005/007 exercise the `_install_couplings` route and pass),
  full beam_shell_verification suite, contact/follower-pressure suites
  (CoupledBeamShellElement users with valid inputs), and
  test_ge_beam3_mixed_p3_optin.py (retired-adjacent opt-in, never enabled;
  its [1.0] weights are POU-compatible by inspection).
- Parent review items: confirm the COUP-012 label wording, and run the
  applicable integration gates after this handoff.
