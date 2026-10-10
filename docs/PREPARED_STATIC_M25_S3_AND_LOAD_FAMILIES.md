# M25 — S3 trusted-scope capture and barge load families

2026-10-09. Owner: Claude (Anthropic). Request: "Implement S3 and pass
load_families, then benchmark". Pre-M25 comparator: `../../m25-baseline`.
Not merged, committed or published.

Terminology: in this report "S3" means review item S3, the **trusted capture**
(capturing per-element recovery recipes inside the native trusted operation
scope). The three-node qualified shell element (`QualifiedE4PLS3ShellElement`) is
written "S3 element". The S3 element is fully supported in every mode.

**Final state (M25f, owner decision): the trusted capture is opt-in.** The solver
option `trusted_capture` (default `False`) on `prepare_static_evaluator` and
`prepare_static_response_evaluator`, also accepted by the ANYfem factories,
enables it; by default every recipe is captured with full per-call guards, exactly
as before M25. See "Decision: opt-in (M25f)" below.

## S3: capture under the native trusted operation scope

`_capture_owned_local_recovery` (prepared_static_recovery.py) runs its native calls
on the freshly cloned private element (pressure warm-up, Q4 stage compile, native
zero-displacement warm-up) inside the pinned native trusted operation scope, but
only when the span is admitted. As revised after the M25 review (section "Review
and fixes" below):

- Only exact Q4/S3 clones are considered; beams and other elements keep the
  per-call guarded route with no scope check, as before M25.
- Before admission the capture authenticates its span helpers and the proof
  functions (code and global bindings) and the scope-factory tables; a change is
  refused (PreparedStaticCapabilityError).
- The span is admitted only when the proofs that
  `boundary._run_foreign_code_free_load_vector` uses for its own trusted span hold
  (builtin NumPy error and warning routes, untouched model/mesh/node routing
  classes, an exact `LoadCase` for the pressure probe) and the element's material
  and section pass native authority; otherwise the capture keeps the per-call
  guarded route (pre-M25 behaviour). Q4 kernel authority is checked before entry.
- The factory checks the element's runtime authority at entry and exit; inside,
  guarded calls on that element take the native trusted path. After the span the
  admission proofs are re-checked and a change is refused.

This is not the full check set of `owned_recovery_scope` (which also re-runs the
native source-authority check, tens of milliseconds, unaffordable per capture);
it is the boundary's own admission policy for constant-time trusted spans. Nothing
in the pinned element modules changed, and no numerical path changed.

Effect on one capture (cProfile counts, same element, pre-M25 versus M25):

| Capture | Boundary guards before | after | Untrusted post-observation guards after |
|---|---:|---:|---:|
| Q4 with stage compile | 107 | 9 | 0 (92 trusted) |
| Q4 pressure-only recipe | 30 | 2 | 0 (28 trusted) |
| S3 with warm-up | 193 | 10 | 0 (169 trusted) |
| S3 pressure-only recipe | 48 | 2 | 0 (42 trusted) |

The model's own elements (assembly, oracle load verification) are outside S3 and
keep their per-call guards.

## load_families for the barge workflow

No product change. The barge project has no gravity, masses or acceleration
loads, so the M25 screen passes `load_families=("nodal", "element", "pressure")`
through the existing ANYfem factory option; acceleration mass capture is skipped.
A request that needs acceleration is refused by the existing family check. Product
defaults keep all four families.

## Verification (M25 as first implemented)

- Cross-version probe `../../evidence/m25_digest_probe.py` (M21 probe plus the
  pressure-only recipes, their retained bytes and exact pressure load vectors):
  pre-M25 and M25 JSON byte-identical (`m25-digest-baseline.json`,
  `m25-digest-s3.json`).
- New tests `tests/test_prepared_static_response_m25.py`: the trusted path is
  taken during capture for Q4 and S3, full and pressure-only (no untrusted
  post-observation guard; the scope ends with the capture); a rebound scope
  factory is refused before it runs; frozen C1-C8 lean holdouts A1-L, A3-L, A5-L,
  A4 GO (`m25-assessment-01.json`). 7 passed.
- Regression: M20/M21/M22/M24, Q4, pressure verification, mass capture,
  accounting cache and independent suites 61 of 62; the one failure is the M24
  assessment test refusing to overwrite its preserved evidence file (assessment
  itself ran; re-run as the M25 assessment). Base prepared-static suites 112 of
  115, the three known pre-existing authority-test failures. ANYfem 16 of 16.
  Checks 112.25 of 150 s (m25-digest-baseline, m25-digest-s3, m25-claude-01 to -04).

## Barge benchmark (M25 as first implemented, epoch m25, 1,230.74 of 1,500 s)

Matched cold processes, 300 cases each, lean consumed output, block 4, 2048 MiB,
primary at even and holdout at odd saved positions; both routes run with
`load_families=nodal,element,pressure`. Vectorized runs use
`selected_reaction_diagnostics="lean"`.

| 300-case history | Primary vectorized | Primary canonical | Holdout vectorized | Holdout canonical |
|---|---:|---:|---:|---:|
| Built model to consumed output | 82.0 s | 529.1 s | 78.1 s | 531.3 s |
| Preparation | 63.2 s | 54.0 s | 59.3 s | 51.3 s |
| Case evaluation | 15.0 s | 471.4 s | 15.0 s | 476.1 s |
| Load evaluation phase | 2.2 s | 78.7 s | 2.3 s | 80.1 s |
| Recovery phase | 5.0 s | 378.3 s | 5.1 s | 381.6 s |
| Peak RSS | 1,124 MiB | 1,114 MiB | 1,123 MiB | 1,113 MiB |

**Complete-workload ratio 6.46x primary and 6.80x holdout**, against a same-session
canonical comparator (M24 5.61x / 5.31x against the M22 canonical runs; M22 4.23x /
4.37x). Case evaluation is about 31.5x faster.

Preparation, vectorized lean primary, M24 to M25 (progress events):

| Preparation phase | M24 | M25 | Cause |
|---|---:|---:|---|
| Load maps (pressure recipes, mass capture) | 25.4 s | 13.7 s | S3 on pressure-only captures and skipped acceleration mass capture, not separated |
| Recovery recipes (warm-ups, Q4 stage compile) | 26.9 s | 13.2 s | S3 alone |
| Vector recovery build after factorization | 20.5 s | 20.9 s | unchanged |
| Whole preparation | 86.5 s | 63.2 s | |

Holdout preparation 88.7 to 59.3 s. Canonical preparation fell from 89.0 / 79.4 s
(M22) to 54.0 / 51.3 s because the canonical route captures the same recipes. Peak
memory fell by about 70 MiB on both routes (no mass maps retained). Canonical case
evaluation was about 5% faster than M22 with byte-identical outputs, so part of the
canonical change is machine drift.

Output identity: the M25 vectorized lean histories and whole-model envelopes are
byte-identical to M24 lean (primary and holdout), and the M25 canonical outputs
are byte-identical to M22 canonical, so S3 and the family restriction change no
output. All 600 vectorized cases reconstructed with no fallback (worst source
ratio 5.2e-15). Differences against canonical are unchanged: displacement 6.0e-13
/ 5.5e-13 of maximum, selected stresses 1.5e-11 / 1.4e-11 of element maximum,
envelope values 7.3e-10 / 6.6e-10 of entity maximum, reactions identical, and
43,518 / 46,001 same-phase tie identity differences as before. Evidence:
`../../evidence/m25-analysis.json`; runs m25-primary-lean 84.52 s,
m25-holdout-lean 80.55 s, m25-primary-canonical 531.75 s, m25-holdout-canonical
533.92 s.

Per case the vectorized route now costs about 0.05 s and preparation is about 77%
of a 300-case run. Projection only: 10,000 cases about 9.5 minutes vectorized
versus about 4.4 hours canonical.

## Review and fixes (M25b)

Review of the M25 change by Claude with Codex CLI (gpt-6-astra, max effort,
read-only) as independent reviewer: 12 findings, two authority regressions
reproduced (a substituted pressure helper and a foreign NumPy error handler both
ran inside the trusted span). Fixes as described in the S3 section; evidence:

- v2 probe (`../../evidence/m25_digest_probe_v2.py`, adds a warped Q4 model and
  recipe-state digests): pre-M25 and fixed JSON byte-identical.
- Tests: M25 26 tests including trusted-versus-guarded identity for six capture
  kinds and fresh-process retained bytes; regression 88 of 88; base suites 112 of
  115 (the three known pre-existing failures, same messages); ANYfem 16 of 16;
  one-shot assessment `m25-assessment-02.json` GO. Both reproductions now take the
  guarded route. Checks 119.13 of 200 s.
- Barge (epoch m25b, 1,283.45 of 1,500 s): lean 81.6 / 83.5 s, preparation 62.2 /
  62.9 s (within noise of M25); canonical 544.7 / 562.8 s; outputs byte-identical
  to M24 lean and M22 canonical. Ratios 6.68x / 6.74x, but the Codex re-review ran
  during the canonical runs, so the M25 ratios (6.46x / 6.80x) remain the clean
  speed figures. Evidence `../../evidence/m25b-analysis.json`.

Codex re-review of the fixes (`../../evidence/m25-review/fixes/codex-review-fixes.md`):
findings 6, 8, 10, 11, 12 fixed; 1, 2, 3, 4, 5, 7, 9 partially fixed. Open:

1. BLOCKER: the material proof runs last and can execute foreign code
   (`model.materials` may be a `_QualifiedStateMapping` with an instance `get`,
   which preparation does not reject), after the NumPy and LoadCase proofs passed.
   Premise verified by code reading; not reproduced.
2. `_CAPTURE_SPAN_FACTS` is a plain module binding; rebinding it to `()` makes the
   helper authentication vacuous on the load-map and affine-capture paths.
3. The one-shot assessment file is collected by pytest, so full-suite reruns fail
   (same convention as the M16-M23 assessment files).
4. `pressure_probe` and `warm_stress` are not proven plain before entry (callers
   pass constants).
5. The identity fingerprint does not traverse the cloned mesh and material, and
   pressure-only cases compare no output.
6. The exception test does not prove revocation of a failed clone's lease or
   cancellation behaviour.

### Second round of fixes (M25c)

1. Material proof (blocker, reproduced on the M25b source by
   `../../evidence/m25-review/fixes/m25_material_toctou.py`): the proof now runs on
   the private clones and calls no mapping or attribute provider: exact reviewed
   elastic material class whose class executables equal the import-time facts,
   plain instance data without executable shadows, exact plain sections read from
   the clone's namespace. Proof order: plain arguments, material, routing
   classes, LoadCase, NumPy routes last. Admission calls no `model.materials`
   method; a substitute planted earlier (by `get_material`) is caught by the
   LoadCase proof.
2. Authentication root: the facts (capture function, admission helpers, proof
   functions, `compile_affine_recovery`, the boundary/loads/static_batch helpers,
   with code and global bindings) live only in a closure; the checker verifies its
   own binding and code; capture calls the import-time checker held as a private
   keyword default, so rebinding the module name or `_CAPTURE_SPAN_FACTS` has no
   effect; every capture caller (load maps, affine recovery compile, envelope
   plan) runs the check before its capture loop. Residual by design: an in-place
   change of the capture function object itself on the canonical load-map path,
   where no prepared-static code is authenticated by identity (pre-existing).
3. The assessment file is opt-in (`PREPARED_STATIC_WRITE_EVIDENCE=m25-assessment-03`)
   and skipped otherwise.
4. Non-plain `pressure_probe` or non-bool `warm_stress` keep the guarded route.
5. The identity fingerprint covers the cloned element, mesh and material contents,
   records aliasing by first-visit index, and compares a pressure load for
   pressure-only recipes; probe v3 (`../../evidence/m25_digest_probe_v3.py`) does the
   same across versions.
6. Tests prove revocation of the failed clone's lease (from the traceback) after a
   native error and after a cancellation injected inside the span (trace
   function), with the exception propagated unchanged.

Evidence: probe v3 pre-M25 versus fixed byte-identical; M25 tests 37 plus the
regression set 99 passed, 1 skipped (opt-in); base suites 112 of 115 (known
failures, same messages); ANYfem 16 of 16; `m25-assessment-03.json` GO; all four
reproductions take the safe route. Barge (epoch m25c, 392.6 of 400 s): lean
outputs byte-identical to M24 (primary twice, holdout once). The timings are not
clean: phases the fix does not touch (stiffness, vector build, case evaluation)
ran 13-60% slower than in M25 while the machine carried other load (system CPU
about 9.8% against 6.5%), and the holdout rerun hit its 100 s timeout during
preparation (preserved as a timeout). Measured directly, admission plus exit
checks cost 279 us per Q4/S3 capture (231 us after the first fixes), about 2.7 s
over the barge's roughly 9,600 captures, against the S3 saving of about 25 s.


### Third round (M25d): Codex re-review of M25c and fixes

The Codex re-review of M25c (`../../evidence/m25-review/fixes2/`) was stopped by
the OpenAI service ("flagged for possible cybersecurity risk") before it wrote a
report. Before the stop it had run the M25 tests (37 passed) and the reproductions
(safe), and found one real regression that M25c introduced by running the NumPy
route proof last: a numpy module `__getattr__`, reached through a deleted
`np.geterr` during that proof, planted a self-restoring pressure helper after the
LoadCase proof, and the span accepted its nested guarded call
(`m25_numpy_getattr_probe.py`; reproduced on M25c, refused now). Root cause: the
proofs are not individually callback-free (module attribute lookups can reach a
module `__getattr__`; replaced values can run methods), so no proof order is safe.

Fix: admission is bracketed by two general checks. (1) Before any proof and again
after the proofs and the span, 780 tracked modules (numpy, scipy, numba,
anysolver, anymaterial, warnings, sys, builtins and other stdlib modules the
proofs or span use) must still be their import-time module type with their
import-time `__getattr__` (modules still initialising when the table is built may
only gain a `__getattr__` defined in their own source file); attribute lookups then
cannot fall through to a substituted hook. (2) A callback-free identity snapshot
taken before and after the proofs must be unchanged: LoadCase, routing and
material class namespaces, the material clone, the warnings, sys and builtins
namespaces and warning filters, and NumPy's error state (C getter, compared by
value). After the span the snapshot (without the material clone, which span code
may cache on) and the module table are re-checked. The proofs run in the
boundary's order again (NumPy routes first). A change keeps the guarded route
during admission and is refused after the span.

Tests verified against the source each round fixed: the M25d tests fail on M25c
and pass now; the snapshot test fails on a scratch variant with the snapshot
disabled; earlier rounds' behavioural tests fail on their own pre-fix sources.
Note found while doing this: `pyproject.toml` sets pytest `pythonpath = ["src"]`,
which overrides PYTHONPATH, so pytest runs against an older source need
`-o pythonpath=<dir>`; the cross-version probes run with plain Python and are
unaffected. The three known base-suite failures were re-run correctly against the
pre-M16 and pre-M25 baselines and fail identically there.

Evidence: probe v3 pre-M25 versus now byte-identical; M25 tests 41 (with the
regression set 103 passed, 1 skipped opt-in); base suites 112 of 115 (known
failures, same messages); ANYfem 16 of 16; `m25-assessment-04.json` GO; all five
reproductions safe. Barge (epoch m25d): lean outputs byte-identical to M24;
timings again contaminated by other machine load (system CPU 15-17% against about
6.5% for M25; case evaluation, which the fix does not touch, about 20% slower).
Measured directly, admission plus exit checks now cost about 475 us per Q4/S3
capture, about 4.5 s over the barge's roughly 9,600 captures, so S3 nets about 20
of its 25 s preparation saving.

### Fourth round (M25e): Codex review of M25d and fixes

Codex (`../../evidence/m25-review/fixes3/codex-review-fixes3.md`) reported five
blockers, four should-fix and one nit. Fixed:

- Blocker 1 (admission could change an owner, reject trust, and continue with the
  changed owner): any change of the snapshot or module table during admission now
  refuses the capture, whatever the proofs concluded; and after every Q4/S3 capture,
  on either route, the private owner must still hold exactly the element inputs,
  material data and geometry frozen into its recipe identity (by value; NaN equals
  NaN), otherwise the capture is refused.
- Blocker 2 (late-module check could call `__eq__` on a replaced `__file__`): the
  canonical test requires exact `str` values, and the hook of a module that was
  still initialising is pinned with its code fingerprint once the module finishes.
- Blocker 4 (module table built before `prepared_static_q4` was imported): the
  table is built after every module-level import, also checks the `sys.modules`
  binding of every tracked name, and pins newly imported modules of the tracked
  families on first sight. scipy is no longer tracked (used by neither the proofs
  nor the span); `linecache` is.
- Part of blocker 3: the snapshot now covers the code and defaults objects of every
  method of the snapshot classes (in-place code swaps during admission) and the
  probe LoadCase instance; the LoadCase pressure helper and the boundary functions
  it calls are authenticated by a non-raising proof (a substituted helper keeps the
  guarded route, as before M25).
- Should-fix 6: the module check runs before the scope tables are read; the helper
  checker runs again in the final, callback-free block.
- Should-fix 8: an exception inside a proof means "not admitted" (guarded route).
- Should-fix 9: new tests for each fix, each shown to fail on the M25d source; the
  material-proof and exit-module-check tests shown to fail on scratch variants with
  that check removed; exact file paths in profile counts; the exit test sets its
  precondition; a binding-only checker test; a copied-context lease test.

Not fixed, by design (residual threat model). The span still relies on no foreign
code running inside it. Python tracing, profiling and monitoring callbacks, other
Python threads, signal handlers, garbage-collection finalizers and weakref
callbacks, and audit hooks can all run code inside a span and restore what they
changed (blocker 5); code that is already running can change the authenticator
itself (should-fix 7); and in-place changes of deep state outside the snapshot
remain possible (rest of blocker 3). These apply equally to the trusted scopes the
prepared-static route already uses for all per-case recovery
(`owned_recovery_scope`) and to the boundary and assembly spans; closing them needs
process isolation or C-level guards, not more Python checks. S3 is therefore as
strong as the existing trusted spans, not as strong as the fully guarded route.
(Superseded: the round-five review found two capture-specific blockers, so this
conclusion does not hold for the opt-in path as implemented; see the next section.)

Cost and benefit (direct measurements on the test models): a trusted capture saves
about 4 ms per Q4 stress capture, 0.6 ms per Q4 pressure capture and 8 ms per S3
capture against the guarded route; admission and exit checks now cost about
650 us per Q4/S3 capture, about 6 s over the barge's roughly 9,600 captures, so S3
nets about 19 of its 25 s preparation saving. Barge (epoch m25e): lean outputs
byte-identical to M24; preparation 71.5 / 71.3 s with the machine about 10-15%
slower than for M25 (system CPU about 9% against 6.5%).

Decision for the owner: (a) keep S3 by default under the trusted-span threat model
shared with the rest of the route; (b) make S3 opt-in (default capture fully
guarded); or (c) remove S3 and keep load_families (preparation about 19 s longer).

Evidence: probe v3 pre-M25 versus now byte-identical; M25 tests 53 (regression set
115 passed, 1 skipped opt-in); base suites 112 of 115 (known failures); ANYfem 16
of 16; `m25-assessment-05.json` GO; all reproductions safe.

### Codex review of M25e (round five, not yet acted on)

`../../evidence/m25-review/fixes4/codex-review-fixes4.md` (Codex ran the M25 tests:
53 passed on M25e; 10 of 53 fail on M25d). Codex does not yet accept that every
remaining risk is shared with the existing trusted scopes:

1. BLOCKER, S3-specific: the owner check compares values but not the private
   owners' providers or types: a callback during admission could plant an instance
   `get_node` on the private mesh (the Q4 coordinate reader calls `mesh.get_node`,
   e4_pl_element.py:2463; the boundary's own admission rejects exactly this) or
   change the cloned material's `__class__`. Premise verified by code reading.
2. BLOCKER, S3-specific, introduced in M25e: the runtime module rescan reads
   `__dict__` of arbitrary new `sys.modules` objects, which can invoke a descriptor.
3. SHOULD-FIX, introduced in M25e: `except Exception` around the proofs swallows
   `SolveCancelled` (a `RuntimeError`; verified).
4. SHOULD-FIX, introduced in M25e: append-only rescans can permanently disable S3
   after a temporary module replacement (availability, not correctness).
5. SHOULD-FIX: two tests do not independently prove their check (late-hook pinning;
   checker self-binding) and the pressure-helper proof has no dedicated test.
6. SHOULD-FIX, shared: a native scope exit failure can replace the primary exception
   (matrix_assembly preserves primary-exception precedence; the native scopes do not).
7-9. NITs: authentication narrower than worded; combined pressure+stress ordering;
   cost and eligibility depend on import history.

Codex classified blocker 5 and should-fix 7 of the previous round as accepted
residuals under the shared trusted-span model, and should-fix 6 as fixed.

### Decision: opt-in (M25f)

Owner decision after the round-five review: option 2, opt-in.

- `prepare_static_evaluator(..., trusted_capture=False)` and the response factory
  (through its keyword arguments); the ANYfem factories pass the option through.
  A non-`bool` value is refused. `diagnostics()["trusted_capture"]` reports it.
- Default (`False`): `_capture_owned_local_recovery` evaluates the recipe identity
  with the pre-M25 expression and then runs the pre-M25 capture statements; the
  only differences are that two plain assignments (`staged = None`, the fallback
  reason) come before the pressure warm-up, that the function reads the opt-in
  token (one context-variable lookup) and that it has a private keyword default
  (`_span_authority`). No admission, module check, snapshot or owner-identity
  check runs, and the capture callers skip the helper authentication. Small
  bookkeeping does run by default: the evaluator enters and resets the opt-in
  scope, capture reads the token, and the identity components are assigned to two
  names. At import the change creates only its checker closures, which hold no
  facts yet: the authentication, pressure-helper and material facts, the capture
  state table and the module table (about 5 ms) are all built on the first opt-in
  check. The owned-scope factory check used by `owned_recovery_scope` (reached by
  default through envelope compilation) is the pre-M25 check; the scope-table
  binding check added in the first round runs only on the opt-in path (M25o,
  round 9).
- Opt-in (`True`): the M25e admission-checked trusted capture, enabled for the
  duration of that preparation's snapshot capture through a context variable that
  holds a revocable token; the token is revoked on every exit, so a context copied
  during preparation (for example by a progress callback) does not keep the opt-in.
  Round-five blocker 2 (reading a module object's namespace could run code of an
  arbitrary `sys.modules` entry) also reached the default path, because the module
  table was built at import whatever the option (found by the opt-in review, round
  3; further routes in rounds 4 and 5: a foreign metaclass `__eq__`, a builtin
  descriptor of another class, a namespace key with a colliding hash). Fixed in
  M25i to M25k: the module table is now built on the first opt-in admission, so
  the default path (import and capture) never inspects `sys.modules`; and the
  inspection reads a namespace only when no Python-level code can run (plain
  metaclass on every class in the MRO; `__dict__` and `__getattribute__` only as
  builtin descriptors of the defining class; identity comparisons only; exact `str`
  keys checked by iteration before the keyed lookups made while building or
  rescanning the table, and in the `sys` namespace on every check). Any other object
  under a tracked package name is never read and keeps the opt-in on the guarded
  route while it is registered. M25l (round 6): the authentication facts use this
  module's own globals instead of a `sys.modules` lookup at import. M25m (round 7):
  the capture state table (`warnings`, `sys`, `builtins` namespaces and class
  executables) is also built on the first opt-in admission, after the module check;
  the authentication facts and the pressure-helper proof take their functions from
  import statements, with the modules' globals dicts as owners. The change's own
  import-time code therefore reads no module object (lookups by the import system
  itself are outside this guarantee). M25n (round 8): the authentication facts, the
  pressure-helper facts and the material facts are also recorded on the first
  opt-in check, so the default import makes no keyed read of another module's
  globals; only ordinary name resolution and import statements remain. Consequence
  for the opt-in path: these facts describe the state at the first opt-in use, not
  at import, so a change made between import and that first use is not detected.
  M25o (round 9): the scope-table binding check (keyed reads of this module's
  globals) moved from `owned_recovery_scope`, which runs by default, to the opt-in
  admission; the default route runs the pre-M25 owned-scope check. Residual, opt-in
  only: after the first scan, lookups in tracked module namespaces and by name in
  `sys.modules` are not re-validated unless `sys.modules` changes length, so a
  non-`str` key inserted later (or with a length-preserving swap) could run its
  equality during a later opt-in admission.
  The other
  capture-specific round-five findings (blocker 1, should-fix 3 to 5, nits 8 and 9)
  apply only to this opt-in path and are not fixed. Should-fix 6 (a
  native scope's exit failure can replace the primary exception) and nit 7
  (authentication narrower than worded) are shared limitations that also apply to
  the existing trusted recovery scopes, which run by default. The factory
  docstring states the opt-in's assumption.

Evidence: probe v4 (`../../evidence/m25_digest_probe_v4.py`) byte-identical for
pre-M25, default and opt-in; M25 tests 67 at M25f (default-route, option,
validation and response tests added; opt-in tests use an autouse fixture), 78
after the opt-in review rounds (copied-context revocation, four import cases with
hostile `sys.modules` entries, an import with a colliding `sys.modules` key, an
import with a hostile `warnings` module class, a reload with a planted key in
another module's globals, an uninspectable entry during an opt-in capture, the
default owned scope with planted keys in recovery's globals, and rebound scope
tables refused by the opt-in capture only); regression set 129
passed, 1 skipped; base suites 112 of 115 (known failures); ANYfem 17 of 17 with
`fem/tests/test_prepared_static_trusted_capture.py` (pass-through and identical
results); `m25-assessment-06.json` GO with the opt-in. Barge (epoch m25f), lean
outputs byte-identical to M24 in both modes; preparation, paired runs on a
heavily loaded machine (system CPU 18-28%): default 98.6 / 81.4 s, opt-in
70.9 / 72.1 s.

### Codex review of the opt-in change (ten static rounds, M25g to M25o)

Codex (`gpt-6-astra`, effort max, `--sandbox read-only`) reviewed the opt-in change
statically from bundles, because its Windows sandbox could not start commands.
Rounds 1 to 9 returned NOT OK; each finding was fixed (M25g to M25o) and gained a
test that fails on the previous source. Every finding after round 2 was a way the
default import or default route could still run foreign code through this change's
own inspection code. Round 10 (`../../evidence/m25-review/optin/codex-review-optin-11.md`):
**VERDICT: OK**, one NIT (the test count in this report), fixed. Final evidence: M25
tests 78 of 78 (`m26-optin-review-tests-10d`), ANYfem trusted-capture test 1 of 1
(`m26-optin-review-fem-10`), probe v4 byte-identical to pre-M25 with the option off
and on (`m25o-digest-default`, `m25o-digest-optin`). The opt-in path's own residuals
listed above stay open.

Later note (M30 platform check, 2026-10-10): on Python 3.12 the import system
reads the source module's `__name__` for every `from .boundary import ...`
statement, so `test_initialization_makes_no_keyed_reads_of_other_modules_globals`
failed on Linux/Python 3.12 although no inspection code of the change ran. The test
now ignores reads made while the caller executes an import instruction (import
statements are outside the review's scope) and still fails on the round-8 source.

## Remaining preparation levers (not implemented)

- The vector recovery build (about 21 s: affine probing of 4,245 envelope
  elements) is now the largest preparation item. M26 pipelines its two passes
  (`PREPARED_STATIC_M26_VECTOR_BUILD_SINGLE_PASS.md`).
- Stiffness assembly about 9 s and load-map verification against the oracle use
  the model's own elements with per-call guards; S3 does not cover them.
- S7 (digest by array bytes, about 4 s) remains an owner decision.

## Still open

Different-family review; the five pre-existing authority-test failures; S7;
integration (commit/merge) decision.
