# General contact original workflow — Mistral work 2026-10-10

Owned working note for scope `D1_ORIGINAL_WORKFLOW_DELIVERY_DEV600_V1`
(repo `ANYsolver-contact-main-reconcile-20261001`, HEAD `3f654669`, mode Edit).
This note records concrete findings, intended edits, remaining work and
blockers for the connected actual300-coordinate initializer/first-increment
delivery. It is development evidence only, not installed engineering
qualification.

## Findings (inspection, pre-run)

- Guard `original-workflow-dev600-v1/guard.py` verified: fresh ledger
  (600 s limit, 90 s reserve, 0 used, 0/10 attempts), immutable source
  snapshot per attempt, TEMP redirected to the attempt directory, serial
  threads/JIT disabled, fixture hashes bound
  (`candidate_fixture.py` `3e178644...`, `force-full.json` `6de4c6f0...`).
- Original fixture confirmed: `build_candidate(descriptor)` with the
  `force-full.json` descriptor builds 300 dofs / 48 elements (16 Q4 source,
  32 S3 target), program `((0,0,0),(0.04,0.00008,0.0026))` with
  `steps_per_segment=8` (8 macro steps), fine 25-Q1 pressure rows,
  `complementarity_force_scale_n=0.018`, gap tolerance 5e-5 m, moving
  source-left guide (nodes 1,6,11,16,21 uz tied to node 1), physical
  target outer clamp, controls node1 ux/uz + node38 uz.
- First original waypoint = registered step 1 of the same programme:
  `max_load_factor=0.125` (`requested_step=round(0.125*8)=1`), not a new
  programme. Driver: `solve_static_nonlinear(..., contact_path_program=...)`
  -> `static_path.solve_static_contact_path` -> `semismooth_path.solve_increment`.
- Seed wiring confirmed: `initial_contact_seed='linearized_kkt_dev'` is
  opt-in (default `'none'`), requested only on the first macro attempt of a
  fresh frictionless reference-linear D1 overlap-local solve
  (`static_path.py` `initial_seed_selection`). The private
  `semismooth_path._INITIAL_SEED_DECISION_HOOK` (default None) receives the
  production decision payload after the unchanged admission predicates
  (actual-mechanics candidate reevaluation, swept admissible fraction,
  full scaled merit comparison) and before any Newton iteration.
- Admission predicates in `semismooth_path.solve_increment` (unchanged):
  finite merit, `seed_z >= 0` on supported modes, swept
  `admissible_fraction == 1.0`, strict `seed_merit < origin_merit*(1-1e-4)`.
  Refusal leaves the origin untouched; no acceptance gate changes.
- Revision binding: `core._INITIAL_CONTACT_SEED_REVISION =
  'origin_linearized_kkt_nonnegative_pressure_v1'`; enabled seed binds
  `contact_initial_seed` into the analysis identity
  (`static_path.py`) and `contact_initial_seed_revision` into the request
  identity (`request_identity.py`). Default-none keeps the exact legacy
  serialized shape (both strip the field).
- Prior evidence reused, not repeated: the coarser 2x2 toy's unsafe full
  proposal (~122um/half ~51um vs 50um budget) and its endpoint/path
  refusal are already captured; this scope uses the actual original
  fixture only.

## Intended edit

1. `tests/test_general_contact_original_workflow_seed_decision.py` (new,
   180 s cap): build the original fixture, enable
   `initial_contact_seed='linearized_kkt_dev'`, capture the first actual
   decision through `_INITIAL_SEED_DECISION_HOOK` (full bound
   q/reactions/z/control/gap/merit arrays + numerical source/effective
   runtime provenance written to the guard TEMP), raise `SolveCancelled`
   intentionally, verify propagation and coherent rollback (identical
   decision on an immediate rerun proves no partial state survived).
2. Depending on the captured outcome:
   - admitted -> `tests/test_general_contact_original_workflow_first_increment.py`
     runs the actual ordinary first increment (step 1, `max_load_factor=0.125`)
     with the seed enabled and checks the caller/state result.
   - refused -> implement the adopted bounded backtracking of the complete
     algorithmic correction as an opt-in v2 selection
     (`origin_linearized_kkt_seed_merit_globalization_v2` revision), with
     finite trial policy reevaluated per trial (finite/nonnegative
     supported forces, actual coupled residual/control/NCP merit, full
     conservative swept-gap admission from the same committed origin,
     strict merit improvement, explicit refusal otherwise), demonstrate
     the changed decision, then run the first increment.

## Actual state (attempts 01-04, CLI11953) and independent findings

- Guard attempts 01/02 (seed decision, NONPASS) and 03 (QP mechanism,
  np.int64 JSON signature) were fixture-assertion failures; attempt 04
  (QP mechanism) PASSED and captured the exact production QP operator
  (`original-workflow-qp-mechanism-v1.json`): 25 modes, SPD
  symmetrized gap response (eigenvalues 4.42e-8 .. 1.93), asymmetry
  2.85e-14, backward error 2.67e-13, v1 terminal `iteration_cap` at the
  full 116 iterations.
- Verified mechanism from the captured trace: from iteration 4 the v1
  active-set loop sits at free face {11} with free gradient 3.98e-5
  (face NOT stationary) and 5 bound gradients < -1e-12 (min -6.92e-5);
  each iteration releases the most negative bound index, the enlarged
  face minimizer wants that entering index negative, it re-clamps at
  zero with no move, and the identical working set repeats 112 times to
  the cap. Final full gradient residual 2.47e-4 — a real stationarity
  violation, not roundoff.
- v2 central edits exist (selection plumbing in core/request_identity/
  static_path, bounded-globalization block in semismooth_path, QP
  release_alternatives in initial_contact_seed) but are
  implemented-unverified: the QP-mechanism test wrapper predates the
  `release_alternatives` keyword and would now raise TypeError, and no
  v2 numerical decision has been captured.
- Independent scrutiny (Reader99108, preliminary) findings to repair:
  - R1: the bounded-globalization block is claimed to crash with
    UnboundLocalError on origin-evaluation failure or proposal refusal.
    Verified against current source: the block is nested inside the
    proposal-accepted `else`, so those refusal paths cannot reach it
    and `seed_q`/`seed_mu`/`seed_z`/`unsupported`/`seed_base` are always
    assigned when it runs; the literal crash path does not exist in the
    current nesting. The invariant is still made structural (explicit
    finite-proposal guard) and a production-caller regression for both
    refusal entries is added.
  - R2 (real defect): the v2 QP masks blocked negative bound gradients
    before its optimality check and can certify `optimal` from a
    repeated-face fixed point without the full unmasked KKT residual.
    Neither is sufficient; the 2.47e-4 residual shows the false
    optimal. Repair below.

## Concrete repair/check plan (this continuation)

1. R2 repair in `initial_contact_seed._bounded_nonnegative_qp`
   (v2 `release_alternatives` path only; v1 behavior byte-identical):
   - optimality is certified ONLY from the full unmasked KKT residual
     (no bound gradient < -tolerance, no free gradient magnitude >
     tolerance); the `blocked` mask only limits release selection;
   - v2 sequencing: a bound index is released only when the current
     iterate is stationary on the current free face; otherwise the loop
     keeps minimizing the current face (the captured trace shows the
     release-while-nonstationary sequencing as the cycling driver);
   - the repeated-face fixed point no longer certifies `optimal`: a
     fixed point without full KKT support terminates honestly as
     `kkt_fixed_point` (caller refuses `qp_kkt_fixed_point`); a
     degenerate release (enlarged-face minimizer keeps the entering
     index at zero) re-clamps and excludes the index for the current
     face;
   - the computed full KKT/gradient residual (free max abs, bound min,
     overall max abs) is reported in the seed diagnostics for every
     terminal; tolerance 1e-12*scale and cap 4*modes+16 unchanged; no
     regularization.
2. R1 repair in `semismooth_path.solve_increment`: the bounded block
   additionally requires an actually constructed, unrefused proposal
   (`proposal is not None and not proposal.refused`), making the
   only-backtrack-a-finite-proposal invariant structural.
3. Test repairs: QP-mechanism wrapper forwards `release_alternatives`
   (v1 replay and cap assertion unchanged) and additionally runs the
   repaired v2 QP on the exact captured original operator, asserting an
   honestly supported terminal and recording the full KKT residual;
   seed-decision v2 test's unconditional `origin_merit` assertion made
   conditional (proposal-level refusals carry no origin merit); two
   production-caller refusal regressions added under v2 (patched
   origin-evaluation failure and patched proposal refusal through the
   real driver): explicit refusal record, no crash, no
   `bounded_globalization` trials, origin/model/programme identity
   unchanged.
4. Guard sequence (existing balance only, no renewal): QP mechanism
   (60 s), seed decision incl. v2 changed-decision evidence and
   refusal regressions (180 s), then — only if the v2 seed admits —
   the actual ordinary first original increment
   (`test_general_contact_original_workflow_first_increment.py`,
   180 s): same programme/load/control target, `max_load_factor=0.125`,
   existing gates, captured result/checkpoint. If the seed does not
   admit, diagnose ONE concrete obstruction before any expensive run.

## DELTA_V4 continuation state (test-oracle correction, this session)

- Attempt 05 (qp-mechanism-original-03) NONPASS retained as evidence: its
  `v2_residual = max(abs(h @ v2_z + g)) <= tolerance` oracle is INVALID for
  z >= 0 (a positive gradient at a zero-pressure bound is valid); the
  reported 4.461947712e-4 all-gradient maximum is not an optimality defect
  by itself. Classification as a test-oracle defect is made only after the
  corrected actual checks below support it.
- Corrected qp-mechanism test oracle (owned test only, tolerance and cap
  unchanged): exact nonnegativity/finiteness; stationarity on the
  positive-pressure support (gradient ~ 0 where z > 0); valid bound gradient
  (gradient >= -tolerance where z == 0); KKT residual = max of the separate
  stationarity and bound-gradient violations; complementarity recorded;
  the all-gradient maximum kept as a separate descriptive field
  (`v2_repaired_all_gradient_max_abs`), never the KKT norm. Diagnostics are
  written BEFORE the KKT assertions. The v1 production iterate gets the same
  support-split decomposition as descriptive evidence of the real legacy
  defect (nonstationary free face 3.98e-5, negative clamped gradient
  -6.92e-5), while the v1 `iteration_cap` assertion is unchanged.
- Seed-decision test: the v1 refusal branch now asserts the explicit legacy
  refusal shape (`reason == "qp_iteration_cap"`, no `origin_merit`, no
  proposal arrays) instead of silently tolerating both shapes; the two
  authored refusal regressions (origin-evaluation failure, proposal
  refusal) already assert the same missing-`origin_merit` shape and that
  the bounded-globalization block never runs.
- Verified in current source before the runs: the v2 QP certifies `optimal`
  only from unmasked bound violations plus free stationarity; the
  bounded-globalization block is unreachable without an actually
  constructed, unrefused proposal (no UnboundLocalError path); the v2
  mirror replay in the test matches the production loop exactly.
- Guard sequence (existing balance only): qp-mechanism-original-04 (60 s),
  seed-decision-original-03 (180 s, v1/v2 + refusal regressions), then only
  if the v2 seed admits, first-increment-original-01 (180 s) with the same
  full programme, `max_load_factor=0.125`, `max_iterations=18`, all
  existing gates. Actual outcomes are appended below.

## Remaining work

- Run the guard sequence above, record actual outcomes/captures, complete
  the focused default-none/v1/v2 identity and incompatible opt-in/cancel
  safety evidence where available, and give the FINAL HANDOFF.

## Blockers

None currently.

## Root-reconstructed pause handoff — 10 October 2026

State: partial implementation verified against selected source-only checks;
latest first-increment test edits UNVERIFIED. No final worker handoff was emitted.
All owned actors are terminal; no matching process remains. Actual guard evidence:
QP attempt06 PASS; seed/refusal attempt08 PASS4/4; first-increment attempt09 NONPASS
on NumPy Boolean identity despite actual completed two-Newton-step increment.
Final worker changed Boolean handling, moment scale and producer-checkpoint capture,
but launched no tenth attempt. No producer-checkpoint evidence exists yet.
Ledger used232.5507088000304s,9/10 attempts;90s reserve remains protected.
See GENERAL_CONTACT_RESTART.md for exact next actions, scope and evidence paths.
Earlier "Remaining work"/"Blockers" lists above are historical, not live status.