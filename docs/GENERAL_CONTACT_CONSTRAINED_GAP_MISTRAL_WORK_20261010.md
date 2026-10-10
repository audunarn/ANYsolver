# Mistral constrained-gap work note — 2026-10-10

Owned kernel: `src/anysolver/general_contact/q4_overlap_local_bound.py`.
Owned tests: `tests/test_general_contact_constrained_gap_joint_dual.py` (new).
Status: FINAL HANDOFF, revised by the parent integration inspection repair
(same owner, same owned boundary), then updated with the admitted exact-pair
guarded result (see the last section). The focused pytest stage remains
unverified (timeout, preserved); the exact-pair discriminator check has now
run under the parent's guard and certified the pair.

## Findings (source inspection only)

- The refusing production route is `matching_projection_swept_lower` with
  `gap_budget`/`refinement_gap_budget` = 5e-5 m, `adaptive_depth=7`,
  `node_budget=1024`, opt-in `overlap_dual=True` (s3_patch_static.py:877,953,1456).
- Terminal-box certificate: `lower = min(0, n_lower) * p_upper / d_lower` with
  numerator A enclosed by 5 (time) x 4 (box corner) joint Bernstein controls;
  overlap constraints u,v,w (raw target barycentric numerators, m^4) share the
  same 20 joint controls. On the represented overlap u,v,w >= 0.
- Existing opt-in dual: one constant NONNEGATIVE weight per single axis
  (U or V or W), candidates from choose(20,2) line intersections per axis
  (<= 570 total), each batch-validated with directed outward arithmetic
  (`_overlap_dual_axis_lower`); baseline (0,0,0) via
  `_overlap_dual_coefficient_lower`, which already accepts full
  three-component constant weights but is never searched jointly.
- Evidence (read-only, `overlap-dual-start-reuse-v1`): exact 7/30 refusal
  lower -50.01322558144736 um at depth exhaustion, 43 nodes, node budget not
  exhausted; axis dual was enabled. Independent strict-inside point intervals
  ~ -48.1158 um (base) and ~ -48.1755 um (refused endpoint). Needed
  certificate gain to admit at unchanged 50 um budget: 0.01322558144736 um
  (0.0265% of the bound). A prior 7/35 full-proposal point violates ~ -110 um
  (not equilibrium infeasibility; do not replay).
- Conservatism decomposition of bound vs sampled point (~3.8% total):
  (a) Cauchy-Schwarz (R.Ns)/|Ns| <= |R| with R = corner-0 normal (time-varying);
  (b) box min of A vs overlap-restricted min of A; (c) d_lower/p_upper
  enclosure slacks; (d) sampled points are not the overlap minimizer.
  The dual attacks (b) only.

## Hypothesis H1 (bounded, one route)

At the refusing 7/30 terminal boxes, the single-axis dual leaves numerator
slack because the min-of-A controls sit where the foot is provably outside the
target triangle across MORE THAN ONE barycentric constraint simultaneously.
The exact LP optimum of the box certificate

  max over constant lambda = (lU, lV, lW) >= 0 of
  min over the 20 joint controls of (n_lo - lU*u_hi - lV*v_hi - lW*w_hi)

is approached by a bounded candidate enumeration (variables t, lU, lV, lW;
20 rows t + lambda.c_j <= n_j, 3 rows lambda >= 0): all choose(23,4) = 8855
4-subsets are treated as candidate active sets (bounded, deterministic,
structurally including the single-axis sets). Finite-precision determinant
filtering and solving do not certify that all vertices or the exact optimal
LP value were recovered, and unbounded/degenerate LPs are not specially
handled; the directed validation of the chosen nonnegative vector is sound
regardless of enumeration completeness. The joint stage runs only after the
axis stage and max's into the existing lower, so it is never weaker and
never admitting (directed outward arithmetic).

Outcome mapping:
- Joint certifies the 7/30 endpoint (>= -50 um): refusal was numerator/box
  conservatism -> parent runs the focused tests + exact refusal-pair check;
  endpoint admissible at unchanged mechanics/budgets.
- Joint improves but still < -50 um: remaining slack is (a)/(c)/(d) -> next
  decision: box-aware cosine enclosure of (R.Ns)/|Ns| (needs |Ns| lower via
  pairwise corner-normal quartics) or accept refusal as possibly physical.
- No improvement at all: a negative result for this candidate enumeration
  only. It does not prove the axis weights were LP-optimal on the refusing
  boxes and does not rule out numerator slack; escalate with the (a)/(c)
  decomposition instead.

## Implementation plan (owned files only)

1. Kernel: add `_overlap_dual_joint_candidates` (8855-set vertex enumeration,
   det pre-filter, batched solve, lambda >= 0 filter, exact-float dedupe,
   sorted deterministic order) and `_overlap_dual_joint_lower(numerator,
   barycentric)` -> (lower, checked): batched directed validation mirroring
   the gold subtraction order, winner revalidated through
   `_overlap_dual_coefficient_lower`, adopt min(batched, gold).
2. Call site in `matching_projection_swept_lower`: run the joint stage ONLY
   when a finite threshold exists AND the box still refuses after the axis
   dual (`lower < -threshold`). No-budget dev calls and default False paths
   are bit-unchanged. New diagnostics keys `dual_joint_candidates_checked`,
   `dual_joint_improved_boxes` (additive; existing keys and the
   `checked <= 570` / `dual_improved_boxes == 1` contracts preserved because
   the joint never fires in those scenarios).
3. Tests `tests/test_general_contact_constrained_gap_joint_dual.py`:
   synthetic LP where joint optimum -2/3 strictly dominates every single-axis
   optimum -2; counterexample preservation (joint cannot beat the honest -1
   on the existing coefficient-varying counterexample controls); gate and
   diagnostics integration through `matching_projection_swept_lower`;
   bounded/deterministic enumeration properties; invalid-input refusal;
   batched-vs-gold parity.
4. Proposed checks (parent-admitted runs only):
   `python -m pytest tests/test_general_contact_constrained_gap_joint_dual.py
   tests/test_general_contact_overlap_dual_certificate.py
   tests/test_general_contact_overlap_dual_integration.py -x -q`
   (serial, < 1 GiB, minutes), then the exact refusal-pair witness rerun with
   the joint-enabled candidate; discriminator: 7/30 endpoint lower moves from
   -50.01322558144736 um to >= -50 um or not, with
   `dual_joint_improved_boxes > 0` on the refusing boxes.

## Reserved decisions (parent)

- Any change to s3_patch_static.py, settings, method revision string
  (`fixed_axis_nonnegative_bernstein_overlap_dual_v1` in core.py), restart
  identity, or promotion of the result. NOTE: the opt-in flag-on behavior is
  now strictly stronger on budget-refusing terminal boxes; the parent should
  decide whether the method revision string/restart identity moves to a v2
  before any admitted rerun that compares against archived identities.
- Whether a still-refusing outcome triggers the cosine-enclosure route or
  closure as inconclusive/possibly-physical.

## Final handoff (source phase complete)

### What was implemented

All in `src/anysolver/general_contact/q4_overlap_local_bound.py`:

1. `_overlap_dual_vertex_active_sets()` + module constant
   `_OVERLAP_DUAL_VERTEX_ACTIVE_SETS`: the fixed choose(23,4)=8855 active
   4-subsets of the certificate-LP constraint rows (20 joint-control rows
   t + lambda.c_j <= n_j, 3 nonnegativity rows lambda_i >= 0).
2. `_overlap_dual_joint_candidates(n, c)`: bounded deterministic vertex
   candidate enumeration, grouped by zero-pattern. Nonnegativity-active
   components are pinned to exact zero (a zero component is never lost
   to solve noise) and only the remaining square system is batch-solved
   with a determinant pre-filter and a per-row LinAlgError fallback.
   Only finite nonnegative exact-binary64 triples are proposed, deduped
   and sorted. The single-axis active sets are structurally among the
   enumerated subsets; finite-precision filtering may still drop
   individual proposals, and the joint stage runs only after the axis
   stage and max's in, so the combined result is never weaker.
3. `_overlap_dual_joint_weight_lower(n, c, weights)`: batched directed
   outward validation of constant three-component weights on all 20 joint
   controls, mirroring `_overlap_dual_coefficient_lower`'s subtraction
   order exactly (upper barycentric endpoints consumed, one ulp outward
   per operation). Nonfinite/overflowing rows validate to -inf.
4. `_overlap_dual_joint_lower(numerator, barycentric)`: elevates the cubic
   numerator, validates all control structure/finiteness conservatively,
   enumerates candidates, batch-validates, then revalidates the batched
   winner through the untouched gold-path
   `_overlap_dual_coefficient_lower` and adopts the smaller value.
   Returns (lower, checked) with the same shape as the axis function.
5. Call site in `matching_projection_swept_lower`: a joint stage runs ONLY
   when `overlap_dual` is on AND a finite threshold exists AND the box
   still refuses after the axis dual (`lower < -threshold`). Improvement
   path identical in form to the axis stage (min(0,joint)*p_upper/d_lower,
   outward). New additive diagnostics keys
   `dual_joint_candidates_checked`, `dual_joint_improved_boxes`.
   `_overlap_dual_numerator_lower` itself is untouched; budgetless dev
   calls and default-False paths are bit-unchanged.

### Why this is conservative

- One constant nonnegative triple applies to all 20 aligned time/spatial
  controls of the box (no coefficientwise choice; the existing
  counterexample is preserved by construction and by test).
- On the represented overlap u,v,w >= 0, so
  N - lU*u - lV*v - lW*w <= N there for any l >= 0; a directed lower
  bound of the combination over the whole box is therefore a lower bound
  on N over the overlap. Candidate generation is only proposal; the
  certificate is the directed validation, and the winner is revalidated
  a second time through the gold path.
- The joint result is only ever max'd into the existing box lower; boxes
  meeting the budget, pruned boxes, unresolved charts and default paths
  are unchanged.

### Cost estimate (unmeasured)

No timing was admitted in this phase; no measured cost exists. These
are explicit unmeasured estimates only. Per refusing terminal box:
8855 active sets, batched (one det + one solve per zero-pattern group),
estimated on the order of 10-20 ms typical, worst case bounded by the
unchanged node budget 1024 (estimated at up to roughly 20 s per
pathological pair sweep; the evidence 7/30 refusal had 43 nodes /
~11 terminal refusing boxes, so an estimated ~0.2 s per sweep there).
Boxes that certify via budget or the axis dual never pay it.

### Checks actually run

None. No test, solve, build, benchmark, import or interpreter execution
was admitted in this phase. Everything above is implemented but
unverified.

### Proposed exact checks (parent admission)

1. Focused unit/regression (serial, <1 GiB, minutes):
   `python -m pytest tests/test_general_contact_constrained_gap_joint_dual.py
   tests/test_general_contact_overlap_dual_certificate.py
   tests/test_general_contact_overlap_dual_integration.py
   tests/test_general_contact_adaptive_overlap_certificate.py -x -q`
2. Exact refusal-pair discriminator (the decision-changing check): rerun
   the saved exact 7/30 endpoint certificate with the joint-enabled
   candidate under the parent's evidence harness
   (`overlap-dual-start-reuse-v1` bindings), unchanged fixture/budgets.
   Discriminators: endpoint matching lower moves from
   -50.01322558144736 um; `dual_joint_improved_boxes > 0` on the refusing
   boxes; `dual_joint_candidates_checked > 0`; visited nodes and all
   previously-certified boxes unchanged.

### Outcome mapping (unchanged from H1)

- Joint certifies the endpoint (>= -50 um): refusal was numerator/box
  conservatism; endpoint admissible at unchanged mechanics/budgets.
- Joint improves but still refuses: remaining slack is the
  Cauchy-Schwarz ratio (R.Ns)/|Ns| <= |R|, the D/|P| enclosure slacks, or
  a genuinely deeper physical minimum; next decision is the box-aware
  cosine-enclosure route (needs a |Ns| lower bound via pairwise
  corner-normal quartics) or closure as possibly-physical.
- No joint improvement on the refusing boxes: a negative result for this
  candidate enumeration only; it does not prove the axis weights were
  LP-optimal there and does not rule out numerator slack; escalate with
  the (a)/(c) decomposition.

### Uncertainty

- Whether the 0.01322558144736 um shortfall is numerator slack (H1) or
  chart/Cauchy-Schwarz slack is not determinable without an admitted run.
  The implementation searches a bounded candidate set and independently
  revalidates each lower bound; it does not make the numerator
  certificate exactly LP-optimal per box, so a no-improvement outcome
  does not cleanly separate the two (it does not rule out numerator
  slack). A successful valid lower bound can still certify this
  represented overlap at unchanged controls.
- The synthetic tests were derived analytically (exact rational LP
  optima -2/3 vs -2 and -1) but have never executed; a first admitted
  pytest run may surface mechanical issues (shapes, numpy edge cases)
  that source review could not.
- `np.linalg.det/solve` are deterministic per build but not guaranteed
  identical across numpy versions; candidates are only proposals and the
  directed validation is the certificate, so cross-version differences
  cannot affect validity, only which proposals exist.

## Exact-pair guarded result (2026-10-10, attempt-03, admitted)

Command executed exactly as admitted, first action of the continuation after
identity inspection only:

  C:/Python/Python314/python.exe C:/ANYworkspaceWork/contact_mistral_constrained_gap_delivery_20261010/execution-v1/guard_v1.py C:/ANYworkspaceWork/contact_mistral_constrained_gap_delivery_20261010/execution-v1/job-exact-pair-v1.json ADOPTED_FREEZE_PAIR_V1.json

Guard verdict: pass, exit 0. Guard stdout (exact):
`{"stage": "d1-constrained-joint-exact-pair-v1", "status": "pass", "process_wall_s": 8.029802400007611, "peak_process_tree_rss_mib": 183.60546875, "remaining_after_s": 223.6901707999932}`.
Child stdout (exact):
`{"status": "PAIR_DISCRIMINATOR_COMPLETE_NO_ACCEPTANCE", "discriminator": "EXACT_PAIR_CERTIFIED", "lower_m": -4.822737260501268e-05, "checks": 6}`.
Child stderr: empty. Saved result:
`execution-v1/results/exact-pair-v1.json` (also mirrored in
`execution-v1/attempt-03-d1-constrained-joint-exact-pair-v1/result.json`).

### Discriminator and bounds

- Status: `PAIR_DISCRIMINATOR_COMPLETE_NO_ACCEPTANCE`;
  discriminator: `EXACT_PAIR_CERTIFIED`. All six recorded checks true:
  exact_archived_pair_and_endpoint, unchanged_model_and_settings,
  inputs_and_work_map_unchanged, monotone_candidate_bound, context_restored,
  no_equilibrium_solve. Kernel sha256
  `d1f4c16cd11d5746f55433923a631a37d572b19cbee256040f313a6b2770d5e6`,
  method revision `constant_nonnegative_joint_bernstein_overlap_dual_v2`.
- Exact archived pair bound: source face 6 / element 7, target face 13 /
  element 30 (the exact 7/30 pair), two literal poses.
- Archived conservative refused lower: -5.001322558144736e-05 m
  (-50.01322558144736 um).
- `current_start` pose certified lower: -4.8167667247676126e-05 m
  (-48.167667247676 um) — above the -50 um budget by ~1.846 um.
- `closest_refused_endpoint` pose certified lower:
  -4.822737260501268e-05 m (-48.227372605013 um) — above the -50 um
  budget by ~1.773 um.
- Both endpoint poses now certify at the unchanged 50 um / depth 7 /
  node 1024 settings. Per the H1 outcome mapping, the prior refusal on
  this exact pair is attributable to numerator/box conservatism that the
  joint dual recovers. This is a represented-pair gap-budget certificate
  only: no whole-pose, path, or equilibrium admission is claimed, and no
  optimizer-completeness claim is made (the enumeration is a bounded
  proposal set, not exact LP optimality per box).

### Actual candidate counts and runtime

Per-pose diagnostics (both: initial_depth 3, maximum_depth 7, node_budget
1024, node_budget_exhausted false, depth_exhausted false,
unresolved_chart false, unresolved_leaf_count 0,
represented_pair_certified true):

- `current_start`: visited_nodes 21, dual_candidates_checked 234,
  dual_improved_boxes 3, dual_joint_candidates_checked 839,
  dual_joint_improved_boxes 2, span_s 0.03998279999359511.
- `closest_refused_endpoint`: visited_nodes 21, dual_candidates_checked
  237, dual_improved_boxes 3, dual_joint_candidates_checked 847,
  dual_joint_improved_boxes 2, span_s 0.03869989998929668.

`dual_joint_candidates_checked > 0` and `dual_joint_improved_boxes > 0`
fired as proposed. The archived axis-only run visited 43 nodes; the
joint-enabled candidate visits 21, consistent with earlier pruning from
the stronger lower bound. Guard-measured elapsed 8.029802400007611 s
wall, peak process-tree RSS 183.60546875 MiB against the 60 s / 953 MiB
job cap. Ledger after the job: used_s 76.30982920000679 of limit 300,
reserve 30 retained, 3 numerical jobs, one at a time, scope
D1_CONSTRAINED_GAP_JOINT_DEV300_V1 still OPEN.

### Proof limitations

- Two exact archived pair endpoint certificates only; the scope string in
  the result is explicit: no whole-pose/path or equilibrium admission.
- The certified lower proves the represented-pair gap budget only. It does
  not prove the candidate is LP-optimal per box, does not extend to other
  pairs/poses, and (had it refused) would not have proven physical
  penetration or infeasibility.
- Single process, single run, fixed runtime (Python 3.14, OpenBLAS
  single-threaded, JIT disabled per the saved runtime.json); no pooling.

### Focused coverage gap (open)

The focused pytest stage (`d1-constrained-joint-focused-v1`, attempt-02)
ended TIMEOUT at 45.0535024 s after 48 anonymous pass markers, with no
terminal XML/result or case identities and no mechanics failure reported.
That consumed stage is preserved as-is: not replayed, and which named
checks passed cannot be concluded from the dots. Focused unit/regression
coverage of the joint dual therefore remains unverified; the parent will
provide the specific split-check admission needed to finish verification.
No further product edits or numerical jobs were made in this
continuation.


## Parent ownership reconciliation

The units-run narrative was appended to the protected raw source-phase snapshot in error. Parent recovered its exact original prefix/hash, preserved the mutated copy separately, and moved the appended run narrative here. Numerical source, inputs and results were unchanged.

## Parent-admitted verification run, 2026-10-10 (guard_v2, this owner)

Stage 1 `d1-constrained-joint-units-v2` (exact admitted command, 45 s /
953 MiB cap) ran to guard status `nonpass` in 9.0718 s wall / 191.65 MiB
peak RSS, no timeout. Cause: pytest INTERNALERROR from the harness
reporting hook `save()` — `PermissionError [WinError 5]` on
`os.replace` of the state file while saving the setup report of
collected case #16
(`test_analytical_cut_improves_without_changing_parent_ray`). No test
assertion failed: 47/47 collected, 15 completed all passed (inventory
IDs 1-15), 0 failures, 1 harness error; 31 cases unrun. Full inventory,
46 persisted reports and active_case are preserved in
`execution-v1/results/units-v2.json` (+ `units-v2.xml`); guard record in
`execution-v1/attempt-04-d1-constrained-joint-units-v2/`. Stage 2
(`d1-constrained-joint-identity-v2`) was NOT launched per the serial
PASS-gate/stop rule; its 60 s cap is unspent. Guard-reported remaining
balance 214.6184 s of the 300 s combined cap (ledger: 76.3098 + 9.0718 =
85.3816 s used). Short actionable handoff saved as
`HANDOFF_UNITS_V2_NONPASS.md` (suggested repair: rerun stage 1 unchanged;
save-path hardening is a parent-owned freeze decision). This section is a
same-owner run record, not an independent assessment. The joint-dual
kernel/caller implementation therefore remains verified only on the 15
executed unit cases; whole-path, equilibrium and acceptance limits below
are unchanged and still open.
