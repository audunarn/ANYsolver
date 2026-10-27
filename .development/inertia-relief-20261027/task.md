# Inertia relief implementation — 2026-10-27

State: implemented and verified against the assigned functional and isolated
artifact criteria. Independent Opus5.5/medium review completed; findings resolved.

User-approved scope: one connected free-free linear beam/shell assembly with
homogeneous internal MPCs. Public `solve_inertia_relief` and typed result/error;
mass-based physical six-component acceleration, inertial loads, nullspace elastic
solve and numerical reporting. Full governing plan is the user's implementation
request in this chat. Fable 5.1/high reviewed the plan once; evidence is
`C:/ANYworkspaceWork/inertia-relief-plan-20261027-01/fable-review-network/review.txt`.

Slices, in dependency order:
1. Shared rigid-inertia projection, admission and physical load balance;
   analytical acceleration and resultant checks must pass at 1e-10.
2. Nullspace elastic solve, converged scaled mechanism check and effective-load
   recovery; beam/shell/MPC independent oracles must pass at 1e-8.
3. Session/cancellation/result metadata, example and documentation; focused,
   affected regressions and isolated installed-artifact checks must pass.

Prospective gates: acceleration/elastic backward error, force/moment block
balance, rigid compatibility/stiffness/gauge <=1e-10; scaled elastic eigenvalue
margin >1e-12 and eigenpair residual <=1e-13. Do not loosen thresholds. No
pseudoinverse, artificial supports or invented stiffness. Matrix-free projection
and sparse Lanczos; no dense full stiffness or full complement basis.

Protected dirty work: solid adapter and principal-axis edits. Baseline patch,
status, hashes and copies of overlapping assembly/__init__ files are preserved at
`C:/ANYworkspaceWork/inertia-relief-impl-20261027-01/`. Never reset/discard them.
No sibling edits, commits, pushes, publication or historical qualification runs.

Implementation owner: Astra directly. The optional Sonnet Edit launcher was
rejected by automatic approval review because prior source-export permission was
limited to Fable Read review. No worker inference or edits occurred. Direct
ownership preserves one connected implementation and avoids widening export
authority. User subsequently approved Fable requests and emphasized independent
review. User then clarified that general independent review must use Opus5.5 at
medium effort; Fable5.1/high remains the completed plan review.

Runtime: `C:/Github/ANYsolid/.venv/Scripts/python.exe`, read-only dependency use;
`PYTHONPATH=C:/Github/ANYsolver/src` confirmed actual source imports. NumPy 2.4.6,
SciPy 1.17.1, pytest 9.1.1. Do not modify this sibling environment. Checks through
`C:/ANYworkspaceWork/inertia-relief-impl-20261027-01/checks.py` only: worker 900
process-wall seconds, root verification reserve 600 seconds. Each process tree is
bounded; exact commands, source hashes, outputs, counts and failures retained.

Open risks: scalable mechanism classification at the frozen tolerances; shell
capability admission and effective-load recovery; stale direct point-mass edits;
preserving distinct activity policies; ill-conditioned valid thin-shell cases.

## Progress / handoff

Initial design decisions: perform the rigid solve in centre-of-mass coordinates
and transform it to the requested reference by exact rigid-coordinate congruence;
this solves the coupled reference equation without distant-origin cancellation.
Use matrix-free projected, dimensionally scaled Lanczos with a diagnostic-only
rank-six lift; it never changes physical stiffness. Recover stresses on demand
through existing recovery and compute constraint forces against effective loads.
First focused run: 33 passed, 4 failed (checks/135847-focused-277751). Three
failures were cancellation-dominated normalization: unaugmented residuals were
5.9e-17 to 1.45e-16, but dividing by F_effective alone gave 2e-4 to 8e-3.
Define the scaled physical-data backward error as
||S(Kq-F_effective)||inf / (||SKS||inf ||q/S||inf + ||S T.T F||inf + ||S T.T Fi||inf).
Retain the effective-load-relative error as an additional diagnostic, without
projecting loads or loosening 1e-10. Fourth failure: the COM coupling-block check
scaled against its own cancelled norm; relief supplies mass*geometric_length as
the natural coupling scale at the unchanged 1e-10 tolerance. Existing public mass
diagnostic calls retain their default semantics. Diagnostic evidence is retained
at checks/135936-diagnostic-2f260e. Source currently implemented, not yet verified.
## Verification checkpoint

Implementation and functional/artifact checks are complete; independent review
closeout remains pending. Core source is frozen for Opus delta review.

Owned changes: new inertia_relief module, shared mass projection/validation,
point-mass cache identity, additive root exports, two focused test modules,
docs/INERTIA_RELIEF.md, examples/inertia_relief.py, README link and this note.
All ten pre-existing tracked dirty files were verified preserved (the original
__init__ content is identical after removing the four additive exports). Existing
assembly.py is unchanged by this task. Verification receipt:
`C:/ANYworkspaceWork/inertia-relief-impl-20261027-01/protected-work-verification.json`.
Base HEAD: `1cff283d67ba31bf6d5dc816e2b55bd8359daa9b`; no commits/pushes/publication.

Checks use `C:/Github/ANYsolid/.venv/Scripts/python.exe` with the task harness
`C:/ANYworkspaceWork/inertia-relief-impl-20261027-01/checks.py`:

- `focused`: 56 passed, 0 failed, 0 skipped; 16.453 process-wall seconds;
  `checks/142437-focused-589a17`.
- `regression`: 134 passed, 0 failed, 1 skipped (PyPardiso absent);
  130.109 process-wall seconds; `checks/141954-regression-e0cd53`. Two expected
  warnings are from existing nonfinite/overflow mass-refusal tests. Core helper,
  mass/session, original static, prepared mass and control regressions passed.
- `installed --wheel checks/142519-installed-deec31/wheels/anysolver-0.4.7-cp311-cp311-win_amd64.whl`:
  source/test hashes matched the retained built wheel; a fresh isolated install
  verified its import under the isolated sys.prefix, then 56 focused tests passed
  with 0 failures/skips; 46.375 process-wall seconds;
  `checks/142954-installed-0f35f5`.

Each check folder contains exact underlying commands, source SHA256 identity,
full stdout/stderr, terminal process-tree cleanup, precise wall duration and
junit counts. At this checkpoint cumulative check process-wall use was 457.891
seconds of the self-imposed 1500-second allocation; no frozen authority consumed.

Additional failures preserved: missing optional Numba caused five regression
failures at `checks/140239-regression-829b9b` (129 pass,1 skip). Installed Numba
0.68.0/llvmlite0.50.0 only into this task's test-dependencies, leaving the sibling
environment unchanged; subsequent regression passed. Initial installed check
`checks/142519-installed-deec31` correctly caught pip skipping a same-version
wheel because shared dependencies exposed an old solver; repaired disposable
installer uses --ignore-installed and verifies actual artifact origin.

Independent review: user selected Opus5.5/medium for general review. Initial
report at `C:/ANYworkspaceWork/inertia-relief-opus-review-20261027-01/review.txt`
found core mechanics sound but blocked on availability and inherited load scale.
Resolved inherited refusal with a caller-specific tolerance algebraically
removing its unit floor, while keeping refusal enabled and physical 1e-10 gates.
Density/load scales 1,1e6,1e12 now pass. Added cancellation ratio and explicit
total-load accuracy caveat, activity and stale-recovery tests. Revision signature
source was verified to return a fresh dict; result also explicitly copies it.

Availability investigation was decision-oriented, not a tolerance sweep:
`checks/141059-refinement-642e51` measured 32/64/128 beam elements; an enlarged
bounded Krylov space resolved a 512-element beam at lambda=2.58807e-8 and
residual=8.16e-16 (`checks/141551-refinement-72738f`). Thin-panel failure was
independently confirmed as Lanczos nonconvergence, not a below-gate mode:
4x4 panel L/t=1000 and 10000 had dense-oracle minima 1.01016e-8 / 1.01016e-10
(`checks/142153-thin-0d0080`). The final bounded ncv128..256 workspace resolved
both at unchanged 1e-12 margin/1e-13 residual gates, agreeing with dense oracles
(`checks/142234-thin-82dd9e`). These are measured cases, not ship-scale claims.

A valid homogeneous MPC counterexample corrected the naive zero-row test:
ux_node2=ux_node1 makes one independent coordinate a whole rigid translation.
Zero rows are rejected only when outside the physical six-mode span. Extra,
unloaded and negative stiffness modes still fail. Code/API now reports
unresolved_elastic_stiffness without asserting a physical mechanism.

Opus5.5/medium delta review completed at
`C:/ANYworkspaceWork/inertia-relief-opus-review-20261027-02/review.txt`. It found
no correctness blocker, confirmed the effective-load recovery and tolerance
fixes, and withdrew the unmeasured N^-4 estimate as an acceptance blocker.
It requested a restarted-Lanczos unloaded-mechanism test on a large model and
extra staleness/scale checks; these are now covered below. No full qualification,
external solver campaign or PyPardiso agreement has been claimed/run.

## Final acceptance and handoff

State: verified against assigned criteria. No required implementation work is
outstanding. Independent review is complete; all actionable findings have been
adjudicated or covered by the final checks. The post-review production change
adds only result-case input identity metadata; the reviewed numerical equations
and gates are unchanged. No claim of blanket element qualification or release.

Final focused run: **61 passed, 0 failed, 0 skipped**, 26.375 process-wall seconds,
`checks/143818-focused-bbc628`. Added 512-element unloaded released/negative
stiffness cases (n far exceeds ncv), non-gravity rigid-load amplitudes 1e-9 and
1e12, in-place activity staleness, displacement agreement after session geometry
changes and mass/constraint provenance identity. All passed.

Final artifact run: **61 passed, 0 failed, 0 skipped**, 66.252 process-wall seconds,
`checks/144006-installed-459a81`. Rebuilt the wheel after the provenance change,
installed it into a fresh isolated venv with --ignore-installed, verified actual
import origin under that venv, ran the example and copied standalone tests.
The example gave a=6.36942675159 m/s^2, matching 1000/(7850*.01*2); force-balance
error 1.13687e-16, moment error 0, elastic backward error 2.728e-17.

Affected legacy regressions remain **134 passed, 1 skipped, 0 failed**. Subsequent
changes were confined to the new inertia-relief module, new tests/docs and
result-case metadata; the legacy mass/session/export helpers that this regression
verified were unchanged. PyPardiso backend agreement remains unverified because
that optional package is absent; the skip is not a pass.

Exact task check entry points (underlying pytest/build/install commands are saved
in each check folder's phase command.json):

```powershell
$env:INERTIA_RELIEF_ROOT_CHECK = '1'
$python = 'C:/Github/ANYsolid/.venv/Scripts/python.exe'
$checks = 'C:/ANYworkspaceWork/inertia-relief-impl-20261027-01/checks.py'
& $python $checks focused
& $python $checks regression
& $python $checks installed
```

Effective runtime and dependency origins are recorded in `runtime.json` in the
evidence root. NumPy2.4.6/SciPy1.17.1/pytest9.1.1, task-local Numba0.68.0 and
llvmlite0.50.0 were verified; both OpenBLAS pools used two threads. The shared
dependency environment was not edited. All completed supervised process trees
were cleaned up; no task-owned background work remains.

Known limits: one free-free linear body, admitted beam/shell element profiles,
homogeneous internal MPCs. Native total-Lagrangian formulations, solids,
nonlinear/prestressed routes, follower loads, load-only masses and physical
supports are refused. Tested shell acceptance is E4-PL Q4 and the current public
linear S3 V2D profile with an authoritative reference_normal. The conservative
fixed spectral gate can refuse a valid but numerically
unresolved model. Cancellation ratio must be interpreted for small elastic
signals; the error gate is relative to total applied+inertial load, not a relative
stress forward-error guarantee. No full-repository, historical qualification,
external solver or publication campaign was run or authorized by this task.

### Final scope audit

The scope audit distinguished a dormant native S3 implementation from the
current public selector. The current public factory maps to linear S3 V2D,
requires authoritative reference_normal and reports native-TL=False; its
canonical linear stiffness/mass and recovery passed the tiny feasibility probe
at checks/145050-s3-77e661. The preceding missing-normal factory refusal is
preserved at checks/144939-s3-144f35, with its exact input script retained. This
was an input-admission failure, not a solver pass. Earlier wording that the
default public S3 was excluded was corrected after observing the effective
runtime selector. No element guard, production kernel or acceptance tolerance
was changed to admit the profile.

Added direct manufactured-strain/rigid-acceleration acceptance for default S3
V2D (semidefinite full M, nonsingular rigid inertia), and quadratic-beam free fall
with consistent-mass provenance. Source focused run: **63 passed, 0 failed,
0 skipped**, 22.282 process-wall seconds, checks/145236-focused-76b195. Production
source is byte-identical to the previously built 61-test wheel; only tests and
documentation changed. That retained wheel is being checked in a fresh isolated
environment with the current 63-test input. The source-binding check correctly
refused reuse when it detected an unrelated concurrent pressure-region export
addition in __init__.py (14:50 UTC); that addition is preserved. The critical
inertia-relief/mass/session sources are unchanged, but the candidate is being
rebuilt against the current package exports. The refused reuse is retained at
checks/145342-installed-4204f5; it performed no numerical tests.

Final source-bound artifact closeout: **63 passed, 0 failed, 0 skipped**, 64.375
process-wall seconds, checks/145722-installed-ad1338. The five critical solver,
mass, session and recovery source modules were byte-hash checked against the
current checkout. A later concurrent pressure-region export update changed
__init__.py after the build; normalized-AST comparison proved all existing and
inertia-relief bindings identical, excluding only the nonshadowing pressure
import/__all__ extension. Both entry-point snapshots are retained. This is a
scoped inertia-relief artifact check, not qualification of concurrent pressure
work. The current-checkout entry point and analytical example also passed at
checks/150951-smoke-89ed9c. The installed example also
passed with the same analytical acceleration and numerical errors listed above.
The source run remains 63/0/0, legacy regression 134/0/1. Final machine-readable
counts, exact source/wheel hashes, review model/effort receipts and protected-work
verification are in
`C:/ANYworkspaceWork/inertia-relief-impl-20261027-01/verification-summary.json`.
All source/installed acceptance criteria are met; no task-owned work remains.
Cumulative supervised numerical-check process-wall use was 643.425 seconds of
the 1500-second self-imposed allocation. All failed evidence and earlier artifact
snapshots remain retained; no source or acceptance gate was reset or waived.

## Merge delivery verification (2026-10-27)

The user explicitly authorized including earlier S3 reference fix `1cff283d67ba31bf6d5dc816e2b55bd8359daa9b`. The inertia-relief delivery is isolated from unrelated shared-checkout edits in a disposable clone based on that commit. Only the ten owned inertia-relief files are staged.

Independent review: Claude Opus 5.5 at medium effort, including follow-up; no remaining correctness blockers. Review receipts and original source identity remain in the evidence paths recorded above.

### Clean-checkout focused and affected regressions: 197 passed, 1 skipped (PyPardiso unavailable); license compliance passed

Evidence: `C:/ANYworkspaceWork/inertia-relief-impl-20261027-01/checks/160220-delivery-core-2e8821`; process-wall seconds: 69.734. Exact commands:

```text

C:\Github\ANYsolid\.venv\Scripts\python.exe -m pytest -q --junitxml=C:\ANYworkspaceWork\inertia-relief-impl-20261027-01\checks\160220-delivery-core-2e8821\junit.xml tests/test_inertia_relief.py tests/test_inertia_relief_integration.py tests/test_fe_solver_infrastructure.py tests/test_fe_solver_mass_modal.py tests/test_generalized_section_mass_properties.py tests/test_analysis_session.py tests/test_static_batch.py tests/test_prepared_static_mass_capture.py tests/test_solver_control_contracts.py

C:\Github\ANYsolid\.venv\Scripts\python.exe scripts/check_license_compliance.py

```

### Earlier S3 fix: 7 passed, 5 deselected, including both new checks

Evidence: `C:/ANYworkspaceWork/inertia-relief-impl-20261027-01/checks/160108-clipped-fast-4193fc`; process-wall seconds: 8.531. Exact commands:

```text

C:\Github\ANYsolid\.venv\Scripts\python.exe -m pytest -q --junitxml=C:\ANYworkspaceWork\inertia-relief-impl-20261027-01\checks\160108-clipped-fast-4193fc\junit.xml tests/test_general_contact_transient_clipped_s3.py -k "not moving_clipped and not captured_clipped and not refined_clipped_production and not fresh_matched"

```

### New isolated wheel: 63 passed, 0 failed, 0 skipped; installed import and analytical example passed

Evidence: `C:/ANYworkspaceWork/inertia-relief-impl-20261027-01/checks/160450-installed-fbd722`; process-wall seconds: 80.079. Exact commands:

```text

C:\Github\ANYsolid\.venv\Scripts\python.exe -m build --wheel --no-isolation --outdir C:\ANYworkspaceWork\inertia-relief-impl-20261027-01\checks\160450-installed-fbd722\wheels C:\ANYworkspaceWork\inertia-relief-delivery-20261027-01\checkout

C:\Github\ANYsolid\.venv\Scripts\python.exe -m venv C:\ANYworkspaceWork\inertia-relief-impl-20261027-01\checks\160450-installed-fbd722\venv

C:\ANYworkspaceWork\inertia-relief-impl-20261027-01\checks\160450-installed-fbd722\venv\Scripts\python.exe -m pip install --no-deps --ignore-installed C:\ANYworkspaceWork\inertia-relief-impl-20261027-01\checks\160450-installed-fbd722\wheels\anysolver-0.4.7-cp311-cp311-win_amd64.whl

C:\ANYworkspaceWork\inertia-relief-impl-20261027-01\checks\160450-installed-fbd722\venv\Scripts\python.exe -c "import anysolver,pathlib,sys; p=pathlib.Path(anysolver.__file__); assert p.is_relative_to(pathlib.Path(sys.prefix)),p; from anysolver import solve_inertia_relief,InertiaReliefResult,InertiaReliefError; print('installed artifact:',p)"

C:\ANYworkspaceWork\inertia-relief-impl-20261027-01\checks\160450-installed-fbd722\venv\Scripts\python.exe C:\ANYworkspaceWork\inertia-relief-delivery-20261027-01\checkout\examples\inertia_relief.py

C:\ANYworkspaceWork\inertia-relief-impl-20261027-01\checks\160450-installed-fbd722\venv\Scripts\python.exe -m pytest -q -c C:\ANYworkspaceWork\inertia-relief-impl-20261027-01\checks\160450-installed-fbd722\pytest.ini --junitxml=C:\ANYworkspaceWork\inertia-relief-impl-20261027-01\checks\160450-installed-fbd722\junit.xml C:\ANYworkspaceWork\inertia-relief-impl-20261027-01\checks\160450-installed-fbd722\tests

```

### Preserved failures and limits

The first combined run timed out after 300 seconds with setup failures caused by missing RUNNER_TEMP. The diagnostic run recorded 1 failure and 3 passes. With the CI-compatible environment corrected, the full clipped S3 transient module still timed out after 240 seconds (seven progress successes, incomplete suite). Five long transient scenarios remain unverified locally; this is not a full-module pass. No numerical tolerance or acceptance gate was changed. Failed evidence is retained under `153759-delivery-f3a847`, `154857-clipped-d15263`, and `155348-clipped-f69631`. CI has not yet run for the delivery commit.

The diagnostic environment repr exposed an inherited credential in tool output and two external evidence files. Those saved files were redacted with a retained redaction receipt; subsequent test children remove credential/provider environment variables. No credential-bearing evidence is staged or published. Parent credentials/settings were not changed.

Cumulative supervised numerical-check process-wall use: 1349.472 seconds of the unchanged 1500-second allocation.


## Static batch integration milestone (2026-10-27)

User request: inertia relief and nullspace must be fully wired into the static
batch fast path. Baseline is merge 1882ba5d9; isolated worktree excludes concurrent
solid, pressure and S3 edits in the shared checkout. This is authorized connected
implementation and focused verification, not a new qualification campaign.

Plan and prospective acceptance:
1. Share reusable inertia-relief preparation, balancing and accuracy services
   between the public scalar solve and prepared static operators. Preserve every
   original admission, mechanism, error and cancellation gate. Acceptance: scalar
   analytical and refusal tests remain unchanged and pass.
2. Add an explicit opt-in inertia_relief=True and reference_point to
   iter_linear_batches, preserving default behavior. Use one prepared operator,
   matrix-RHS solves and bounded output/recovery; no loop over the public scalar
   solver. Acceptance: multi-case/multi-block results and diagnostics match scalar
   beam, shell and eccentric-MPC references; counters demonstrate reuse.
3. Verify nullspace, effective-load recovery, mutation/invalidation, cancellation,
   resource/lifecycle and installed public API. Acceptance: focused/affected tests
   and independent review close without changing scientific tolerances.

Open risks: scale-dependent cancellation, physical MPC forces confused with gauge
or support reactions, stale mass/constraint caches, eager custom load observation,
selected-output memory, and factorization reuse across blocks. Numerical failure
must refuse the block and never expose accepted displacements. Keep ordinary
unbalanced-load refusal and explicit legacy opt-in behavior unchanged. Inertia
relief cannot silently enable allow_unbalanced_free_free.

One Sonnet 5.5 subscription worker owns the connected implementation and its
focused inspect/design/edit/check/repair/document loop. Astra owns contract review,
independent verification and integration. New milestone numerical allocation:
1800 supervised process-wall seconds total, worker may use 900; reserve 900 for
independent acceptance. This does not renew prior exhausted checks or authorize
historical campaigns. Preserve all failures. Early checkpoint within 120 seconds
of inference: concrete findings, route, intended edits and blockers in this note.

Implementation ownership checkpoint: automatic approval review rejected the scoped
Sonnet Edit launch as outside its interpreted Fable-only authorization; no worker
inference started. Astra takes direct ownership because that runner is unavailable.
No repeated worker probe or alternate billing route is used. The existing batch
operator already supports multi-RHS nullspace solving. The implementation shares
physical inertia preparation, matrix balancing and elastic certification with the
scalar route; the session owns one revision-keyed plan and cached Lanczos result.
Reference-point reporting is separate from that physical cache. Remaining work:
wire the prepared plan into batch reductions, effective-load recovery and metadata,
then exercise cancellation/mutation/reuse and independent review. Scientific
thresholds and ordinary default batch behavior remain fixed.


### Integrated candidate and independent findings

The collecting API solve_linear_many was found to route explicit nullspace but
refuse auto free-free models. The authorized connected boundary now also includes
that function in assembly.py: explicit inertia relief and auto/explicit nullspace
use the prepared batch engine; supported-static defaults retain their route.

Initial integrated check checks/162309-focused-4f8058: 124 passed, 0 failed,
51.563 process-wall seconds. Its receipt omitted the static_batch source hash;
it is superseded for final acceptance by the later source-bound run.
Expanded check checks/162756-delivery-core-1feda6: 230 passed, 1 skipped, 2 failed,
with failures from a new stress test numerically comparing string provenance.
Full diagnostics/JUnit remain retained. The comparator was corrected to compare
numeric fields with unchanged 1e-8/1e-9 tolerances and strings exactly.

Independent Opus5.5 medium source review completed (4 successful reads, no tool
errors) at C:/ANYworkspaceWork/static-batch-inertia-relief-20261027-01/opus-review.
Its physical equations, scaling, compatibility normalization and effective-load
MPC checks were favorable. Addressed: Lanczos Krylov/work memory preflight,
immediate stale-plan release on stiffness/mass/constraint invalidation, defensive
metadata copies, typed input codes/numerical statuses, conditional inertia-only
imports, and reporting raw backend gauge/augmented errors before gauge cleanup.
Final-field scientific gates remain unchanged. Added discriminating memory,
metadata-isolation, cache-lifetime, MPC-recertification, activity, force-scale,
raw-backend-gauge and zero-load checks. Implicit detection of all unbumped
material/geometry changes was not adopted: the original user contract explicitly
retains revision updates except for direct point-mass contents.

Corrected combined check checks/163439-delivery-core-90f006: 240 passed, 1 skipped
(PyPardiso unavailable), 0 failed; two expected overflow warnings in retained-mass
refusal coverage; license compliance passed; process-wall duration70.031 seconds.
Exact commands, source hashes, JUnit and process-tree cleanup are retained.

Opus5.5 medium follow-up completed, 9 successful reads, no tool/API errors, at
C:/ANYworkspaceWork/static-batch-inertia-relief-20261027-01/opus-followup. It found
no blocking correctness defects in mechanics, gates or keys. Subsequent small
repairs address empty-input model admission, deep copies of cached mechanism
failure lists and scalar mode/constraint metadata. Effective constraint-mode
reporting was already corrected while that review was reading the earlier source.
Code/status/scope assertions and empty-input/detached-failure tests were added.
The external factor-cache ownership behavior is preserved and documented: reuse
across calls requires retaining the AnalysisSession; implicit sessions have
distinct signatures. Changing global cache lifecycle semantics is outside this
integration and would break an existing caller-cache test. The follow-up's
non-blocking suggestion for an adversarial perturbation separating generic and
physical-data error normalization remains additional possible coverage; existing
analytical, dense reference, force-scale, corrupted-column and raw-gauge tests
exercise production acceptance. No gate or physical assumption was weakened.

First installed run checks/163730-installed-c16157: wheel build/import and scalar
plus batch analytical example passed; 141 tests passed, 1 failed because the
isolated test copy omitted the qualified-S3 helper module imported by an existing
batch test. This is a harness dependency error, not a passing full suite. The
helper is now copied and pytest uses only the four explicit intended test modules
so the helper's qualification campaign is NOT collected or run. A rebuilt final
source candidate is being verified after the minor review repairs above.

### Final batch integration acceptance

The final shared-source run and isolated artifact both pass. Independent Opus
review has no remaining blocking findings; its non-blocking cache-lifecycle
limitation and additional possible adversarial-normalization coverage are
documented above. Scope remains the original linear beam/shell profile.

source: **244 passed, 1 skipped, 0 failed**, 68.141 supervised process-wall seconds.

Evidence: `C:/ANYworkspaceWork/static-batch-inertia-relief-20261027-01/checks/165103-integration-9945bb`. Exact phase commands:

```text

C:\Github\ANYsolid\.venv\Scripts\python.exe -c "import json,numpy,scipy,numba,anysolver; from threadpoolctl import threadpool_info; from anysolver.jit_compiler import JIT_ENABLED; print(json.dumps(dict(module=anysolver.__file__,numpy=numpy.__version__,scipy=scipy.__version__,numba=numba.__version__,numba_max=numba.config.NUMBA_NUM_THREADS,numba_effective=numba.get_num_threads(),jit_enabled=JIT_ENABLED,pools=[{k:x.get(k) for k in ('internal_api','num_threads','prefix')} for x in threadpool_info()])))"

C:\Github\ANYsolid\.venv\Scripts\python.exe -m pytest -q --junitxml=C:\ANYworkspaceWork\static-batch-inertia-relief-20261027-01\checks\165103-integration-9945bb\junit.xml tests/test_static_batch_inertia_relief.py tests/test_static_batch.py tests/test_inertia_relief.py tests/test_inertia_relief_integration.py tests/test_fe_solver_infrastructure.py tests/test_fe_solver_mass_modal.py tests/test_generalized_section_mass_properties.py tests/test_analysis_session.py tests/test_static_batch.py tests/test_prepared_static_mass_capture.py tests/test_solver_control_contracts.py

```

installed: **146 passed, 0 skipped, 0 failed**, 83.907 supervised process-wall seconds.

Evidence: `C:/ANYworkspaceWork/static-batch-inertia-relief-20261027-01/checks/165228-installed-c7aeb9`. Exact phase commands:

```text

C:\Github\ANYsolid\.venv\Scripts\python.exe -m build --wheel --no-isolation --outdir C:\ANYworkspaceWork\static-batch-inertia-relief-20261027-01\checks\165228-installed-c7aeb9\wheels C:\ANYworkspaceWork\static-batch-inertia-relief-20261027-01\checkout

C:\Github\ANYsolid\.venv\Scripts\python.exe -m venv C:\ANYworkspaceWork\static-batch-inertia-relief-20261027-01\checks\165228-installed-c7aeb9\venv

C:\ANYworkspaceWork\static-batch-inertia-relief-20261027-01\checks\165228-installed-c7aeb9\venv\Scripts\python.exe -m pip install --no-deps --ignore-installed C:\ANYworkspaceWork\static-batch-inertia-relief-20261027-01\checks\165228-installed-c7aeb9\wheels\anysolver-0.4.7-cp311-cp311-win_amd64.whl

C:\ANYworkspaceWork\static-batch-inertia-relief-20261027-01\checks\165228-installed-c7aeb9\venv\Scripts\python.exe -c "import anysolver,pathlib,sys; p=pathlib.Path(anysolver.__file__); assert p.is_relative_to(pathlib.Path(sys.prefix)),p; from anysolver import solve_inertia_relief,InertiaReliefResult,InertiaReliefError; print('installed artifact:',p)"

C:\ANYworkspaceWork\static-batch-inertia-relief-20261027-01\checks\165228-installed-c7aeb9\venv\Scripts\python.exe C:\ANYworkspaceWork\static-batch-inertia-relief-20261027-01\checkout\examples\inertia_relief.py

C:\ANYworkspaceWork\static-batch-inertia-relief-20261027-01\checks\165228-installed-c7aeb9\venv\Scripts\python.exe -m pytest -q -c C:\ANYworkspaceWork\static-batch-inertia-relief-20261027-01\checks\165228-installed-c7aeb9\pytest.ini --junitxml=C:\ANYworkspaceWork\static-batch-inertia-relief-20261027-01\checks\165228-installed-c7aeb9\junit.xml C:\ANYworkspaceWork\static-batch-inertia-relief-20261027-01\checks\165228-installed-c7aeb9\tests\test_static_batch_inertia_relief.py C:\ANYworkspaceWork\static-batch-inertia-relief-20261027-01\checks\165228-installed-c7aeb9\tests\test_static_batch.py C:\ANYworkspaceWork\static-batch-inertia-relief-20261027-01\checks\165228-installed-c7aeb9\tests\test_inertia_relief.py C:\ANYworkspaceWork\static-batch-inertia-relief-20261027-01\checks\165228-installed-c7aeb9\tests\test_inertia_relief_integration.py

```

The final source run observes this shared checkout, NumPy2.4.6, SciPy1.17.1,
Numba0.68.0, JIT enabled, Numba maximum/effective threads2, and all observed
BLAS/OpenMP pools2. Its sole skip is optional PyPardiso absence; two overflow
warnings are expected refusal-case diagnostics. Earlier runs only recorded
requested BLAS thread settings, not observed Numba settings.

The installed example reports scalar and batch axial acceleration
6.369426751592358 m/s^2 (analytical1000/(7850*.01*2)), zero force/moment
balance errors, scalar elastic backward error3.638e-17, and selected elastic
tip displacement2.97619047619e-7 m. No speedup or discretization claim is made.

The preceding artifact check checks/164217-installed-cb3cf1 passed145 tests
before the final unsupported-solid-dispatch guard. That guard is now tested
before any downstream adapter can drop the inertia flag. A new artifact was
built rather than reusing the earlier source identity. Final tests pass146.

Shared-checkout integration preserved27 unrelated dirty/untracked files.
The pre-existing solid adapter in assembly.py was reconciled without copying
it into this commit. Reversing only the owned patch in a disposable copy
proved the mixed assembly edits byte-identical. Three previously clean owned
files underwent only normal LF/CRLF conversion in that preservation proof.
The initial failed patch checks made no primary edits; the forward patch
applied after reconciliation. Integration details are in integration-receipt.json.

Final wheel SHA256: `d2c8acf552f407d60dd21b22d04d0a6a3243e475f89d516dba95ba42a5dfbb8c`. Its targeted source members
match staged Git blobs after normal Windows newline normalization; raw
source/wheel-member hashes and Git blob identities are retained in
`C:/ANYworkspaceWork/static-batch-inertia-relief-20261027-01/acceptance.json`.

Total supervised numerical process-wall use: 570.267
seconds of the unchanged1800-second milestone allocation. All failed
evidence is preserved. No full repository, historical qualification, external
solver or performance campaign was run. Other dirty work is not qualified
by this result. The final commit will contain only the eight owned paths.
