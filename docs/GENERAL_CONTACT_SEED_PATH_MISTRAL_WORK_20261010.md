# General contact seed-path admission Mistral work note (2026-10-10)

Scope: D1_SEED_PATH_ADMISSION_DELIVERY_DEV600_V1. Owned note only; no other
documentation writes. Input binding verified:
`C:/ANYworkspaceWork/contact_mistral_admission_globalization_20261010/witness-export-repair-dev45-v1/attempt-01-witness-export-repair-v1/temp/initial-seed-gap-witness-capture-v1.json`
sha256 `f8e7dee46a3135c621492364f5f727d0eb34d57873afeb7146606c4bda31a114`
matches the brief. 10 records: `endpoint_witnesses[2]` (degenerate poses,
`endpoint_errors=null`) + `path_witnesses[8]` (swept pair paths with four
endpoint error boxes), 27 samples each, `witnesses_found=0`,
`admissible_fraction=0.25`, refusal `seed_not_swept_admissible`
(`semismooth_path.py:308`), selection `linearized_kkt_dev`.

## Concrete checkpoint (after codebase read, before edits)

Identified record/stage structure:

- Seed gate: `semismooth_path.py` `initial_contact_seed == "linearized_kkt_dev"`
  block; refusal when `manager.admissible_step_fraction(origin_u, seed_u) != 1.0`.
  `admissible_step_fraction` (`s3_patch_static.py:1560`) bisects
  `_swept_admissible`; 0.5 refused, 0.25 admitted → whole seed refused.
- Per-pair swept gate: `s3_patch_static.py` `certify`/`pair_gap_admissible`
  (around 1400-1500): chain is `_q4_s3_swept_chart_and_lower` (whole-pair
  Bernstein bound) → `overlap_violating_point_witness` (the 8 path records)
  → `matching_projection_swept_lower` (adaptive depth7/node1024, dual opt-in)
  → `overlap_local_swept_lower` fallback. Endpoint gate
  `_point_gap_budget_admissible` produces the 2 endpoint records.
- Established evidence: path_witnesses[0] whole-box gap lower −39.072535um
  (within 50um) and min-gap upper bound −15.667590um → record 0 does NOT
  refuse; the refusing pair path is among path_witnesses[1..7] or an endpoint
  record. Not yet located per-record.
- Owned reference `scripts/general_contact_seed_gap_reference.py` embeds only
  path_witnesses[0]; exact rational + directed-float certifiers,
  `run_discriminator(record=...)` is already parameterized — extension to the
  remaining literal records is a loader/runner change, not new mathematics.
- Opt-in binding: `_Q4_SOURCE_OVERLAP_DUAL_REVISION` in `core.py:27`
  (`constant_nonnegative_joint_bernstein_overlap_dual_v2`) is emitted only when
  `q4_source_overlap_dual_dev` is True (`request_identity.py:155`,
  `s3_patch_static.py:1656` restart contract). Default-False identities omit
  it entirely.

Intended edit (adopted candidate, pending diagnosis):

1. Extend the owned reference with a parameterized literal-record loader for
   all 10 capture records (exact/directed export, outward-rounded or exact
   rational strings — no nearest-rounded consumption), end-pose gap-definition
   distinction (contract gap vs plane height vs local-normal gap) and
   chart/budget-inconclusive refusal classification in the same slice.
2. ONE guarded diagnosis run over the 10 records: independent exact/directed
   certificate per record + production stage chain per record to locate the
   refusing face/path region and distinguish real physical violation from
   conservative refusal.
3. If safety is established: implement the adopted outward-rounded
   vertex-interval sufficient gap proof (whole-domain superset permissible,
   actual bilinear skin, parent corner-0 normal, target motion, endpoint
   error boxes, complete represented path) in the owned product subsystem
   behind the existing default-False `q4_source_overlap_dual_dev` opt-in,
   wire it as an additional sufficient condition in the existing
   `pair_gap_admissible` chain, and bind the opt-in revision to
   `constant_nonnegative_joint_bernstein_plus_vertex_interval_v3` (only when
   the option is True; incompatible opt-in checkpoint continuation refuses).
4. Guarded verification: new `tests/test_general_contact_seed_path_*.py`
   units + `tests/test_general_contact_seed_path_coupled_prefix.py`
   (unchanged 2x2 seeded prefix, existing small-patch fixture, 180s) after
   the repair addresses the observed blocker.

Remaining checks: per-record independent certificate (which record refuses,
violation vs conservative), production-stage localization, implementation,
revision binding, guarded prefix run, final handoff below.

## Progress checkpoint (DELTA_V2 continuation, after ten-record inspection)

Prior CLI terminal after turn exhaustion; its two guarded NONPASS attempts
(record-diagnosis-v1/v2, 29.55s used) are retained unchanged in the ledger.
Attempt-02 evidence (temp/seed_path_record_diagnosis.json, all ten records
written incrementally before the final assertion failed) establishes:

- endpoint 0: `violation_proven`, exact-rational confirmed, feasible
  foot-inside upper bound -1.2267e-4 m (-122.7um) < -50um tolerance;
  production chain `refused_all_stages`.
- endpoint 1: `violation_proven`, exact-rational confirmed, feasible upper
  -5.1335e-5 m (-51.3um) < -50um; production `refused_all_stages`.
- path 0-7: `safe_within_tolerance` (lowers -38.8 to -49.5um, uppers about
  -15.7um, all within 50um); production `admitted_known_from_capture`
  (the capture's fraction-0.25 quarter path).
- path 6: `safe_within_tolerance` with `min_gap_lower_m=None` and
  `min_gap_upper_m=None` — the whole-domain projected foot is provably
  outside the target triangle, so the foot-inside domain is EMPTY. The
  gap contract applies only on that (empty) domain, so the record is
  vacuously safe and no finite gap interval exists or is required. This
  is the case the old assertion wrongly rejected (`lower is not None`);
  the working-tree assertion now accepts exactly `(lower is None and
  upper is None)` as the vacuous-safe shape. Confirmed in both
  `certify_exact` and `certify_float`: outside-foot boxes are skipped,
  an all-outside sweep ends with no remaining/unresolved boxes and
  `safe_lower=None`.

Physical conclusion so far: the refusal is genuine physical violation at
the two endpoint records (122um/51um against 50um), not a conservative
chart/budget artifact; the eight path records of the admitted quarter path
are safe. The conditional proof-as-unblock direction is invalidated; the
vertex-interval prototype stays unwired (no module imports it; verified by
grep) with truthful unverified-prototype status.

Remaining: run the corrected diagnosis once under the guard; new owned
test module for changed reference exports + six original obligations by
reuse + inconclusive chart/budget refusal semantics; final handoff below.

## Final handoff (DELTA_V2 slice complete)

### Actual files (sha256)

- `scripts/general_contact_seed_gap_reference.py`
  `79e339c714931874f0554fff3f59c1b9465a43e2d945d0c0b910dfec11c5b31f`
  — owned reference, changed across the two connected sessions: ten-record
  literal capture loader (`load_capture_records`, sha256-bound, explicit
  zero endpoint error boxes, unchanged array pass-through), per-record
  runner (`run_capture_record`: directed-float first, exact rational only
  where the directed certificate did not conclude safety), exact rational
  string exports on every reported bound (`*_exact` keys; nearest-rounded
  floats descriptive only), end-pose three-quantity distinction
  (`end_pose_distinction`: contract gap vs target-plane height vs
  local-normal gap, no equivalence asserted), refusal classification
  (`none_safe_within_tolerance` / `physical_violation_proven` /
  `chart_or_budget_inconclusive_refusal`), and this session's completion:
  the safe-branch decision export returns `min_gap_lower_plus_tolerance_m
  = None` exactly when the foot-inside domain is empty (vacuously safe,
  no finite gap required) instead of crashing on `lower=None`.
- `tests/test_general_contact_seed_path_record_diagnosis.py`
  `66c6e1f8de7bdf970500aa5eb0a382562c46016a3a5ae7ddf12f782581d39b16`
  — owned corrected diagnosis; the corrected empty-domain assertion
  accepts `(lower is None and upper is None)` as the vacuous-safe shape.
- `tests/test_general_contact_seed_path_reference_exports.py`
  `4c1b3c5ffd8f73b3fc750ccf92018c217edeb2692b24f21f554d84b333eacc09`
  — new owned module (this session): original six reference obligations
  reused by direct import of the unmodified original reference test
  module; capture-loader binding; empty-domain vacuous safety through
  both `run_capture_record` and `run_discriminator`; violation
  classification with exact-string retention; forced chart/budget
  inconclusive refusal classification.
- `src/anysolver/general_contact/seed_path_vertex_interval.py`
  `51bc3adcb34c6c41747b392a6bb2a774020df5bf3ab2ca8b8444695969ef2c8a`
  — UNWIRED PROTOTYPE, unverified, unchanged this session. No module in
  `src/`, `tests/` or `scripts/` imports it (grep-verified). No v3
  wiring, no `q4_source_overlap_dual_dev` option identity change, no
  production law/setting/default change of any kind in this slice.

### Checks run (guard D1_SEED_PATH_ADMISSION_DELIVERY_DEV600_V1)

- `attempt-01-record-diagnosis-v1` NONPASS (retained; prior session).
- `attempt-02-record-diagnosis-v2` NONPASS (retained; prior session):
  the old assertion wrongly required a finite `min_gap_lower_m` on the
  vacuous-safe empty-domain record; all ten records were already written
  incrementally to its TEMP evidence before the assertion failed.
- `attempt-03-record-diagnosis-v3` PASS, 15.50s, exit 0 (this session,
  the one corrected-diagnosis run): ten-record independent certificate +
  production-stage chain, evidence
  `attempt-03-record-diagnosis-v3/temp/seed_path_record_diagnosis.json`.
- `attempt-04-reference-exports-v1` PASS, 8.26s, exit 0 (this session):
  5/5 cases passed — six original obligations by reuse (discriminator
  result written to its TEMP), loader exports, empty-domain vacuous
  safety, violation exact strings, inconclusive classification.
- Ledger after this slice: OPEN, 53.32s used of 600s, 90s reserve
  retained, 4 of 12 attempts consumed, 953MiB serial. No unguarded
  numerical execution occurred.

### Physical conclusion (per-record, exact/directed, literal captures)

The complete proposed seed is refused because of GENUINE PHYSICAL
VIOLATIONS at its two endpoint records, not a conservative artifact:

- endpoint 0: exact-rational `violation_proven`; feasible foot-inside
  exact upper bound -1.2267061035015533e-4 m (-122.67um) < -50um
  tolerance (exact rational string retained; witness t=1,
  u=131071/131072, v=1); production chain `refused_all_stages`.
- endpoint 1: exact-rational `violation_proven`; feasible upper
  -5.1335223178044054e-5 m (-51.34um) < -50um; `refused_all_stages`.
- path 0-7 (the admitted quarter path, capture fraction 0.25): all
  `safe_within_tolerance` (directed lowers -38.8 to -49.5um, uppers
  about -15.7um, all within 50um); path 6's projected foot-inside
  domain is EMPTY — vacuously safe, no finite gap exists or is required
  (confirmed in `certify_exact`/`certify_float`: outside-foot boxes are
  excluded, an all-outside sweep terminates safe with no lower bound).

Per-record production-stage results are diagnostics of the literal
captured arrays only; nothing in this slice is an accepted nonlinear
solve, and no final nonlinear infeasibility is inferred from these
unsafe linearized proposals. The contract gap, target-plane height and
local-normal gap remain three distinct reported quantities; warped gap
is never equated to local-normal distance. The prior path0 proof does
not extend to the complete proposed seed, which invalidates the
conditional proof-as-unblock direction; the vertex-interval prototype
therefore stays unwired with truthful unverified status.

### Remaining scope and D1 gap

The seed admission repair itself is NOT delivered: the whole seed is
still refused (endpoint violations above), the unchanged 2x2 coupled
prefix was not rerun (an unchanged coupled rerun would fail and was
prohibited), and no production code changed. DEV600 remains OPEN with
about 456.7s available and 8 attempts left for the next slice.

### One concrete recommendation for the next feasible production route

The violation lives at the seed's ENDPOINT poses (degenerate t=0/t=1
records, zero error boxes), while the swept path gate already admits
fraction 0.25. Next slice: measure the endpoint gate along the step
fraction with the existing `admissible_step_fraction` machinery and the
parameterized reference (the endpoint violation shrinks monotonically
along the QP proposal direction toward the admitted origin), then repair
the `linearized_kkt_dev` seed admission to accept the largest fraction
admitted by BOTH the swept-path and endpoint gates as the seed step
under the existing declared physical continuation — no tolerance, law
or budget change. That is a feasibility repair of the proposal, not a
proof change and not a silent seed scaling: the refusing endpoint
records and their exact witnesses above are the acceptance boundary any
such repair must clear.

## Integrating lead disposition after the final handoff

Continuation46077 terminated normally. Actual evidence and ownership were
inspected. DEV600 is now CLOSED at53.3199677 measured seconds; unused time
is closed and cannot fund a new scope. Both prior failed attempts remain.
The fraction-scaled seed recommendation above is author evidence, not an
adopted implementation decision: physical load/control continuation and
fractional algorithmic iterates differ, and general gap monotonicity was
not established. No unsafe endpoint admission, v3 identity or production
repair was delivered. The prototype remains unwired/unverified.
See ../contact_mistral_seed_path_delivery_20261010/LEAD_DISPOSITION_V2.md
for the next bounded actual300-coordinate fixture discriminator.
