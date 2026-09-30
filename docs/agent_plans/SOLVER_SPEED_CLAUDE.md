# Nonlinear static solver speed (branch `solver_speed_claude`)

Living task note. Owner decision (2026-09-29): implement A + B + E and the
Numba compile cache; investigate C and D.

## Question and evidence

Why is a warm nonlinear static solve of a small quad-first plate/cylinder
model (449 nodes, 396 qualified Q4 + 52 S3 V2D, 11 increments, 36 Newton
iterations, load factor 1000) 22-26 s, and what can be removed without
changing results or the qualification claim?

Stack-sampling attribution of one warm solve (4 ms sampler, attributed to the
outermost guard entry point; cProfile over-states pure-Python guard code):

| Layer | Share |
|---|---|
| Full lifecycle scan (`exact_guard` raw part) | 24 % |
| Lease `require` inside `exact_guard` | 8 % |
| Q4 component-cache binding | 15 % |
| V2D state validation (`_state_identity` recomputes geometry) | 13 % |
| V2D state seal/validate hashing | 5 % |
| Mechanics and driver | 27 % |
| Sparse factorisation/solve | 7 % |
| Q4 per-call class guard outside the scans (E) | 0.5 % |

First solve in a process additionally spends about 12.6 s compiling Numba
kernels (no `cache=True`).

## Scope decisions

- **Numba cache**: default `cache=True` in `jit_compiler.njit/jit`.
- **B**: an exact, unmodified `anysolver.control.CancellationToken` is a
  known checkpoint; foreign or modified tokens keep the full scan.
- **A**: S3 V2D elements join the nonlinear-static constant-time trusted path.
  Design: no V2D epoch manager and no metaclass change. The trusted check
  re-runs the V2D *family-level* part of the exact scan (modules, data
  signatures, dependency modules, class namespaces, base/critical APIs; cost
  independent of element count) and replaces the per-element instance part
  with the mesh mutation token, bumped by a new V2D `__setattr__`/`__delattr__`
  hook. Eligibility requires every V2D instance value to be immutable at
  capture; otherwise the full scan remains. Exposed as a separate lease
  attribute consumed only by nonlinear static, so modal/buckling/recovery
  behaviour is unchanged.
- **E dropped**: `formulation_class_guard` re-compares namespaces of plain
  `type` base classes (e.g. `ShellElement`) that the epoch mechanism cannot
  observe; it is their only per-call check, and its standalone cost is 0.5 %.

## Acceptance

- Bitwise-identical displacements, load factors and step history against
  `main` on the plate/cylinder case (token and no-token).
- Tamper tests: V2D instance write, V2D class/module mutation, foreign token,
  modified token class all fall back or fail closed exactly as before.
- Existing guard/lease/epoch/authority suites pass.

## Implementation notes

- A is paired with the lease through a new lease attribute,
  `_qualified_trusted_state_require` (the unchanged trusted-loop state check,
  now also exposed for mixed models). `_qualified_trusted_require` keeps its
  all-Q4/S3 installation rule, so modal, buckling and recovery are unchanged.
- V2D class now uses `AuthorityEpochMeta`; `__setattr__`/`__delattr__` are
  protected entries and the class is watched by
  `_s3_v2d_runtime_epoch_manager`, so a swap-and-restore of any V2D class
  member between trusted checks is rejected (stronger than the complete scan,
  which only sees the state at each scan instant).
- Behaviour change: an ordinary write to a bound V2D instance during a solve
  now advances the mesh epoch and fails the lease, as Q4 already does. Before,
  a benign write (e.g. `thickness`) mid-solve was silently used.
- Trusted V2D path needs at least one Q4/S3 element (the lease's owned-input
  plan requires one). All-triangle V2D models keep the complete scan.
- `e4_pl_element.py` and `e4_pl_s3_element.py` are untouched; their git blobs
  are live-pinned by the qualified-shell runtime-guard successor record.

## Results (plate/cylinder, load factor 1000)

Bitwise identical displacements and step load factors to `main` in cold,
warm, token and no-token runs.

Idle machine, 2026-09-29:

| Run | `main` | branch |
|---|---|---|
| First solve in a new process | 38.5 s | 12.9 s |
| Warm, no token | 23.7 s | 12.4 s |
| Warm, solver token | 22.4 s | 12.6 s |
| GUI-like (ANYfem progress + token, stack sampler attached) | 31.7 s, 290 complete scans | 17.6 s, 94 complete scans |

## Tests

158 affected test files (3,339 tests: nonlinear statics, V2D, lease/trusted
paths, epochs, cancellation, authority/manifest pins) plus the new
`tests/test_nonlinear_trusted_v2d_and_token.py` (19 tests). 28 failures, all
also failing on `main` with identical error lines (S3 default now V2D vs
frozen `legacy-s3` contract assertions, burn-in inventory/PowerShell identity,
V6H frozen V2D source already changed on `main`, GE-beam3 cutback/line
program). The only difference is the burn-in test-file count (590 vs 589),
from the new test file, in a test already failing on `main`.

## C and D investigation

Remaining complete scans in a GUI-like run (94): 36 after status callbacks,
11 after progress callbacks, 11 progress-state observations, 11 support
reactions, about 20 one-off setup/final checks. Each costs about 49 ms
(31 ms scan, 18 ms lease re-check) at 448 elements.

- **C (complete scans only at increment commit and solve boundaries).**
  Removes the per-callback scans: about 2.8 s (12 %) of the GUI-like run,
  about 0 % without callbacks. Cost: a caller callback could mutate and
  restore authority within an increment undetected; the documented
  "every caller-controlled boundary is a complete-guard boundary" rule and
  tests such as `test_nonlinear_status_callback_is_not_truth_tested_and_keeps_lease`
  would change. Not recommended: small gain for a guarantee change.
  Cheaper alternative that keeps the guarantee: an opt-in status-callback
  interval (callbacks at most every N s), which reduces scans in proportion.
- **D (unguarded mode).** Measured ceiling with the raw scan replaced by a
  no-op: GUI-like 23.6 s to 19.3 s (18 %); lease re-check adds about 1.5 s
  more. Q4 component-cache provenance (15 %) and V2D state validation (8 %)
  protect result correctness (stale caches, state/element binding), not code
  identity, so an unguarded mode must not remove them. Cost: results cannot
  claim qualification, a second code path and label. Not recommended.
- **Next real opportunities (outside A/B/E):** Q4 component-cache binding
  (15-19 %, in blob-pinned `e4_pl_element.py`) and V2D `_state_identity`
  recomputing element geometry on every validation (8-13 %). Both need their
  own correctness review; neither is a guard-policy question.

## Independent review (2026-09-30)

High-effort review of the full diff, focused on fail-open risks. Nine
findings; all others were checked empirically before being reported.

Fixed:
- A token whose event `_flag` was replaced by a hostile object (code in
  `__bool__`) was accepted as the solver's own token and its code ran at each
  checkpoint with the full scan skipped. The check now requires an exact
  `bool` flag and `threading.Condition` cond.
- The V2D capture declined only on `ElementCapabilityError`; it now also
  declines on AttributeError/TypeError/ValueError so the preflight reports.
- Stale `trusted_require` docstring now states its mixed-model scope.
- No test mutated a non-representative V2D element. Added four (callable
  override, thickness write, class swap, mapping replace) plus a hostile-flag
  token case and a two-V2D clean-solve check. The mutation cases fail closed.

Verified, no change needed: derived-cache exemption is inert (garbage or
`None` in `_stiffness_matrix` leaves the result bit-identical); the three
newly cached modules contain no cross-file jit calls, so Numba's per-file
cache invalidation adds no staleness risk.

Skipped (documented limitations or low value):
- All-V2D meshes get no fast path (the lease's owned-input plan needs a
  Q4/S3 anchor). Affects unstructured triangle meshes; worth a follow-up
  that admits V2D into the owned-input plan.
- Token-advance loop duplicated from Q4/S3 (those files are blob-pinned).
- Token trust depends on `threading.Event` private attributes; a change
  degrades to full scans (safe).
- Per-checkpoint namespace comparison cost and two probe classes that could
  be `SimpleNamespace`.

Final-code retest: orchestrator lease (39), epoch/guarded-observation/
control/nonlinear-static suites (108), V2D closeouts (49), cache, eigen and
provenance suites (59 of 61; the 2 failures are among the 18 that fail on
`main`), new tests (25).

## Governance

Precedent: `qualified shell runtime guard performance successor` record
(tested in `tests/test_s3_v2d_default_activation.py`) documents a runtime-
guard performance change with changed blobs, a qualification boundary,
review outcome and validation. A comparable record for this branch needs an
independent review outcome; it is not created here.

## Status

- [x] Numba cache
- [x] B
- [x] A
- [x] C investigation
- [x] D investigation
- [x] Affected suites (158 files) on branch; failures re-run on `main`
- [x] Independent review; fixes applied
- [x] Commit; merged to `main` (not pushed)
- [ ] Optional successor record (runtime-guard performance) signed by an independent reviewer
