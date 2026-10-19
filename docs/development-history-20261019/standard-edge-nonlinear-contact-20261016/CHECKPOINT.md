# CHECKPOINT — nonlinear/contact reliability slice (worker, turn ~7)

## Concrete findings so far (inspection)

- Harness understood: `check.py` wraps every Python run, serial budget 1200 s
  process-wall with 300 s FINAL reserve; labels other than FINAL get
  `remaining - 300` s. Evidence dirs per label-timestamp with receipt.json.
- `tests/test_general_contact_plane.py` (394 lines) is the contact oracle
  reference: `_PlanarQ4PlaneManager(model, contact).evaluate(u)` returns
  `(force, tangent, result)` with `minimum_gap`, `penalty_energy`,
  `shell_force`, `active_pressure_dofs`, `shell_moment`; central-difference
  tangent checks at h=1e-6 with rtol 1e-8/atol 1e-7..1e-6; restart test uses
  `solve_static_nonlinear(..., max_load_factor=0.5, emit_restart_checkpoint=True)`
  then `restart_checkpoint=half.to_restart_checkpoint()` with rtol 1e-8 /
  atol 1e-10 vs uninterrupted; changed contact law raises
  "analysis contract is incompatible"; callback failure propagates and
  `active_contact_manager()` is None afterwards.
- `tests/test_standard_edge_beam_shell_transfer.py` (762 lines) is the
  coupling oracle reference: production `build_constraint_transformation`,
  `reconstruct_full_solution`, `compute_constraint_force_diagnostics`
  (buckets: `mpc_slave_forces`, `mpc_master_equivalent_forces`,
  `support_reactions`; convention K u - F; master-equivalent is
  `-N_i [F, M + r x F]`), dimensionless identity ATOL 1e-10 with explicit
  scales; `InterpolatedBeamShellMPCElement` and `CoupledBeamShellElement`
  constructors; shared-node positive control = direct FEModel composition
  (BeamElement on the same shell edge node IDs, no MPC).
- Source map: `nonlinear_static.py` (8308 lines) builds the constraint
  transformation at line ~5454 via `build_constraint_transformation` and has
  force/displacement control paths; `nonlinear_reduced_assembly.py` (805
  lines) has `build_reduced_assembly_plan` / `assemble_reduced_system`
  (selector and weighted reduced plans, force/tangent mapping appends);
  `general_contact/core.py` has `_PlanarQ4PlaneManager` (evaluate,
  admissible_step_fraction, restart_contract, contact_scope/suspend_contact);
  `general_contact/static_path.py` has `solve_static_contact_path` and
  `ContactPathProgram`; `nonlinear_restart.py` has checkpoint
  create/load/validate with model/analysis configuration fingerprints.

## Intended fixture (design)

New module `tests/test_standard_edge_beam_shell_nonlinear_contact.py`:

1. Qualified Q4 cantilever shell (root fixed) + standard BeamElement along
   the free edge, three routes: SAME shared node IDs (direct composition),
   geometrically matched one-to-one eccentric `CoupledBeamShellElement`,
   interpolated `InterpolatedBeamShellMPCElement` with nontrivial weights
   (negative quadratic weights in the local identity checks).
2. Reduced-vs-full: production reduced force/tangent through the real T
   (constraint-reduced system) compared against full unreduced assembly
   with the MPC eliminated, dimensionless identity <= 1e-10.
3. Central differences of the production residual at open and closed
   contact states, same committed state restored each evaluation,
   translation/rotation/mixed retained directions (lever arm/weights
   active), three locked dimensionless perturbations 1e-4/1e-5/1e-6 times
   explicit length/rotation scales; scaled tangent error <= 1e-6 at two
   adjacent sizes; no differentiation across a contact branch switch.
4. Virtual work and wrench transfer about a common origin from actual
   reported diagnostics buckets, no double counting.
5. Press-release-recontact public solves per route (von_karman,
   shell-only contact): coupling/equilibrium at accepted states, open force
   zero, recontact consistency.
6. Deliberately rejected trial and cancellation preserve accepted state
   (existing status_callback / cancel APIs).
7. Split restart vs uninterrupted rtol 1e-8 / atol 1e-10; changed valid
   weights OR offset rejects the checkpoint before new Newton work.
8. Finite-MPC refusal: use existing non-retired coverage/static source
   review; report exact gap if a fixture would need retired source.

## Remaining work / blockers

- Inspect `nonlinear_static.py` force-control path around MPC reduction and
  callback/cancel APIs; `nonlinear_reduced_assembly.py` plan API; contact
  integration in `static_path.py`; restart fingerprint checks for changed
  weights/offset.
- Then implement module, run first focused check (<=120 s), repair, docs,
  plan append, HANDOFF.md.
- No blockers yet. No checks run yet (budget untouched).

## CONTINUATION-02 delta (worker-02, turn ~7)

Parent review PARENT_REVIEW_01.md read; six repairs mapped to concrete edits in
the owned test module (no source changes planned):

- R1: press/release/recontact becomes ONE public NonlinearLoadProgram solve
  (NonlinearLoadStage press/release/recontact, classes at nonlinear_static.py
  249/268) on one model per route, record_increment_snapshots=True; every
  accepted snapshot checked for stage factors, MPC map, contact branch,
  equilibrium from actual nonlinear internal+contact force vs staged external
  load (never tangent-times-u). Stage-boundary commits confirmed at
  nonlinear_static.py 7099-7107 (increments never jump a cumulative boundary).
- Fixture contract: successful cycle/restart moves to rigid plane z=0
  (admitted _guided_plate-style configuration), tolerance 0.001, stiffness
  1e5, press 0.1/node; release/recontact stage forces +0.102/-0.102 per node so
  the open endpoint has positive free-edge gap (~1.3e-3 m uplift) while
  accepted rotations stay <= 0.01 rad (expected ~2e-3 rad). Separated plane
  z=-0.04, tolerance 0.001 kept for the rejected-trial and derivative cases.
- R2: cancellation now cancels from the progress event 'nonlinear_static_step'
  (nonlinear_static.py 7597, after commit) after one accepted step, with
  _commit_nonlinear_state_candidate (3395) wrapped by monkeypatch (calling the
  original) to capture the real state owner; after SolveCancelled assert
  generation/has_active_trial/payload vs the accepted baseline, then re-solve
  the SAME model and compare to a clean reference. Rejected-trial test adds
  snapshot/checkpoint comparison of the retained state plus re-evaluated
  equilibrium.
- R3: committed mapping snapshot becomes an owned deepcopy with explicit
  restore per +/- FD evaluation and baseline-unchanged verification; every
  perturbed contact evaluation asserts branch margins (active pressure count,
  minimum-gap margin, penalty energy), not just minimum_gap.
- R4: drop the linear compute_constraint_force_diagnostics oracle; use actual
  nonlinear residual f_int(+contact)-F_ext, per-slave analytic transfer
  N_i[F, M + r x F] vs production T mapping, nonzero force/couple required,
  common-origin wrench, and actual nonlinear support-reaction buckets.
- R5: weights (1.4,-0.4) case relabeled as an algebraic extrapolation
  compatibility control (outside the Q4 edge), not a quadratic on-edge record.
- R6: finite-MPC guard at static_path.py 950 confirmed (zero-offset selector,
  no weighted MPC rows, no repeated columns); preserved unchanged, documented
  as static source review evidence.
- Restart: false half-load-open/cross-closure claim removed; with plane z=0
  the half-load state is already closed - actual branch inspected and split vs
  uninterrupted equivalence kept at rtol 1e-8/atol 1e-10, plus direct
  half-state vs uninterrupted-snapshot continuity check.

Next: rewrite tests/test_standard_edge_beam_shell_nonlinear_contact.py, run
focused check via check.py (non-FINAL label), repair, then docs/plan append and
HANDOFF.md. Budget: 1162.31s remaining, 300s parent reserve.
