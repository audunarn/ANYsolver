# Nonlinear static solver speed

Living task note for the constant-time guard work. History: branch
`solver_speed_claude` (2026-09-29), follow-up review fixes on `main`
(2026-09-30). This is a development record; it is not an acceptance record.

## Question and evidence

Why is a warm nonlinear static solve of a small quad-first plate/cylinder model
(449 nodes, 396 qualified Q4 + 52 S3 V2D elements, 11 increments, 36 Newton
iterations, load factor 1000) 22-26 s, and what can be removed without changing
results or the qualification claim?

Stack-sampling attribution of one warm solve before the change (4 ms sampler,
attributed to the outermost guard entry point; cProfile over-states pure-Python
guard code):

| Layer | Share |
|---|---|
| Complete lifecycle scan (`exact_guard`, raw part) | 24 % |
| Lease `require` inside `exact_guard` | 8 % |
| Q4 component-cache binding | 15 % |
| V2D state validation (`_state_identity` recomputes geometry) | 13 % |
| V2D state seal/validate hashing | 5 % |
| Mechanics and driver | 27 % |
| Sparse factorisation and solve | 7 % |

A first solve in a new process additionally spent about 12-14 s compiling Numba
kernels that had no on-disk cache.

## Design as merged

1. **Numba disk cache by default.** `anysolver.jit_compiler.njit`/`jit` pass
   `cache=True` unless the caller supplies `cache`. All 51 kernels are cached
   (36 before). The default lives in the wrapper, not on each kernel, because
   `elements.py`, `plasticity.py` and `vectorized_nonlinear.py` are byte-pinned
   by frozen evidence (see Review history) and stay identical to 0.4.7.
2. **Cancellation-token trust.** An absent token, or an exact unmodified
   `CancellationToken` (class, event, instance data and checkpoint function all
   unchanged), lets the checkpoint use the constant-time guard. The token is
   verified **before** its code runs and again after. Verifying only afterwards
   let a token repair itself inside the checkpoint and still be trusted. Any
   other token keeps the complete scan.
3. **S3 V2D trusted path.** For models that own Q4/S3 and V2D elements the
   trusted check is: the lease's trusted state check (owned inputs, mesh epoch,
   Q4/S3/assembly epochs; exposed as `_qualified_trusted_state_require`), the
   V2D class epoch (`AuthorityEpochMeta`, protected `__setattr__`/
   `__delattr__`), a re-run of the unchanged exact lifecycle guard on one
   representative V2D element (re-validates the whole formulation-level
   authority), and a **private write counter** per capture. The capture
   subscribes the counter to every V2D element through weak references; any
   ordinary attribute write or deletion on a subscribed element advances it,
   under a lock, so concurrent writers neither lose nor reject each other's
   advance. Eligibility requires every observed instance value to be immutable;
   otherwise the complete scan remains. The counter exists only while a capture
   is live: V2D writes outside a solve behave exactly as before and the shared
   mesh epoch is never touched.
4. **Reporting.** `info["nonlinear_performance"]["solver"]["event_counts"]`
   carries `qualified_guard_trusted`, `qualified_guard_complete_scan`,
   `qualified_guard_untrusted_token` and `qualified_v2d_trusted_unavailable`,
   so a solve that could not use the constant-time path is visible.

## Not covered

- Models made only of V2D triangles get no fast path: the lease's owned-input
  plan needs at least one Q4 or S3 element. Nothing is reported for that case.
- `object.__setattr__`, direct `__dict__` writes and code surgery remain outside
  the supported mutation surface. Complete scans still catch a persistent change
  at each callback boundary and at the end of an increment, not mutate-use-
  restore inside a trusted window.
- Modal, buckling, transient, recovery and arc-length analyses are unchanged.

## Behaviour change

Modifying an S3 V2D element while a nonlinear static solve owns it now stops the
solve with an authority error. Before, a harmless-looking write such as a new
thickness was silently used. Writes before or after a solve are unchanged.

## Results (plate/cylinder case, load factor 1000, idle machine)

| Run | parent (0.4.7) | this change |
|---|---|---|
| First solve in a new process | 38.5 s | 12.0 s |
| Warm, no token | 23.7 s | 11.7 s |
| Warm, solver token | 22.4 s | 11.7 s |
| GUI-style (ANYfem wrapper, progress callbacks, token, sampler attached) | 31.7 s, 290 complete scans | 15.1 s, 94 complete scans |

Displacements and step load factors are bit-identical to the parent: default,
token and no-token runs; 14 solver-option combinations (imperfection failure
mode, fracture, corotational, load programs, displacement control with a nested
preload stage, restart checkpoints, snapshots, convergence settings); linear
static, modal, transient and arc-length runs on the same mixed model.

The trusted V2D check itself costs about 0.4 ms per call, 0.6 % of the solve.

## Review history

- `14ce5284` first commit. Reviewed in the same session (a self-review, not an
  independent acceptance). It fixed a hostile event flag being accepted as a
  known token, and added tests that turned out to be weaker than they looked.
- Second review (same session, wider evidence: all 882 test files compared
  against the parent). Findings and fixes:
  - The known-token check ran after the checkpoint had executed the token's code,
    so a token that restored its own `_flag` was trusted and could plant an
    override that the skipped complete scan would have caught (V2D and Q4-only
    models). Fixed by verifying before and after; two mutation tests cover it.
  - `docs/agent_plans/SOLVER_SPEED_CLAUDE.md` raised the file count that
    `test_release_046_bounded` asserts (CI shard 5). This note now lives in
    `docs/`.
  - The 15 `@njit(cache=True)` edits changed `elements.py`, which GE-beam3 audit
    and runner scripts bind by SHA-256 (seven tests). Reverted; the default moved
    to `jit_compiler`.
  - The V2D write hook advanced the shared mesh epoch, which the GE-beam3 M_S3
    reference owner also reads, so three of its frozen tests hit a different
    guard first; it also raced (`ValueError: qualified mutation epoch can only
    advance by one`, lost writes) when two threads wrote different V2D elements.
    Replaced by the private per-capture counter above.
  - Mutation tests injected from status callbacks, which are always followed by
    a complete scan, so three of four passed with the hook removed. Injection now
    happens inside a trusted window; both a counting-disabled mutant and an
    after-only-token mutant are caught.
  - The cache test failed under `NUMBA_DISABLE_JIT=1`; it now skips.
  - Fast-path fallbacks were silent; now reported (see Design 4). Added a
    CHANGELOG entry.
- Lesson: the byte-pin evidence is pervasive (128 files mention `elements.py`).
  A keyword-selected subset of the suite missed eleven newly failing tests;
  changes to these modules need the full-suite comparison.

## C and D investigation

Remaining complete scans in a GUI-style run (94): 36 after status callbacks, 11
after progress callbacks, 11 progress-state observations, 11 support reactions
and about 20 one-off setup and final checks.

- **C (complete scans only at increment commit and solve boundaries).** Removes
  the per-callback scans, about 12 % of a GUI-style run and about 0 % without
  callbacks. Cost: a caller callback could mutate and restore authority inside an
  increment undetected, which changes the documented rule that caller-controlled
  boundaries are complete-guard boundaries. Not recommended; a status-callback
  interval would keep the guarantee.
- **D (unguarded mode).** Measured ceiling about 18-25 % in GUI-style runs. The
  Q4 component-cache and V2D state validation protect result correctness, not
  code identity, so they must stay. Results could no longer claim qualification
  and a second code path would be needed. Not recommended.
- Larger remaining costs: Q4 component-cache binding (about 15 %, in blob-pinned
  `e4_pl_element.py`) and V2D `_state_identity` recomputing element geometry
  (8-13 %). Both need their own correctness review.

## Exact beams beside qualified shells: investigated, not adopted

Branch `solver_speed_beams` (commit `809fa521`, never merged, 2026-09-30) let
exact `BeamElement` stiffeners use the lease's trusted state check
(`_qualified_trusted_state_require`) inside the Newton loop, on the reasoning
that the complete lifecycle scan does not observe generic elements. The
independent review found it fail-open, and it stays parked.

- **The premise was wrong.** The Q4/S3 dependency authority freezes every
  callable and every class namespace of the whole `anysolver.elements` module,
  `BeamElement` included, and the scan re-checks them on each call. Patching a
  `BeamElement` method before a solve makes the preflight raise
  `DEPENDENCY_AUTHORITY_MISMATCH=anysolver.elements.BeamElement...`.
- **The trusted state check documents its own limit.** It validates owned
  inputs, the mesh token and the Q4/S3/assembly epochs, "says nothing about any
  other element family, which the caller must cover with its own authority"
  (`trusted_require` in `matrix_assembly.py`). Beam code, the `BeamElement`
  class and the code reachable from beam evaluation have no such authority. The
  V2D path is admitted only because everything that runs in its window is
  authority-guarded.
- **Demonstrated on the parent and on the branch** (2 Q4 shells, 3 exact beams,
  one beam with an instance-level method override that runs inside the Newton
  loop):

  | Hostile action inside the loop | Parent | Branch |
  |---|---|---|
  | `object.__setattr__` overrides planted on a Q4, left in place | rejected at the next guard | rejected only at the later support-reactions scan, two assemblies later |
  | same, removed one beam call later | rejected at the next guard | solve completes, no error |
  | `BeamElement` class attribute added, left in place | rejected at the next guard | rejected only at the support-reactions scan |
  | same, deleted one beam call later | rejected at the next guard | solve completes, no error |

  No result changed in these runs; they show missed detection, not a wrong
  answer. Scripts: `beam_hostile2.py` (scratch, not kept).
- **Sound variants measured** (12-plate stiffened synthetic model, warm
  nonlinear solve, idle machine; parent 8.3-8.9 s):

  | Variant | Time | Change |
  |---|---|---|
  | Unsafe branch as written | 5.45-6.4 s | -34 % |
  | Complete scan after every element-executing call (assembly, external load, commit, reaction sites), trusted elsewhere | 7.9 s | -7 % |

  The second variant needs no element-type allowlist and is sound by
  construction, but the gain is small: the external-load assembly can also run
  generic code, so only the cancellation checkpoints stay trusted.
- **A per-family beam authority** (re-verify the `elements` class namespaces per
  call, decline on beam instance shadows, strict data-type eligibility) closes
  the demonstrated attacks but cannot be argued closed: the code reachable from
  beam evaluation is not a bounded set the way the Q4/S3 dependency list is.
- **Reach.** ANYfem's default stiffener mode (`offset_mode="automatic"`) adds
  `CoupledBeamShellElement` (and `InterpolatedBeamShellMPCElement` for
  interpolated attachments). Those are not admitted, so the default offset
  stiffened models would have kept the complete scan (events:
  `qualified_guard_complete_scan: 36`, against `qualified_guard_trusted: 30`
  for `centerline`).
- **Decision (owner, 2026-09-30):** leave parked. The guard-cost work continues
  on the scan itself, which is sound for every element mix (recorded in this note when it lands).

## Governance

- The runtime-guard performance successor record (as in
  `tests/test_s3_v2d_default_activation.py`) is not created here: it needs an
  independent reviewer's outcome.
- Files changed relative to 0.4.7: `jit_compiler.py`, `nonlinear_static.py`,
  `matrix_assembly.py`, `current_state_tangent.py`, `e4_pl_s3_v2d_element.py`.
  `jit_compiler.py` appears in `scripts/release_043_runtime.json` and a GE-beam3
  manifest; no currently passing test validates those bytes (full-suite
  comparison). `e4_pl_element.py` and `e4_pl_s3_element.py` are untouched and
  their blobs are live-pinned by the runtime-guard successor record.

## Status

- [x] Numba cache default
- [x] Token trust, verified before and after the checkpoint
- [x] S3 V2D trusted path with private write counters
- [x] Guard-path reporting
- [x] C and D investigated (not adopted)
- [x] Review findings fixed; full-suite comparison against the parent
- [x] Exact built-in beams on the trusted state check: investigated, fail-open, not adopted
- [ ] Runtime-guard performance successor record with an independent reviewer
