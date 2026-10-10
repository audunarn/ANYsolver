# Prepared static evaluator — living implementation record

## Authority and baseline

User approved implementation of the replacement plan on 2026-10-08. Apply
ANY_ECOSYSTEM_RISK_PROPORTIONATE_ENGINEERING_V1 revision 2026-09-24.2. This is
new prepared-direct implementation authority; old benchmark allocations remain
consumed. The approved new benchmark cap is 600 cumulative process-wall seconds.
No package release or default-route change is authorized.

- Solver baseline: cff55d95e905ab689efdacdf08742a60614728c1.
- ANYfem baseline: 3e4eb7f206042931d496b98f39af5e2a40b5951f.
- Isolated solver: C:/ANYworkspaceWork/prepared-static-20261008/solver.
- Isolated application: C:/ANYworkspaceWork/prepared-static-20261008/fem.
- External evidence: C:/ANYworkspaceWork/prepared-static-20261008/evidence.
- The original edited proposal is preserved as evidence/supplied-plan.md. The
  current user-approved replacement and contracts below supersede that proposal.
- Main solver tracked state was clean; unrelated untracked marine implementation,
  guidance, supplied proposal and pytest directories are protected. ANYfem UI,
  application, documentation and test edits remain untouched in its main checkout.
- Solver checkout is sparse (src/tests/docs/scripts/examples/benchmarks and root
  files): full worktree creation encountered preexisting overlong archived paths.

## Adopted contracts

1. Opt-in prepare_static_evaluator returns a context-managed evaluator with
   iter_batches, close and diagnostics. Preserve StaticCase(case_id, load_case,
   time=None), RecoveryConfig, ResourceConfig and existing solve defaults.
2. Snapshot owns mutable containers/metadata; only demonstrably immutable backing
   buffers may be shared through private headers. After preparation no live model
   dependence, per-case model scans or user callbacks within numerical spans.
3. Existing FactorizationCache with private backend/factor. Never steal/transfer a
   caller factor. Caller session lifetime and external same-pattern factorization
   cannot invalidate evaluator state. Deterministic close, counted preparation.
4. Fixed geometry/material/constraints/prescribed offsets/activity/structural mass.
   Arbitrary static time histories and changing case loads remain accepted.
5. Default load_families=None covers current supported families. Exact nodal,
   element, pressure/follower-linear-static and canonical acceleration maps;
   per-case added masses. No dense global inverse or full influence matrix.
6. Source-reviewed affine Q4/S3/beam recovery compiles via canonical zero/local
   basis probes under preparation guards. Random affinity checks are verification,
   not authority for arbitrary code. Preserve frames/stations/initial fields and
   generalized quantity availability. Pinned formulation files remain unchanged.
7. Full actual F, b=T.T@(F-K@u0), existing supported scaling/free-free augmentation,
   per-case backward error 1e-10, compatibility/multipliers/gauge/imbalance policy.
   Reactions preserve fixed/slave/master separation and full residual diagnostics.
8. Snapshot-aware ANYfem adapter covers ALL existing static load families. Freeze
   structural geometry/mappings; ingest case definitions once, run providers
   outside spans, digest actual resolved numeric loads. No whole-project scans.
9. Blocks default 32, reduced by resource policy; count factors/operators/workspace.
   Fail if one case cannot fit. Preserve cancellation, progress, early close,
   case-labelled failures, certified prior blocks and envelope identities.
10. Refuse unsupported requested capabilities explicitly, never silently call the
    live stream. Missing current ANYfem load-family coverage is a delivery gap.
11. Exact patterns are conditional on measured R1 removable-cost screen. No
    selected-response matrices; same recovery of certified q,F. No patterns before
    root's D3 decision. Archives/adjoints/approximation/new backends deferred.
12. Existing formulation/quantity-specific tolerances remain unchanged. Independent
    review of snapshot authority, mechanics and factor lifetime before acceptance.

## Ownership and progress

Root owns architecture, ANYfem integration contract, independent checks, benchmark
accounting, integration and acceptance. Mistral is assigned the connected solver
implementation (snapshot, load compilation, direct solve, recovery/reactions,
API, focused tests and examples) when available. No worker Git delivery.

Question: can immutable preparation eliminate repeated lifecycle/application
observation while retaining the exact fixed-model equations and all load inputs?
First discriminating result: public prepared direct parity on supported/free-free
beam/shell fixtures with source mutation and independent factor lifetime.

Implementation: not started. Correctness checks: none yet. Independent review:
pending. Benchmark time consumed: 0 / 600 seconds. Allocate <=120 pilots/profiles,
<=330 comparisons, reserve 100 holdout and 50 contingency. Root alone launches
benchmarks; failed attempts and warmups count. No hours-long campaigns.

### Implementation checkpoint: first candidates and repair ownership

Mistral availability established by successful source tools and actual candidate
writes. Initial solver run (80 turns) produced four prepared modules and tests,
then stopped without handoff after a failing S3 recovery check. Root review found
shared backend use, API mismatch, nonlinear derived measures incorrectly treated
as affine, insufficient admission/coherence, and incomplete resource accounting.
The same solver owner is repairing those in solver-worker-03.log (80-turn bound).
Root independent counterexamples and benchmark driver are implemented separately.

ANYfem Mistral runs (60 then40 turns) produced the adapter/facade and tests, but
both exhausted their turns without handoff; the continuation left a constructor
signature half-updated and ran no checks. The first run's mesh-copy failure
(22 failed,1 passed,1 skipped) remains preserved. This is incomplete execution,
not an accepted adapter. Root transfers application integration/repair to an
OpenAI worker because repeated incomplete execution and the live cross-repository
API boundary now require a reliably finished, focused integration slice. Preserve
Mistral's useful implementation; do not restart or change authorship retroactively.

Initial worker check wall accounting was incomplete. Solver enclosing tool-call
timestamps bound checks at about25s (conservatively charged30 of180s); the solver
continuation has150s remaining and uses the root process-wall runner. ANYfem first
test's exact process duration is unavailable; conservatively charge its85s timeout
against its180s initial allocation, leaving95s. ANYfem continuation used no new
numerical checks. These uncertainties are retained, not reconstructed by reruns.
No benchmarks have run. Root syntax check of benchmark driver passed in0.126s;
that is not a numerical verification or performance result.

## Delivery gates

- Solver direct + recovery/reactions; then ANYfem all-load integration and R1.
- R1: current exact stream vs prepared direct, same cases/outputs/runtime, complete
  built-model-to-consumed-output cost including factorization and preparation.
- R2 only after D3: count only work actually removed; require optimistic 2x bound
  and plausible finite-history benefit, otherwise DEFERRED_PERFORMANCE.
- Promotion: holdout-confirmed 2x speed or 50% lower peak memory with <=5% slowdown;
  otherwise NO_GO or INCONCLUSIVE. No unmeasured performance claims.

### Solver ownership continuation
The solver's second 80-turn Mistral run ended without handoff or checks and left
its checkpoint's public API and factor-lifetime repairs unimplemented. Useful
load/recovery/snapshot edits are retained. This repeated incomplete execution
requires a focused OpenAI fallback for the connected solver outcome; no prior
scientific acceptance is implied. Remaining solver check allocation is150s, with
no additional benchmarks consumed. Root retains independent mechanics review.

### Independent review, numerical screen and authority checkpoint

Candidate exists in both isolated worktrees; default routes are unchanged. Root
implemented the preparation-only comprehensive snapshot witness/digest as the
reserved cross-repository ownership contract; canonical calls retain their guards.
Mistral review attempts inspected mechanics/ownership but stopped without final
handoffs. A separate OpenAI reviewer (the application author, not solver author)
completed a read-only solver review and found four additional defects: instance
helper shadowing bypasses affine admission; oversized ingress packets escape the
memory estimate; iterator cleanup errors disappear; a provider can close the owner
and still receive a successful zero-RHS block. These are assigned to the solver
owner for repair and adversarial tests. They block acceptance.

Focused integration: ANYfem45 passed plus1 strengthened cache test; solver latest31
passed includes root9 independent tests. Existing impacted solver tests:184 passed,
5 fixture setup errors (sandbox temp-directory permissions); only those5 rerun with
an owned unique basetemp and passed. Existing impacted ANYfem suites61 passed.
Evidence/checks contains commands, exact source hashes/runtime, JUnit and full logs.
These checks do not establish the still-missing numerical/promotion gates.

Free8-case pilot: stream0.3971567s, prepared0.4111460s inclusive preparation; both
one SciPy factorization. Selected displacements meet prior stream tolerance;
near-zero beam stress arithmetic changes cause201 failures under the existing
compiled-recovery componentwise1e-12/1e-12 screen and4 governing-ID changes.
A discriminating2x2 diagnostic found identical operators, full-load difference
2.84e-14, displacement difference5.636e-15, and independent cancellation sensitivity
in canonical vs collapsed recovery. No tolerance has been relaxed. Complete
accuracy/ambiguous-envelope qualification is unmet; this is not a GO result.

Barge4-case baseline:30.3633193s including preparation/consumed selected outputs,
one PARDISO factorization. Prepared initial pilot exceeded60s; taskkill failed to
confirm cleanup. Follow-up Get-Process and psutil inventory found no surviving
owned benchmark. Preserve measured runner65.0822262s and conservatively charge
170.995014906s through the observed absence (actual child exit time unknown).
Runner now kills/waits only its psutil-owned process tree; disposable0.25s timeout
self-check completed cleanup in0.2845385s. No benchmark was rerun to reconstruct
missing accounting.

Subsequent profiling attempt (after replacing per-element mass probes by three
canonical acceleration assemblies) exited3221225477 during faulthandler traceback,
12.315315s, no complete result. Failed evidence retained, attribution unresolved.
Total conservative benchmark charge221.876375406 /600s;378.123624594s remain.
The proposed pilot allocation was exceeded by conservative cleanup accounting;
reduce remaining comparisons, preserve100s holdout reserve, never extend600s.
No promotion, integration commit, merge or publication has occurred. Principal
measures and canonical ambiguous-contender re-evaluation remain explicit delivery
gaps. Pattern work remains conditional and unimplemented.

### Matched primary screen and review continuation

The conditional pressure-preparation candidate completed the four-case barge
primary history (positions 0,198,396,594): prepared34.2073972s, including
33.0507313s preparation, versus exact stream30.8127058s. Peak process working
sets were677101568 and596779008bytes respectively; each used one PARDISO
factorization and zero stale rebuilds. This short history is not a speedup.
All1440 selected values were compared:78 failed the conservative uniform stress
screen, no governing identities differed; displacements/reactions passed their
screen. The uniform1e-12/1e-12 stress check originates in a von-Mises test and
must not be misrepresented as the established criterion for every quantity.
Keep these failures; record formulation-specific criteria and remaining gaps.

Benchmark records now include profile-barge-prepared-03 (40.0677205s timeout),
r1-barge-prepared-primary (37.128535s), a runner-argument failure (0.1066811s),
and r1-barge-stream-primary-02 (33.7686712s). Conservative cumulative charge is
332.947983206/600s, remaining267.052016794s. Numerical benchmarks are paused
while source repairs proceed. No automatic budget extension.

Independent read review found a P1 callback escape in the conditional pressure
span: mesh.elements.items() could be instance-shadowed although the proof uses
builtin dict.values. Assigned builtin iteration plus regression to the solver
owner. Prior four review defects and iterator-construction cleanup are repaired.
Latest pre-followup solver suite43 passed; ANYfem48 passed. These are development
checks, not acceptance. Canonical principal and envelope gates remain open.

Canonical refinement decision: permit private, snapshot-owned native local
recovery copies for cancellation-sensitive/principal outputs, supplementing
compiled affine operators. This implements the requested canonical refinement;
no caller model/session/mesh/element/material may be retained, ownership and
memory must be verified, and numeric recipe identity enters the snapshot digest.
It does not repair full-load/solve arithmetic differences or waive their checks.
Root retains the snapshot/digest contract; solver owner implements recovery.

Main checkouts remain untouched. Solver main stillcff55d95; ANYfem main advanced
externally to c7003679. The isolated implementation comparator remains frozen at
3e4eb7f; do not relabel it as the latest main or integrate unrelated dirty work.

## Final recorded candidate: NO_GO for promotion

The isolated implementation is a development candidate, not an accepted release.
Root integrated-final-01 passed97 tests (0 failures/errors/skips) with JIT enabled,
25.5927817 process-wall seconds and no source changes during the run. This covers
both prepared solver suites,9 independent contracts, the preserved canonical
principal regression, and both ANYfem prepared suites including nonempty stresses
and reactions. Two public example smokes also passed. The principal counterexample
now passes unchanged; a default-collected wrapper keeps it in ordinary pytest.
Earlier impacted checks passed189 solver +61 application tests; their original
manifests identify the earlier source and the5 temp-fixture errors/repaired rerun.
Do not count repeated runs as additional distinct tests.

Independent review identified and source-checked repairs for provider/helper
admission, ingress packet memory, iterator cleanup/reentrant close, pressure
mapping method shadows, yielded DOF header aliases, canonical local executable
authority, and owned mapping storage. The final bounded review found no further
concrete ownership defect in that slice. It does not establish numerical or
performance acceptance. Mistral reviews were incomplete; completed review was a
separate OpenAI author. Failed cloning/refinement runs remain in evidence/checks.

R1 final free-free measurements, complete built-model-to-consumed-output seconds:

| History | Exact stream | Prepared | Result |
|---|---:|---:|---|
|100 primary samples, cold owner|2.548207700|4.983053300|0.5114x speedup (slower)|
|100 same samples, reused owner|2.330317400|4.359423500|slower; same-owner bits identical|
|200 distinct holdout samples|4.727354300|9.174315900|0.5153x speedup (slower)|

All these runs used one SciPy numerical factorization per owner and zero stale
rebuilds. Holdout peak process working sets: stream198373376bytes,
prepared197812224bytes, far short of50% savings. The comparison sink intentionally
retains selected values; this is not an isolated evaluator-memory qualification.

Primary/holdout compared23200/46400 values. Displacements and reaction checks
passed. The unchanged conservative uniform stress screen records2892/5309
failures;6/4 governing envelope identities differ. Quantity-specific acceptance
must use the evidence map, not indiscriminately apply a von-Mises tolerance to
all fields. Near-zero beam cancellation, full-load/solve rounding and canonical
inter-case envelope contender reevaluation remain unresolved. No tolerance was
relaxed. This blocks numerical acceptance independently of the speed regression.

Earlier four-case barge screen: stream30.8127058s versus prepared34.2073972s,
including33.0507313s preparation. That prepared source predates the final local
refinement; do not present it as a final-source performance result or extrapolate
it into a measured long-history speedup. No final supported-family holdout claim.

D3: patterns DEFERRED_PERFORMANCE. The recorded barge solve/reduction fraction
permits only about1.057x optimistic evaluation speedup before basis overhead;
input/fullF/recovery/output remain. Free-first-solve timing cannot establish warm
removable work. Open R1 numerical gates independently prevent pattern promotion.
See evidence/PATTERN_SCREEN.md; no PatternCase API was introduced.

Benchmark campaign stopped at370.299613306/600 cumulative process-wall seconds,
including warm/reused evaluations, failed invocations, timeouts/profiles and the
conservative170.995014906s cleanup upper bound.229.700386694s remain unused.
The stop is decision-oriented: the holdout confirms a substantial regression and
accuracy/envelope gates remain open. This is not permission to renew the cap.

Remaining obligations before merge: complete bounded canonical contender handling
and full-load/solve roundoff adjudication; remove or reduce the measured recovery
and authority overhead without weakening guards; remeasure both workload families
on the repaired frozen source; qualify memory behavior and all requested quantities.
No commits, merge, push or package release were made. Main checkouts/unrelated dirty
work are preserved. Solver and ANYfem candidates remain separately reviewable in
the recorded codex/prepared-static-evaluator worktrees. All owned jobs have ended.

Final phase adjudication: prepared primary recovery4.093226100s versus stream
0.655964100s accounts for the observed regression; prepared load evaluation was
0.002628300s versus stream load assembly0.981017000s, a phase-only improvement.
Refinement/authority subcosts were not separately profiled. Free primary and
holdout solve+reduction fractions now also bound patterns to roughly1.05x even
with zero basis overhead, confirming DEFERRED_PERFORMANCE for both families.
No extra numerical runs were needed for this analysis of existing records.

## Milestone 2 — whole-model envelopes, authorised 2026-10-08

Prospective transition: implement the user's accepted next-step plan targeting
10,000 arbitrary static cases, whole-model envelopes and selected detailed
histories. Preserve the entire previous candidate and all failed evidence.
The existing benchmark ledger remains370.299613306/600s; remaining229.700386694s.
Allocate at most30s profiling,65s comparisons,100s confirmation/holdout, remainder
contingencies. No full10,000-case qualification or automatic cap extension.

Principal question: which part of canonical recovery causes the measured
regression, and can package-owned block execution preserve canonical arithmetic
while removing repeated authority and per-case object construction? Profile the
frozen candidate before changing the recovery path. Distinguish authority,
kinematics, stress/derived calculations, reactions and result construction.

The prior Mistral attempts repeatedly exhausted their turn bounds without usable
handoffs. Continue the established connected OpenAI solver and application owners;
retain separate independent review. This is execution-reliability fallback, not
scientific acceptance or a claim of different-model-family review.

New milestone ownership: solver worker owns the complete prepared solver subsystem
including snapshot/load/recovery/envelope integration and tests; application worker
owns the matching opt-in ANYfem adapter/facade/examples/tests. Root owns frozen
baseline, profiling/benchmark tooling, independent checks, contract decisions and
integration. No worker benchmark, Git integration, pinned-source/default-route
edits or sibling ownership. Previous check budgets/evidence remain consumed.
New-scope correctness allocations: solver180 process-wall seconds, application90,
root integration/review120. These are checks only, not renewed benchmark authority.

M2 profile (`m2-profile-baseline-01`, 7.004610 process seconds): 16 cases on the
frozen previous candidate attributed 3.160639 of 3.789381 profiled seconds to
96 native authority checks; Q4 native stresses 0.530366, beams 0.008525,
derived measures 0.003725 and reactions 0.004578. Profiling overhead is present:
these are attribution evidence, not speedup measurements. Evidence includes raw
pstats and JSON; no expensive parameter sweep was justified.

Initial new driver smoke comparison (free 4 cases, selected histories plus all
model stress/reaction envelopes) compared 379,856 values bitwise, no governing
identity differences. Cold stream/prepared 0.540542/1.261700s, reused
0.319652/0.431969s. The tiny fixture does not amortize setup; no promotion claim.
These invocations consumed 3.553554 + 3.994257 process seconds. Current cumulative
benchmark ledger 384.852034406/600s; remaining 215.147965594s.

Independent application-owner review identified missing native trusted-scope
factory binding authority and final completion revalidation after caller input
cleanup. The solver owner is repairing both before further timings. Earlier
failed tests and profile data remain intact. No tolerance change or budget renewal.

### M2 final handoff — 2026-10-08

Implemented and independently reviewed the additive whole-model envelope route,
canonical full-load/recovery repairs and block authority. Both concrete independent
findings (trusted-scope factory authority; completion after input cleanup) are
resolved and have regression coverage. Native staged execution currently uses
grouped1element×1case fallback tiles; vectorized recovery remains a limitation.
All model/formulation/default implementation files remain unchanged; additive
exports and prepared modules/tests/docs are in isolated worktrees.

Final root checks:66solver+60application passed. Existing impacted suite110passed,
1backend-selection failure; that exact test also fails on unmodified main under
the same effective runtime. Main advanced independently to da1ba2e9 (modal/CI-only
differences from cff55d95; recovery source/test unchanged). Main ANYfem independently
advanced to f74812d9 with unrelated dirty work. No main source was edited here.
Root check use90.925307600/120s; solver worker90.4013583/180s;
application worker73.4583128/90s. All intermediate failures are preserved.

Screen disposition **NO_GO for performance promotion**; barge INCONCLUSIVE.
256case holdouts: free stream5.8186s/prepared5.2405s (1.1103x), supported
5.4451s/5.3936s (1.0096x). Peak memory is slightly higher, not50%lower.
All2,959,664 compared binary64 values and governing identities match exactly.
Candidate accumulator dimensions are fixed and retained estimates remain about
4.23MB over16/64/256cases, with no retained history list; no10,000-case measured
boundedness claim. The primary-based supported projection underpredicts holdout
by16% and is not confirmed. Neither projection meets2x.

Both4case barge attempts stopped at25s limits without delivered blocks, with dead
process trees confirmed. No rerun/extension. Final benchmark ledger
524.545961906/600s, leaving75.454038094s unused. M2 allocation use: profiling7.004610,
comparisons59.802707100, confirmation62.368828200, contingency25.070203300.
Timed CPU coordination ended; no owned jobs remain. No commit, merge or push.

Full report: docs/PREPARED_STATIC_M2_SCREEN.md. Machine-readable results, runtime
preflight, source identities, projection arithmetic and metadata-only10,000sample
uniqueness check: ../evidence/M2_SCREEN_RESULTS.json. Independent review:
../fem/.prepared-static-evidence/prepared-m2-independent-review.md. Exact commands,
durations, JUnit and complete output: ../evidence/checks/m2-*/.
The prior candidate archive and failed evidence are unchanged. Response patterns,
new backends, approximation and full10,000case qualification remain deferred.

### M3 bounded staged recovery prototype — authorised follow-up

User approved the proposed focused implementation, not another benchmark campaign.
Investigate removable repeated Q4 recovery operations, then implement a narrow
staged element/case tile if canonical arithmetic and authority can be preserved.
Retain exact governing identity criteria, transactional updates and native fallback
for unsupported features/formulations. Pinned/default mechanics remain unchanged.
M2 candidate frozen in ../evidence/m3-starting-candidate.zip with SHA manifest.
Prior Mistral exhaustion remains cached; same connected solver owner continues.
Root owns contracts, evidence, independent review and integration. Source ownership
is confined to prepared modules/new prepared tile kernel, focused tests and docs.

No new benchmark/profile/scaling runs authorised here; remaining75.454038094s is
not being spent or renewed. Use unspent correctness allocations: solver89.5986417s,
root29.0746924s. If required checks cannot fit, preserve prototype and report the
specific unmet check; no gate waiver. Early design checkpoint identifies concrete
removed work, kernel eligibility, arithmetic staging and memory bound before tuning.
No merge/publication; M2 performance NO_GO remains unless separately remeasured.

M3 source decision: native Q4 `_recover_planar_mixed_fields` rebuilds equation7
geometry/Jacobians, constitutive data, the35field stationary solve and four station
maps per case. Existing classic MITC4 `recovery_s4` is not this formulation.
Adopt a narrow exact qualified planar homogeneous Q4 route without Hill/initial
fields, hoisting invariant native stages into owned data. Retain canonical staged
GEMV/layout per physical case inside bounded1element×case tiles; no flattened
operator/GEMM reassociation. Opposite directors/rotated or skewed planar geometry
must preserve canonical results. Other features/formulations continue native
fallback, preserving all-load API capability. Activation and removed stationary
solve call counts are correctness evidence, not a measured speedup.

M3 implementation: `prepared_static_q4.py` captures native invariant geometry,
constitutive/stationary solve and station maps in independently owned immutable
buffers, preserving C/F layout. Shared recipe dispatch activates the staged route
for both selected histories and envelopes. Other features retain reasoned native
fallback. Runtime kernel binding/code/class facts are checked around numerical
spans; staged storage is included in snapshot digest/accounting. No pinned source,
default route, factor lifetime or ANYfem product code changed in this slice.

M3 verification (JIT enabled, existing interpreter/harness):
- m3-solver-01:1passed,4.9887507s; old000/048/576 exact governors/full recovery.
- m3-solver-02:7passed,5.1596742s; rotated/skewed opposite directors/multiple
  scales, immutable stages, no repeated stationary solve in arithmetic kernel,
  native and staged executable mutations, warped fallback/public activation.
- m3-solver-03:40.0489397s timeout;73pass dots/no failure printed, no completed
  JUnit summary. The broad suite remains explicitly incomplete. Dead tree confirmed.
- m3-solver-04:15passed/6deselected,16.9928113s;1/8/32public activation,3explicit
  eligibility predicates and9ANYfem integration cases including nonproportional
  balanced free-free history. Predicate tests do not newly qualify excluded physics.
- m3-root-independent:1passed,10.4496289s;33distinct cases/repeatedlabels with
  block1/8/32/restarts, all displacement/stress binary64 values and whole-envelope
  governing times/indices/identities/associated fields exactly match native stream.

Independent Read review found no concrete defect in the bounded slice; final
product hashes match the reviewed sources. Review/evidence limits at
../fem/.prepared-static-evidence/prepared-m3-independent-review.md. No source
changed during numerical checks. Completed checks establish a bounded prototype,
not full numerical/performance qualification or broad-suite completion.

M3 worker check use67.1901759s, leaving22.4084658s of its existing180s allocation
after prior M2 use. Root remaining18.6250635s of120. No benchmark/profile jobs:
ledger remains524.545961906/600s,75.454038094unused. M2 performance NO_GO remains
historical baseline evidence; M3 speed/memory benefit is unmeasured. This is
invariant-stage hoisting with canonical per-case GEMV, not SIMD/multiple-RHS
reassociation. No broader backend/pattern/10,000-case campaign or publication.

### M3 benchmark follow-up — user authorised

Use only the remaining75.454038094process-wall seconds, without renewing600s cap.
Question: does invariant-stage hoisting improve complete envelope/history workloads
while retaining exact values/governors? Frozen M3 source, same driver/settings and
native stream comparator, serial alternating routes. Start64primary supported/free;
run256distinct holdout only if estimated remaining cost fits. Include cold setup,
reused owner, all output, peak memory and retained accumulators. Preserve old failed
barge evidence; no repeat of its25s attempts. No implementation tuning during screen,
no automatic extension or merge. Numerical accuracy/2x-or-memory criteria unchanged.

M3 benchmark completed: all8processes exited0 with stable identical source hashes,
effective JIT enabled/threads1 and1SciPy factorization per owner. Primary64 cold
stream/prepared: free1.6468/2.0774s; supported1.7495/1.8850s. Distinct256holdout:
free5.514806900/3.947923800s (1.397x), supported5.443882000/4.005157000s (1.359x).
Reused holdouts free5.316106500/3.195962800s (1.663x), supported
5.235410500/3.245409000s (1.613x). All1,808,960binary64 values/governors match exactly.
Candidate peak process memory is slightly higher, not50%lower. Retained accumulator
dimensions remain fixed across64/256; no10,000case boundedness claim. These6element/
8node fixtures do not establish production barge speed or memory. Descriptive
two-length projections include holdout in the fit and are explicitly unvalidated.

Decision remains NO_GO for2x/50%memory promotion; retain demonstrated smaller gain
as evidence. No barge reruns/tuning/merge. Current benchmark consumption
590.971911206/600s,9.028088794unused; follow-up used66.425949300s. All numericaljobs
ended and CPU-coordination completion sent. No source edits or new correctness
checks during this benchmark. Full results: ../evidence/M3_BENCHMARK_RESULTS.json;
updated public report: docs/PREPARED_STATIC_M3_PROTOTYPE.md.

### M4 shared recovery and block envelopes — authorised

User approved the combined implementation and explicitly renewed benchmarking
with120cumulative process-wall seconds including warm-ups/failures. Keep the prior
ledger590.971911206/600s intact; its9.028088794s is not added to the new allowance.
New benchmark epoch m4 has120s only. Root owns timings/ledger, with short serial
matched baseline/candidate runs and distinct holdout after correctness review.
Compare complete same-scope envelopes plus selected histories; preserve exact
values/governors,2x-or-memory criteria and no automatic extension or publication.

M3 candidate frozen before edits in ../evidence/m4-starting-candidate.zip with
SHA manifest; full source comparator in ../m4-baseline/solver/src, identity at
../evidence/M4_BASELINE_SOURCE_MANIFEST.json. Native stream remains another useful
comparator; historical runs alone cannot attribute the incremental M4 benefit.

Same solver owner continues under cached Mistral-unavailability fallback. Owned
subsystem is prepared recovery/envelopes/driver integration and focused tests/docs,
no pinned/default sources, API changes, sibling edits or Git. Root owns livingnote,
bench tools, independent checks/review/adjudication. New-scope M4 correctness
ceilings: worker120process seconds, root60; previous allocations remain consumed
and separate. These are correctness checks, not uncharged performance runs.

Principal question: remove duplicated selected/envelope recovery and reaction
diagnostics, then avoid per-case component/associated-field accumulator updates.
Use canonical physical fields once, bounded element/case tiles and exact block
winners; preserve earliest input ties, signedabs values, coherent associated
components, no scopes across observers, failure atomicity and memory refusal.
Consider staging deltas instead of whole accumulator deepcopies only where safe.
No change to physics, scientific tolerances, factor lifetime or native fallback.

### M4 completed implementation and bounded screen

Shared canonical recovery/reactions, eight-case winner tiles and copy-on-write
transactions implemented; independent selection and authority findings repaired.
Source and review frozen; no pinned/default mechanics or FEM product edits in M4.
Root2 independent tests passed14.8567242s; worker checks81.3771391s with preserved
four initial test-oracle failures subsequently repaired without tolerance changes.
Detailed run counts/commands in docs/PREPARED_STATIC_M4_SCREEN.md and evidence.

Renewed benchmark epoch used115.712200200/120s,4.287799800unused; all14processes
completed. Prior590.971911206/600ledger untouched. No further numerical jobs.
Contemporary64primary/256distinct holdout compares frozenM3 and native withM4.
4,114,704 binary64 comparisons exact including associated fields and governors.
256cold native/M4 ratios2.043free,1.991supported(1.996repeat); reused2.822free,
2.715supported(2.739repeat). Incremental M3/M4 reused1.762free/1.623supported.
INCONCLUSIVE strict cold2x both families; demonstrated improvements retained.
No50%memory reduction. Fixed accumulator dimensions measured64/256, not10000.
Tiny6element/8node projections62.6/68.1s M4 vs208.7/212.7native are unvalidated,
not production barge or10000case qualification. No merge/commit/push performed.

User withdrew meshing-chat coordination during timing; no further messages sent.
Final manifest/delta: evidence/M4_FINAL_MANIFEST.json,M4_REVIEW_DELTA.patch.
Results: evidence/M4_BENCHMARK_RESULTS.json. Report: docs/PREPARED_STATIC_M4_SCREEN.md.
All candidate changes remain in isolated worktrees; unrelated main work preserved.
Final ownership check: product source delta against frozenM3 is exactly
prepared_static.py,prepared_static_envelopes.py,new prepared_static_shared.py.
All benchmark manifests report stable sources/completed status. Main solver now
has concurrent tracked changes in e4_pl_element.py,elements.py,sesam_fem/importer.py;
these were not edited or included here. Main FEM unrelated tracked work remains.

### M5 numeric envelope recovery — authorised

User accepted dictionary-recovery optimization and renewed the allowance. Use
fresh120cumulative benchmark-process seconds (epochm5), matching prior renewal;
oldM4=115.712200200/120 and legacy590.971911206/600 remain separate and consumed.
Frozen M4 source comparator captured ../m5-baseline/solver/src before edits.
Principal question: is repeated field-record construction/filtering sufficiently
large to justify direct numeric staged recovery into bounded tiles? Root charges
one short cProfile to epochm5; owner may design while it runs, no competing jobs.
If dominant cost is elsewhere, record evidence and adopt only a compatible narrow
change. No broad newbackend/basis/physics effort, tolerance relaxation or release.
Same implementation owner continues cached Mistral-unavailable fallback; root
owns independent review, benchmark, gate and task note. New correctness ceilings:
worker120process seconds/root60, separate from benchmarks. Preserve all failed
prior evidence. No meshing-chat coordination per user's latest instruction.
M5 profile completed10.181085500process seconds,109.818914500remaining.
Profile combines preparation and64cold+64warm; timings are instrumented cumulative,
not additive wall phases. Shared recovery0.902s, Q4stages0.09s, numeric field discovery
0.07s, deepcopy0.05s, selected wrapper0.01s. Dictionary target is modest, not dominant.
Proceed limited single canonical tuple-core extraction plus compiled field selectors;
no cross-case arithmetic reassociation. Native/explicit principal fallback retained.
Do not broaden into physics or responsebasis. Matched screen may record NO_GO.

### M5 completed experiment — NO_GO

CanonicalQ4numeric20field core + detached detailed wrapper/direct envelope tiles
implemented, native/principal fallback preserved. Selectors per element/block.
Product delta exactly prepared_static_q4.py/shared.py,new numeric regression tests.
Independent source review no findings;9+42+29worker tests and3root tests passed.
Worker correctness50.1926619/120s;root18.7964503/60s. No M5 test failures.

Matched64primary/256distinct holdout and reversed256repeats all exact:
2,802,528binary64values,zero differences/governing mismatches. Free256cold slower
11.7%/5.8%,warm slower3.1%/4.2%; supported varied nearzero except5.1%warm gain
on repeat. Profiles confirm fewer record constructions but not reliable wall gain.
NO_GO performance promotion;stop rather than expand scope/tune acceptance.
ExperimentalM5 remains unmerged in isolated tree; fullM4 predecessor preserved
at m5-baseline/solver/src and main repositories untouched by M5.

M5benchmark epoch93.142273100/120s used,26.857726900unused; includes2profiles and
12unprofiled processes,all completed/stable. Earlier ledgers unchanged. No more
jobs or meshing-chat coordination. Evidence:M5_BENCHMARK_RESULTS.json,
M5_FINAL_MANIFEST.json,M5_REVIEW_DELTA.patch under evidence. Fullreport:
docs/PREPARED_STATIC_M5_SCREEN.md. No commit/push/merge or10000case qualification.

### User selected M4; active candidate restored

User: "Ok keep M4. Next step". Verified M5 source hashes before restoration.
Archived M5 Q4/shared sources,numeric-only test,and former guide under
../evidence/m5-experiment. Restored exactly two product files from full frozenM4;
all active solver Python source hashes match m5-baseline/solver/src. Removed only
M5-specific test from active collection by moving to archive; failure/performance
reports/manifests/profiles remain intact. Guide now accurately identifies M4.
No numerical runs necessary for byte-identical restoration; no budgets renewed,
no commits/merges/pushes. Historical M5 final manifest identifies archived content.

Recommended next step: representative built-model M4 pilot before more tuning.
Prior timing fixtures were6elements/8nodes. On a representative supported/free
mixed model, separate load evaluation/assembly,recovery,reaction and output costs;
then select load-map reuse only if it dominates and preserves arbitrary fields,
changing wetting,envelopes and added masses. No new campaign launched by this
handoff; existing stopped benchmark ledger remains unchanged.

### Representative M4 pilot — new authority

User explicitly approved fresh120cumulative process-wall seconds for representative
pilot including preparation/profiling/failures. New epochrepresentative; earlier
ledgers remain unchanged (M5residual26.8577269 not added). No solveroptimization
or product edits. Main question: which cost dominates real application workflow?
Full0.7mfixture4348nodes/3185Q4/1060beam/1248couplings cannot be assumed short;
Q4associated floats alone497664bytes/element imply~1.59GB for fullQ4envelopes
before headers and multiplecopies. Attempt completegeometry2mfixture under25s,
then enforce memorypreflight and boundedprofile. Do not truncate mechanics or
claim coarsefixture equalsproduction accuracy. Preserve loads/connections/supports.
Root owns execution/accounting; established worker owns evidence-only pilot harness
under cachedunavailabilityfallback. No worker numericaljobs. No meshchatcoordination.

### Representative pilot stopped with actionable preparation evidence

Epochrepresentative used117.358330200/120s,2.641669800unused. Fourattempts:
completegeometry2mmesh15.326198s(countsunchanged),fullbargeprofile60.0927755timeout,
8body48elementfreecontrol11.8746193complete4cases,isolatedloadmaps30.0647374timeout.
Timeouttrees dead/sourcesstable. M4productsource unchanged. No furtherjobs.

Barge eventsadmitted6.137,stiffness24.992,constraints25.960s; no loads event or
certifiedcase. Constraintscallbackfollowedby sourcewitness then loadmapcompiler;
do notattribute entireinterval solely tocompiler. Isolated actualcompiler after
build+BC/noK sampledpressurethen3completegravity/massmatrix stacks atunitaccel
assemblyline867. Sourceconfirmed3unitassemblies,ownedmasscaptureagain,verification
later; infer promising preparationreuse target, not quantified savings or permission
to dropcanonicalindependentchecks. IndependentRead review requested/completed.

Wholeallfieldmemorylowerbound~1.59GBQ4associatedfloats beforeotherstorage led to
explicit narrowerwhole-vonMises+reactions pilot/selectedfullhistory,1GiBcap.
Noallresultants/10000case/productiontimingacceptance. Freecontrol4certifiedcases,
phase/recoveryevidenceonly: exploratoryJSONskipkeys suppresses tuplekeys so no
serializationclaim. cProfile restartatcallbacks makes parentinclusiveprepstats
noncontiguous; use wallstages. Full reportdocs/PREPARED_STATIC_REPRESENTATIVE_PILOT.md;
ledger evidence/REPRESENTATIVE_M4_RESULTS.json. Nextcandidate mass/acceleration
preparationreuse while preservingguards/allloadsemantics/independentoracles.
Investigation did not authorize productfixes; none implemented.

### M6 mass/acceleration preparation — implementation authorised

User Proceed authorizes bounded implementation of last recommendation. Fresh
benchmark allowance asked asynchronously; pending answer NO M6 timed execution.
Runner m6 epoch declared120 only for bookkeeping; declaration is not authority.
Prior representative117.3583302/120 remains stopped/separate. New correctness
ceilings worker120/root60process seconds. Same owner continues cachedMistral
unavailable fallback; no pinned/default sources, FEM product edits or Git.
FullM4product baseline copied before edits to ../m6-baseline/solver/src.

Principal question: obsolete3unitacceleration basis generation vs actual runtime
massmaps and retained oracle. Determine whether removing unused artifact avoids
repeatedmasswork without newcache or altering canonical verification. Preserve
independentfullF oracle, structural/point/caseaddedmass/activity, exactstaged
arithmetic/order and authority/cancellation/refusal. Owner must trace references
and obtainrootadoption for compatibility/criteria changes. Current task is fixing
preparation, not widening physicalscope or droppingguards to get a pass.

M6 first implementation completed102 passing checks in40.8287917 correctness
process-wall seconds. Independent Read found a refusal regression: native invalid
mass could reach the unchanged oracle outside the capability catch. Same owner
is repairing this using captured-mass unit applications without recomputing native
mass or retaining unused basis data. Final review/checks await source freeze.
Benchmark renewal remains pending; no M6 benchmark executed or inferred authority.

### M6 implemented and independently reviewed; benchmark pending

Final product delta only prepared_static_loads.py; SHA25652e00c5fa62244b2e2597418d4ba92a078d772630116465387445ac8650cfef3.
Removed unused basis/native unit assemblies; preserved unit capability checks via
captured mass applications. Runtime evaluator and full-F oracle text-identical.
Independent P2 refusal finding fixed, final Read clear. Worker129 passing test
executions across five attempts (repeat selections),50.1688495/120correctness s.
Root4independent checks pass: first2failed due to wrong harness pointmass API,
then corrected2pass; other2passed first run and not repeated. Failure preserved.
Root20.04735/60correctness s. Binary full-F Q4/beam/S3, governed envelopes and
block/restart/alias checks pass. No benchmarks or measured savings. Renewal still
pending; no authority inferred from runner epoch. Reportdocs/PREPARED_STATIC_M6_IMPLEMENTATION.md;
manifest../evidence/M6_IMPLEMENTATION_RESULTS.json. No Git publication.

### M6 benchmark authority renewed

User explicitly grants fresh120 cumulative process-wall seconds. No pooling with
prior epochs. Question: does eliminating redundant native mass preparation save
representative preparation time, and does it help complete small mixed workflows?
Serial matched baseline/candidate acceleration-only full-barge preparation first
(max25s each), preserving full-F verification; then affordable complete supported
and free-free controls with identical selected histories/envelopes. No profiling
or instrumentation overhead; record phase/total durations, digests and RSS. Avoid
claiming isolated compiler gain as full-barge or 10000-case speedup. Stop within
120including failures; source baseline remains m6-baseline/solver/src.

### M6 renewed screen complete; stopped

Twelve serial runs108.6796952/120process-wall seconds;11.3203048unused. All complete,
stable sources. Fullbarge acceleration-only preparation17.191/17.139baseline vs
10.124/10.015candidate seconds;41.1–41.6%reduction,~7.1ssaved. FourfullFdigests exact,
canonical oracle0.0. Isolatedstage gain not fullworkflowclaim. Complete64case
supported/free controls with reverseorder distinct holdout show modest/inconsistent
coldgains; no repeatable>5%regression;2,443,712 binary64 output comparisons exact,
governingidentities exact. Warmruntime unchanged; no savings attributed. RetainM6
preparationoptimization; incremental2x/50%memory screenNO_GO, no10000qualification.
Reportdocs/PREPARED_STATIC_M6_SCREEN.md; evidence/M6_BENCHMARK_RESULTS.json records
fullaccounting; no furtherjobs and no publication. M4othercode/M5archive intact.

### M7 representative recurring-cost milestone

User approves recommended pilot/optimization and600 total cumulative benchmark
process-wall seconds for this milestone. Fresh epochm7; prior11.3203048unused
is not added. Root exclusively schedules numerical benchmarks, including failures,
warmups/profiling. Freeze current M6 to ../m7-baseline/solver/src. Same implementation
owner continues cached Mistral-unavailable fallback, with complete prepared-subsystem
ownership; no default/pinned/FEMproduct edits, publication or renewed physicalscope.
Correctness ceilings worker120/root60seconds separate from benchmark600.

Decision question: which repeated cost dominates complete representative barge
execution—application loads, solver loading, recovery, reactions or envelopes?
Start complete bounded2case unprofiled baseline (wholevonMises+reactions, selected
physical fullhistories,1GiB cap), then case-only profiling as needed; do not conflate
preparation with recurring work. Adopt one measured target and preserve canonical
arithmetic/authority/transaction semantics. Paired distincthistory supported/free
confirmation within remaining600; no automatic extension, no10000qualification.
Worker first repairs existing pilot tuplekeyserialization and provides fresh harness
without modifying original failed evidence. Maincheckout unrelated work untouched.

M7 first fullbarge baseline120.1016122stimeout beforeloadsevent; trace-only60.0856968s
timeout samples40/50s broad native authority checks in pressureverification. Budget
180.187309/600;419.812691remaining. Important source correction: actualcaseblocks
already own a surrounding recovery scope; verification lacked it. Adopt minimal
pressure-verification prepared-side scope (canonicalfullF oracle staysoutside),
then completepilot before selecting runtime optimization. Per-element load-routing
checks remain runtime hypothesis, not yet measured cause. Original failures retained.

User additionally authorizes root to update budget as needed for concluding
development. Current epoch limit remains600 until a justified recorded extension;
worker budgets/concurrency do not multiply. Source/acceptance/release gates unchanged.

M7a pilot120.0971135stimeout afterloads42.4437, no recovery/case output. Ingress
review found exactrecord foreignpayload path from replaced ingestion; repaired
beforeinvocation,8regressionspassed3.7228461s; frozenM7a remainedpre-fix interim.
Recovery-specific representativeprofile5.6853057s exposed49authorityaudits1.6359s
of2.8236s profiledcompile, plus wrongrequested VM oncoupling. Failedtrace preserved.
Adoptexplicit physicalQ4+beamstressselection(allcouplings staymechanics/reactions),
and captureoutside/owned-schema-scope optimization; retain canonicalarithmetic,
sourceauthority/exceptionchecks and typed missingcomponent refusals. Profile
sample48physicalelements is diagnostic, not a fullbarge timing or finalacceptance.
Benchmarkspend305.9697282/600;294.0302718remaining.

M7b tracedpilot native0xC0000005 at11.6053157sduringunchangedstiffness; no modifiedcode
reached. Faulthandlerfirstsample partial; causeunestablished. Actualtimestamps show
workercheck05 began1.34sAFTERcrash, no numericaloverlap. Untracedretry120.1050491s
completedcold2cases+envelopes106.7769s, then certifiedwarm2cases beforetimeoutduring
warmdetach. Preserve coldcomplete vs overalltimedout distinction. Preparationend
89.943sfromharnessstart; case recovery3.98/3.75s dominates solverloading.32/.77s.

Using explicit user authority to updatebudget, extend M7 TOTAL600→1200s (not fresh
1200):437.680093alreadyused,762.319907remaining. Needcase-onlyprofile(~150cap),
matchedcandidate and distincthistory/referencefreecontrols; no unattendedcampaign.
Freeze finalreviewedM7bto../m7b-final/solver/src for comparison. Hypothesis wasted
fullentrydictcopy in empty_subset perentity, plus repeatedstoragewalks; profile
beforetargetadoption. Bothauthorityreviewfindingsclosed with source/testevidence.

FinalM7bcase-onlyprofile completed108.0079055s, wholecoldinclserialization valid;
benchmark545.6879985/1200. Profilednext13.9001s: nbytes5calls6.7756s, recursive_storage
7.19millioncalls; recover_shared5.0731s; empty_subset4246calls.9094s. Inclusivefigures
notadditive. Adopt M7c exactprivatebytecache with mutationinvalidation and SAME_storage
recomputation, plus emptytransactions avoiding discarded fullentrydictcopies.
Newtransactionsuncached(dictcapacitymaydiffer); no changed arithmetic, ties, memory
criteria, callbacks or factorownership. Independentreview tasked accounting and
transactionalias/failure edges. No numericalworkerjob overlaps rootbenchmarks.

## M7 final checkpoint — 2026-10-08

Implemented and verified in the isolated candidate; no commit, merge or push.
The final product delta from M6 is confined to prepared_static_loads.py,
prepared_static_recovery.py and prepared_static_envelopes.py. Exact source hashes
and frozen comparison identities are recorded in ../evidence/M7_RESULTS.json.
The final solver source matches ../m7c-final/solver/src. Default and pinned
formulations, caller factor ownership and numerical tolerances are unchanged.

Independent review closed the ingress-authority, transitive principal-helper and
transaction entity-key alias findings. Root's final importlib-mode verification
passed 104 tests in 38.7596062 process-wall seconds. The preceding duplicate-test-
basename collection failure (8.5932301 seconds) remains preserved: root check
usage is 47.3528363/60 seconds. Worker focused checks recorded 130 passing test
executions across intermediate/final versions, using 50.8798155/120 check seconds;
these overlap and are not 130 additional distinct final tests.

M7 benchmark use is 1152.4490478999796/1200 cumulative process-wall seconds,
including profiling, failed runs and timeouts. The remaining 47.55095210002037
seconds are unused; the campaign is stopped. Earlier epochs remain closed.
Barge holdout warm history fell 29.7167756 to 23.2570623 seconds (21.7% reduction).
Free-free 64-case holdout warm history fell 8.7756086 to 8.1432886 seconds (7.2%).
Barge complete cold gains were 2.2–5.3%; preparation dominates. Physical outputs,
associated fields and governing identities match exactly. Free-free comparison
also checked 106,272 binary64 values exactly. Peak memory did not materially fall.

Retain the incremental candidate; the 2x complete-workload / 50% peak-memory
promotion screen is NO_GO. No measured 10,000-case qualification or projection-
based acceptance is claimed. Representative stress envelopes cover all physical
Q4/beam von Mises locations, with all-node reactions and selected detailed
histories; this is not every-component qualification. Failed evidence is retained.

Final report: docs/PREPARED_STATIC_M7_SCREEN.md.
Machine-readable evidence: ../evidence/M7_RESULTS.json.
Independent review: ../fem/.prepared-static-evidence/prepared-m7-independent-review.md.
Final test logs: ../evidence/checks/m7-root-final-importlib/.
Implementation handoff: .prepared-static-evidence/m7-solver-handoff.md.
No further numerical execution is needed for this development screen.

## M8 source-response implementation — authorized 2026-10-08

The user approved the revised source-based response reconstruction plan. Preserve
M7 and all earlier failed evidence. New benchmark epoch M8 has a 600 cumulative
process-wall second ceiling; no pooling with prior ledgers. Correctness checks
start with separate 120-second worker ceilings and a 120-second root reserve;
all process commands/status/timing/effective settings must be recorded. Numerical
jobs are serialized by root during timed runs. No merge/push is authorized.

Implement opt-in prepare_static_response_evaluator and ANYfem's corresponding
factory, PatternCase alongside StaticCase, owned baseline/homogeneous response
columns, sparse active coefficients, full-state per-case 1e-10 certification,
free-free multipliers and per-body compatibility, complete reactions and derived
measures. Retain original-time canonical fallback for mandatory governing IDs.
No credible contender bound currently exists: canonical replay of all unresolved
envelope samples is the required safe starting point; report its cost honestly.
Do not claim a cheap residual certificate until independently justified including
rounding, source discrepancy and denominator LOWER bound. It is conditional.

ANYfem periodic-source adapter must preserve full clipped pressure; declared
period/grid/source admission, no expression-name hardcoding or interpolation.
The frozen 600-case representative has nominal 60 phases, external pressure ramp,
one independent moment and no gravity. Full library prep cost counts. Sparse
samples activate phase + moment. Arbitrary other cases stay direct. An old-time
sin recurrence is not bit identity; unsafe source equivalence falls back.
Outputs: whole-model physical stress/resultant/reaction envelopes plus selected
histories; default APIs, tolerances, pinned formulations and caller factor owners
unchanged. 2x complete speed or 50% RSS reduction with <=5% slowdown are promotion
gates, not implementation assumptions. Budget exhaustion/NO_GO does not permit
relaxation. No new mandatory native dependency or hydrodynamics in this slice.

Ownership: cached Mistral unavailability/exhaustion remains valid. OpenAI workers
own the coherent solver and separately scoped ANYfem outcomes; root owns shared
contracts, benchmark harness/evidence, integration and final acceptance. Existing
prepared source is prior task work, intentionally continued rather than discarded.

### M8 handoff — 2026-10-09

Implemented experimental response factories, owned homogeneous reduced-response
libraries, sparse coefficient packets, actual full-load certification/reactions,
supported/free-free execution and the general declared periodic ANYfem adapter.
Full 60-pressure-phase plus moment barge library exercised. Exact original-time
loads remain available for fallback. No default API or pinned formulation change.

Scientific disposition: response stress superposition failed preserved existing
principal/cancellation checks in m8-solver-05. Removed unqualified component
columns; all stress/envelope cases now use canonical direct solves and staged
recovery. Cheap certificates/output exclusion bounds remain deferred. Safe subset
implemented, requested whole-model stress-reconstruction acceleration NOT accepted.
See ../PREPARED_STATIC_M8_SCREEN.md and ../../.prepared-static-evidence/m8-solver-handoff.md.

Numerically corrected barge: warm 1.61–1.75x, cold 15.3% slower and higher peak RSS;
829,188 history values and all three envelope hashes bit-identical. Small free-free
64-case holdout cold 3.42x is batching evidence only. Representative promotion
NO_GO; no 10,000-case run, qualification or defensible representative projection.
Benchmark ledger: 540.0326433999871 / 600 process-wall seconds, 59.96735660001286
unused. Stop campaign. Full evidence:
C:/ANYworkspaceWork/prepared-static-20261008/evidence/M8_RESULTS.json.

Final authority review closed subclass and native-base class/instance/global hook
replacement before trusted spans. Focused m8-solver-10: 11 passed. Earlier root
affected-path integration: 38 passed. Final broad authority regression timed out
after 26.0346231 seconds with no completed summary: verification remains incomplete.
Root check usage118.7279141/120; solver104.6395796/120; FEM36.4547319/120.
No tolerances relaxed; failed evidence and timeout output retained. Final authority
source differs from timed numerical source; hashes and distinction are in report.

Root reviewed ownership, numerical failures and authority changes; owners supplied
cross-repository review. Cached Mistral exhaustion persists; no different-family
assessment claimed. All edits retained uncommitted in isolated worktrees under
C:/ANYworkspaceWork/prepared-static-20261008; no main edits, commit, merge or push.
M8 source delta is three solver and three FEM files, plus tests/docs/evidence;
prior M1–M7 work remains intact. Remaining work includes broad final-source checks,
qualified stress/output bounds, mixed-packet memory edge behavior and representative
free-free/selected-only/long changed-envelope coverage. Current status: implemented
safe experimental subset, partially verified, scientific/performance NO_GO for the
requested whole-model response-reconstruction promotion.

### M9 numerical reconstruction follow-through — 2026-10-09

User approved the recommended next step: finish the outstanding broad regression,
isolate stress-reconstruction counterexamples and test a staged numerical route
under unchanged criteria. New bounded correctness/diagnostic reserves are 120
process-wall seconds each for root and the existing solver owner. No benchmark
renewal or representative timing campaign. M8 ledger remains closed and preserved.
Cached Mistral unavailability remains valid; retain the existing OpenAI solver owner.

Question: is the failure caused by response displacement rounding, flattening of
canonical recovery stages, or nonlinear derived quantities? Use the small existing
shell/principal and mixed free-free beam/shell counterexamples to distinguish those
causes. Compare canonical recovery at the identical reconstructed displacement,
staged kinematic reconstruction and direct-solve recovery. Outcomes determine a
compatible tested candidate or a precise documented obstruction. No changed
tolerances, zero clipping or heuristic governing exclusion; envelopes stay canonical
without an independently accepted conservative error bound. Root owns admission,
scientific adjudication and cross-author review; solver owner owns the connected
numerical candidate. Source frozen until root final M8 regression completes.

M9 root final M8 regression completed before releasing source freeze:
51 passed, exit0, 26.6744898 process-wall seconds. Final M8 authority-hardened
source broad-check gap resolved; source hashes captured in the unique run record
evidence/checks/m9-root-final-m8-regression/run.json. Remaining M9 root reserve
93.3255102 seconds. This is correctness evidence, no additional benchmark.

M9 completed: no product activation. Ten small stage controls separated coefficient
rounding, local/station superposition and derived fields. All original physical
displacement comparisons pass; native stage controls and single/multi-RHS library
preparation match exactly. Rotated local-DOF sums fail eight same-u principal entries;
native staged recovery at reconstructed global u still exceeds the corresponding
direct-output screen for three mixed-model von Mises entries. Principal direct-u
comparisons remain diagnostic applications of the existing field tolerance. Full
analysis/limitations: docs/PREPARED_STATIC_M9_INVESTIGATION.md relative to solver root,
and .prepared-static-evidence/m9-solver-handoff.md. No tolerance changes or claimed
impossibility of exact-arithmetic superposition; no conservative governor bound.

Root independently inspected diagnostic arithmetic and reproduced the frozen ten-case
result byte-for-byte: m9-root-independent-stages, exit0, 6.3321755 process-wall seconds.
Root M9 total33.0066653/120; worker17.6793787/120. Source code hashes stayed unchanged.
The diagnostic success exit verifies its native controls, not the rejected candidate.
Prior provisional load-order and coordinate-versus-physical-displacement interpretations
remain preserved with corrections. Windows longdouble has no extra mantissa precision.
No benchmarks: M8 ledger540.0326434/600 remains unchanged. Broad final-source check
gap resolved; stress-reconstruction/governor shortcut remains unaccepted. No main
changes, commit, merge or push. Stop this diagnostic batch: further work needs a
specific numerical candidate or reviewed output-error/contender bound rather than
additional timing or an automatic parameter sweep.

Final review correction: diagnostic "bit_differences" used numerical inequality
and missed signed-zero payloads. Owner corrected it with finite float64/shape
admission and uint64 payload comparison, retaining all earlier records. Run04 and
root m9-root-final-payload-diagnostic verify zero preparation/control payload
differences, including signed zeros. Root reproduced final JSON byte-for-byte,
SHA256 B655AE09A889E7E59D887F8516783DD5AF63E2C3EDAACBD27274C158FF320827.
Diagnostic final SHA84FF59AC8FCD5ADEBF80C2A8C5C360A00DA821F033E760DF138DA277A14FCE39.
Root final M9 usage39.2941374/120; owner23.9242539/120. No new numerical candidate,
benchmark, product edit or acceptance claim; broad regression and bounded numerical
investigation completed with a precise negative outcome.

### M10 conservative output bounds — 2026-10-09

User approved the recommended next step: small-fixture conservative error bounds
for safe reconstruction/contender exclusion, direct replay on uncertainty. Reserve
120 process-wall diagnostic/check seconds each for root and existing solver owner;
no benchmark renewal, no pooling M8/M9 leftovers, no 10,000-case run. Product
activation requires independent review of the actual complete bound. Existing
criteria, direct governor identities and scientific failures remain intact.

Principal uncertainty: a bound for the exact represented linear system alone does
not bound the output of canonical floating-point direct execution. Establish and
report the difference. Candidate scope: verified factor residual and triangular
inverse-action norm comparison, outward local staged arithmetic, and strict interval
contender exclusion. No global inverse, new native dependency or heuristic ties.
Test containment on M9 counterexamples and misleading-certificate/tie examples;
measure useful versus inconclusive decisions without performance claims. Root
owns proof/admission decisions and source review; solver owner owns diagnostic
implementation only until an explicit prospective activation decision.

M10 early evidence: exact rational comparison-factor proof contracts for supported
12DOF operator but overestimates linear fields; unscaled augmented54DOF refuses.
One exact power-of-two congruence resolves augmented contraction, leaving huge
output widths. This distinguishes unit scaling from proof usefulness. Root reviews
proof and requested a signed triangular-action tightening (factor-defect actions,
no global inverse) to preserve cancellations lost by comparison matrices, bounded
to one30s attempt within existing worker reserve. Observed-direct residual bounds
are explicitly not online avoidance of that direct solve. Dot rounding assumptions,
nonlinear output kernels and source/reduction uncertainty remain open qualifications.
Root independent oracle uses closed-form2x2 systems, distinct from numerical factors.

M10 completed diagnostic foundation, no product activation. Signed exact rational
triangular actions of streamed factor defects certify both original represented
operators (12DOF supported eta4.3531e-15,54DOF augmented eta9.1543e-7), avoiding a
global inverse. The earlier positive comparison refusal/scaled control and narrow
partial-field results remain preserved. Conditional staged intervals contain114
linear outputs. Requested prepared canonical VM intervals contain14outputs; width/
existing-tolerance max0.546/0.534,7paired station quantities strictly separated.
35/56paired linear components separate; exact ties remain unresolved. Near-zero
components/free beam bounds still too wide. Full report:
docs/PREPARED_STATIC_M10_BOUNDS.md; owner derivation/hashes:
.prepared-static-evidence/m10-solver-handoff.md. These use observed direct solution
residuals: no unseen-contender exclusion, solve avoidance or performance promotion.

Root reviewed proof, source graph and conditional arithmetic; independent closed-
form/permutation/cancellation/subnormal/VM oracles6passed. Owner proof tests3passed.
Root final diagnostic reproduction matches raw JSON byte-for-byte SHA
A7841A96B145B3564E73FC08D4F06E21684AF937C784E01982EC7AE50B58D49E.
Final M10 root checks12.0940658999898/120; worker21.21329490005155/120; no benchmarks.
M8 ledger540.0326433999871/600 unchanged; legacy runner display is a separate epoch.
Source product hashes unchanged, so the prior final51-test regression remains valid.

Disposition: small represented-system proof verified, sampled supported VM
usefulness conditional; production/governing activation INCONCLUSIVE. Retain direct
fallback. Next prerequisite: prospective canonical-direct solve uncertainty without
executing that solve, qualified checker/BLAS/scalar arithmetic, followed by complete
requested output/load/provenance coverage. Principal/eigensolver/reactive outputs,
offsets and full-load construction uncertainty not supplied by this prototype.
No accepted API/physics changes, main edits, commit, merge, push or10,000caseclaim.

### M11 unseen canonical-direct uncertainty — 2026-10-09

User requested the next step after M10: eliminate per-case observed-direct dependence
and qualify arithmetic. Connected milestone tests a generic canonical acceptance-
predicate bound including CSR checker rounding and unknown solution magnitude.
Root independently inspects whether actual resident backend factors expose a
stronger forward-error contract if that predicate is too weak. No weaker tolerances
or guessed governance; keep all M10/source evidence and direct fallback.

New root/owner correctness reserves120 process-wall seconds each, no benchmark
renewal or pooling prior leftovers. Owner edits new M11 diagnostic/test/evidence
files only. Product activation remains reserved until complete-bound independent
review. No global inverse, new backend/dependency or publication.

Question: can any vector admitted by the actual1e-10 checker be enclosed tightly
enough at the requested output tolerances without its direct residual? False-pass
1x1 control, actual rounded-checker proof, supported/augmented small operators,
refusal and nonlinear-output relevance determine the answer. A negative generic
predicate result is not a proof that the concrete factor-backed solve is inaccurate.
If needed, identify the missing backend-factor/triangular-rounding guarantee.

M11 completed conditional unseen-gate diagnostic; NO_GO for generic-gate
canonical-case exclusion. Even identity admits1.5e-10 output error at7.5e-11
backward ratio. Supported radius1.8196079876e-5 is too broad; free augmented
comparison contraction refuses. Direct oracle evaluated strictly afterward, never
an input. This does not establish concrete solver inaccuracy or response-library
failure. Root independent closed-form/permutation/adversary/full-load/refusal
checks5passed; author3unique tests passed; final source diagnostics reproduced.
Root8.802721900000165/120, owner10.522612199999912/120; no benchmark. M8 ledger
540.0326433999871/600 unchanged. Product hashes unchanged; no main edits or Git
publication. Full proof, resource/source audit and backend inspection:
docs/PREPARED_STATIC_M11_UNSEEN_BOUND.md; .prepared-static-evidence/m11-solver-handoff.md.

Next useful route is actual resident-factor/triangular-solve error bounds, initially
SuperLU1.16.3 with scaling/permutations/runtime arithmetic binding and componentwise
outputs. Generic1e-10 gate cannot replace that evidence. Current PARDISO wrapper
has no numeric factor export; documented pardiso_export is Schur-only. Preserve
canonical fallback and backend defaults. No source/physical-output/arithmetic or
governing exclusion qualification is claimed. Mistral remains cached unavailable;
existing solver owner continued; root performed reserved proof/architecture review
and independent tests. Different-family acceptance still unmet.

### M12 resident SuperLU solve enclosure — 2026-10-09

User approved proceeding from M11 to actual backend-specific uncertainty. This
bounded development slice owns only new M12 diagnostic/tests/evidence; product,
main, backend defaults, scientific tolerances and canonical replay remain unchanged.
Question: can resident factors plus a justified solve-rounding relation give useful
componentwise intervals for unseen canonical outputs, unlike the generic gate?
Compare supported and augmented small fixtures, exact/permuted/cancellation controls
and M10 staged outputs. Refuse unsupported arithmetic/runtime evidence explicitly;
no observed direct solution/residual as bound input. Direct solve is an oracle only
after bound construction. Source/factor proof alone is not installed-binary proof.

Allocate at most120 process-wall seconds each to owner and root correctness checks,
serial numerical lane, no pooling previous reserves or benchmark renewal. M8
benchmark ledger540.0326433999871/600 stays frozen. Mistral cached unavailable;
continue existing OpenAI solver owner. Root owns source/runtime proof review,
independent tests and activation decisions. Different-family qualification remains
unmet. No benchmark, new backend/dependency, global inverse, publication or claimed
10,000-case qualification.

M12 completed resident-factor-to-output conditional prototype. It encloses native
external scaling/permutations/triangular solves and M10 staged outputs without
observed direct inputs; oracles executed afterward. Root found diagonal-scaled
subnormal division term; regression preserved. First positive-comparison evidence
retained; one signed transpose-row action tightening captures factor cancellation
without a stored inverse. Native residual relation/export equivalence still
UNQUALIFIED. Runtime observations identify two loadedOpenBLAS versions/SkylakeX,
threads1; calling-thread nearest/denormal-preserving state and sampled underflow
observed, not a kernel proof. All114linear/beam+14VM sampled values contained.
35/56supportedlinear and7/7VMpairs strictly separate; exactties unresolved. VMwidth/
tol2.33; freefield widths.000856/.005431 remain too broad. No production activation
or performance claim. Root reviewed equations and closedform independent controls.

Final author5tests and root5tests passed (10distinct), root diagnostic byte-identical
SHA87ADEACAB9E68F70F5FAA1D2256E7FAFDC85D0C5EFAA3BCFCD3441AF9BA0430C.
Owner12.262074999999868/120, root7.046796999999742/120 process-wall seconds; no
benchmark. M8ledger540.0326433999871/600 unchanged; sourceproducthashes preserved.
Report docs/PREPARED_STATIC_M12_RESIDENT_BOUND.md, proof/hashes/evidence
.prepared-static-evidence/m12-solver-handoff.md. Mistral still unavailable; independent
OpenAI checks do not satisfy different-family qualification. No Git publication.
Next discriminator output-aware uncertainty actions preserving canonical staged
arithmetic, especiallyfreefree; native solve/recovery qualification remains needed.

### M13 output-aware uncertainty actions — 2026-10-09

User requested next step after M12. Test whether factor-error correlations lost in
independent coordinate intervals can be retained through reviewed physical output
functionals. Own new M13 diagnostics/tests/evidence only; keep M12 failed-width
and arithmetic evidence unchanged. Canonical staged recovery remains the oracle
and execution contract. Composed exact linear rows may bound uncertainty but may
not replace the canonical staged computation. Unknown canonical solve/recovery
values are not inputs. Include all staged rounding and scaling uncertainty; a
factor-linear functional alone is not a full canonical output certificate.

Question: do signed output/factor actions tighten free-free stress bounds enough
to resolve historical contenders, or does the native/rounding model still dominate?
Use same supported/free fixtures, signed/cancellation/permutation and exact ties;
separate factor uncertainty from staged roundoff. Preserve source/full-load,
principal/reaction and native arithmetic qualification gaps. One bounded targeted
correlation repair, no sweeping fixtures/parameters to find a pass.

Allocate at most120 process-wall seconds each to owner/root correctness checks,
serial numerical lane, no previous reserve pooling or benchmark renewal. M8
ledger540.0326433999871/600 unchanged. Mistral cached unavailable; existing solver
owner continues central algorithm/integration; root owns proof/contract decisions,
independent checks and final disposition. No backend/dependency/default or product
activation, Git publication or10,000caseclaim.

M13 completed signed output/factor uncertainty actions with separate canonical
stage-rounding symbols. No observed direct input; all114linear/beam+14VM interval
containment before post-bound oracle. SupportedVM width/tolerance .57977/.58028
(vsM12~2.33);7/7VM and35/56linear pairs separate. Free shear widths2.70159e-5/
.000171283 (~31.7x narrower) stillresolve no contenders; native backward radius
dominates. Even removing native/RHS contributions from current allowances leaves
recovery widths~2.64e-8/1.68e-7, so native qualification alone is insufficient.
Conditional native/staged arithmetic and selected-helper-only authority gaps
retained. No activation, benchmark, backend/sourceproduct or scientific changes.

Root proof review/exact correlated-error/noise/permutation/refusal controls:9distinct
tests ultimatelyverified (author4, root5). Initial roottest4pass1failure assumed zero
contribution key persisted; fixedtest to recognize omittedzero, affectedtest1passed;
failed log retained, formula/tolerance unchanged. Final diagnostic byte-identical
SHA6016442852C5C2CEF283B0D706D4E04305E83B6E6F5F0C9C75DEBF6624352D07.
Owner8.144885799999429/120; root10.145557499999995/120 processwall seconds. M8
ledger540.0326433999871/600 frozen; no reservepooling. Full outcome/decisions:
docs/PREPARED_STATIC_M13_OUTPUT_ACTIONS.md; proof/sourcehashes:
.prepared-static-evidence/m13-solver-handoff.md. Previous evidence/producthashes
preserved; no main/Git publication. Mistral unavailable; no different-family
qualification. Next discriminator actual backward-solve/recovery primitive audit,
including exactselector/sign/dyadic operations, with unchangedcanonical arithmetic.

### M14 exact primitives and native backward-solve audit — 2026-10-09

User approved next discriminator from M13. This slice audits exact selector/sign/
power-of-two primitives and applies proved exactness only to diagnostic rounding
allowances, preserving canonical computation. Subnormal/overflow/cancellation and
signed-zero scope must be explicit. Do not empirically reduce native gamma or infer
an unobserved vendor operation schedule from exported factors. Separate native
backward and staged contributions; same historical fixtures decide usefulness.

Own new M14 diagnostic/tests/evidence only. All M1–M13, product/backend/defaults,
scientific tolerances, prior failures and canonical fallback remain frozen. No
benchmarks, publication or10,000caseclaim. Allocate at most120 process-wall seconds
each to owner/root correctness checks, serial lane, no priorreservepooling; M8
benchmarkledger540.0326433999871/600 unchanged. Mistral cached unavailable; existing
OpenAI solver owner implements coherent slice, root audits native source/contracts
and independent exactness/counterexample tests. Native arithmetic/different-family
qualification remain unmet unless actual evidence establishes them.

Question: can proved exact primitives remove the staged-error floor, and does the
native backward relation still prevent free-free contender exclusion? Native audit
must identify available/unavailable executed schedule evidence and quantitative
usefulness; absence of a tighter proof is reported, not patched around.

M14 completed exact primitive allowances and nativeaudit. Zero/unit/sign/selectors
and safe power2 rules proved with underflow/overflow exceptions; no genericdyadic
exactness. Root independent near-minnormal/minsub/max/sign/mixeddot controls5pass;
author7pass (12distinct), finalfixture JSONbyteidenticalSHA
D4D0DED89224A745B3F04AE2707C73A72B49A16F61A0334A65F3DAF77ED27028.
All114linear/beam+14VM conditionalcontainment; supportedVMwidth/tolerance .41417/
.41439,7/7VM and35/56linear pairseparation. Free selector/finalscale/transformnoise
vanish, removingM13 stagedfloor. Freewidths2.69895e-5/.000171116 remain dominated
by nativeback1.34927e-5/8.55447e-5; nofreeexclusion. Nativeg/a unchanged.

Audit matchedSciPy gstrs source/publicL/U exports; native supernodepartition/packed
TRSMschedule notexported. LoadedOpenBLAS0.3.29.dev metadata lacks exactcommit/
selectedkernel proof. IndividualpublicOpenBLAS sourcepages returnedcachemiss;
notassumedread ormatcheddevbinary. No privatepointer/nativewrapper workaround.
Nativeaudit INCONCLUSIVE; runtime/sourceidentity alone cannotqualify usefulbound.
Retain exactrules; further recovery-only tweaks don'tresolve freeblocker.
Report docs/PREPARED_STATIC_M14_PRIMITIVES.md; proof/sourcehashes
.prepared-static-evidence/m14-solver-handoff.md. Owner6.722925499999746/120,
root7.006808099999944/120 processwall. No failure/timeout/skip, no benchmark or
pooling; M8ledger540.0326433999871/600 frozen. Product/M1–M13 preserved; no
activation/main/Git/10k claim. Different-family qualification unmet; Mistralcached
unavailable. Next required evidence useful actualnative solveerror relation.

### M15 native solve relation investigation — 2026-10-09

User approved proceeding after M14. Target a justified native backward-solve error
relation, rather than another recovery-bound tweak. Root investigates installed
SciPy/OpenBLAS build/source identity and available native schedule authority.
Owner may construct a bounded operation-level or partition-independent diagnostic
candidate using actualresident factors, while distinguishing reference arithmetic
from the executednative path. Exactprimitive/Sterbenz/correlated-rounding proofs
may be used; no observed direct/intermediate solution may seed onlinebounds.
Canonical direct solve remains an after-bound oracle only. A scalar reference
triangular solve is not automatically equivalent to gstrs/vendor TRSM/GEMM.

New M15 diagnostics/tests/evidence only; preserve M1–M14, product/defaults,
scientificcriteria and failed evidence. No nativebuild/privatepointer workaround,
newbackend/dependency/benchmark/publication. Allocate at most120 process-wall sec
each owner/root correctness checks, serial lane, no pooling previousreserves. M8
ledger540.0326433999871/600 unchanged. Cached Mistralunavailability persists;
existing owner connected investigation/implementation, root proofs/nativeidentity
and acceptance. Early decisivecheckpoint: prospective route with actual prerequisite
or concrete missingevidence, not a genericgamma reduction. If no justified useful
relation can be established in this slice, stop the bound-refinement line with a
specific limitation and preserve candidate; do not invent native qualification.

M15 complete: NO_GO for sufficiency of existing native residual relation;
actual native tighter relation INCONCLUSIVE. Exact represented triangular
counterexample admits 4.656612873077393e-10 output error against1e-12 target;
root independent two-case control proves governor reversal can be admitted.
Not an observed native solver defect; scalar reference is explicitly distinct.
Public versioned gstrs uses scalar or vendorTRSM/GEMM by resident supernodes;
CSC exports lack partition/order authority. Exact installed DLL-to-source/kernel
mapping was not established; failed retrieval is not proof unavailable. No
justified useful stronger native contract found. Stop bound-refinement under
current assumptions; preserve candidate/canonical fallback. Seven distinct tests
pass (owner3/root4), zero failures/skips/timeouts, combined3.6494646000010106
correctness process-wall sec. Owner2.2034979000009116/120; root1.445966700000099/120.
M8 benchmark540.0326433999871/600 unchanged. Product hashes unchanged; no main,
sibling, backend/build/Git/benchmark edits or activation. Different-family review
unmet, cached Mistral unavailability. Report docs/PREPARED_STATIC_M15_NATIVE_LIMIT.md;
raw ../evidence/checks/m15-solver-01,-02,m15-root-01; owner handoff
.prepared-static-evidence/m15-solver-handoff.md. Next work needs a concrete native
arithmetic proof or separately adopted architecture decision, not another sweep.

2026-10-09 user requested handover for another model. Restart checkpoint saved at
PREPARED_STATIC_MODEL_HANDOVER.md in this directory, with exact artifact identities,
M15 decisive limitation, protected dirty/evidence ownership, unmet native/family
review gates, process state and consumed budget. No new checks or benchmarks for
handover; no publication or renewed execution authority.

### M16 certified response route — adopted 2026-10-09

Prospective transition. Owner takeover by Claude (Anthropic) after the M15
handover. The user reviewed the takeover memo and chose "Option A,
certified-route contract for the opt-in response route". This is an explicit
scientific-contract delta for the opt-in response evaluator only. Default APIs,
the direct stream, the prepared direct evaluator and M8 response behaviour stay
unchanged. All M1-M15 source, evidence and failed results are preserved.

Reason for the delta. M9 showed the stress-library mismatch is floating-point
non-commutativity of superposition versus solving the summed load: preparation
columns and same-displacement recovery are bit-identical, only the rounding
path differs. M10-M15 tried to bound the canonical direct solve a priori to skip
replay; M15 proved the available SuperLU relation insufficient, and PARDISO
(the barge backend) exports no factors, so that line could never cover the
representative workload. Under the old contract the response route cannot
remove recovery, which is the dominant recurring cost (barge warm, four cases:
recovery 5.4-5.9 s of 13.7 s; solve 0.06 s).

Adopted contract (opt-in keyword `stress_execution="certified_library"`;
default `"canonical"` keeps M8 behaviour exactly):

1. Source agreement. The case load is F_c = F0 + sum c_j F_j from owned columns.
   When an original-time canonical packet is supplied, its native assembled F is
   authoritative. Reconstruction is admitted only if
   max|F_actual - F_c| <= 1e-12 * max(|F0| + sum |c_j| |F_j|), else canonical
   direct fallback (counted). Bitwise identity is no longer required.
2. State certificate. The reconstructed reduced state is certified with the
   existing 1e-10 backward error against the actual RHS; failure falls back.
3. Stress. Each admitted element gets verified affine output columns
   Y_0 = rec(u_0), Y_j = rec(u_j) - rec(0) from owned canonical recipes, with
   random additivity/homogeneity verification at preparation. A case emits
   Y_0 + sum c_j Y_j. Nonlinear measures (von Mises, equivalent, principal) are
   recomputed from the reconstructed components by the reviewed
   `_derived_measure`; constants are copied. Elements whose fields fail
   verification refuse the requested capability explicitly.
4. Reactions and displacements. Actual Ku-F diagnostics at the certified state;
   unchanged code.
5. Envelopes. The unchanged shared reducer folds the route's values. Exact ties
   keep the earliest input. Governor identity basis is labelled
   `certified_response_values`.
6. Qualification is by assessment against canonical staged recovery at the same
   certified state, not by a per-case runtime proof. This is the main shift from
   M10-M15.

Refinement versus the takeover memo: the memo mentioned replaying overlapping
contenders canonically. Under this contract canonical direct values are not
the reference, so replay would only reintroduce bitwise compatibility. It is
dropped. Labelling governors that are ambiguous within route accuracy is an
open item, not implemented here.

Frozen acceptance criteria (fixed before any M16 measurement). u = 2^-53.
For element e and case c, U_e = |u_0,e| + sum |c_j| |u_j,e| (full columns incl.
prescribed offset in u_0), H_e = probed local affine map of each linear field,
r_e = rec(0), s_e = max over e's linear stress entries of (|H_e| U_e + |r_e|).

- C1 displacement: route u_c versus a canonical direct solve of the actual
  load, existing tolerances (supported rtol 1e-12 atol 1e-14; free-free rtol
  1e-11 atol 1e-13).
- C2 linear stress entries: |y_route - y_can(u_c)| <= 1e-12 |y_can| + 2^10 u s_e.
- C3 derived measures (von Mises, equivalent, principal top/bottom):
  |d_route - d_can(u_c)| <= 1e-12 |d_can| + 2^14 u s_e. Factor 16 over C2 covers
  the Lipschitz constants of the measures in the components (Weyl bound for
  principal, norm property for von Mises, surface membrane +/- bending
  doubling) plus their own arithmetic.
- C4 reactions: route versus canonical constraint-force diagnostics at u_c,
  bitwise identical (same code, same inputs).
- C5 envelopes: every route envelope value (min and max of every stress entry)
  meets C2/C3 against the canonical-at-u_c envelope. A governing-identity
  difference passes only as a near tie: the canonical value of the route's
  governing case meets the same tolerance against the canonical governing value.
- C6 behaviour: default route unchanged; source discrepancy above the
  agreement threshold falls back and is counted; failed certificate falls back;
  refusal of unverifiable elements; offsets applied once; free-free imbalance
  policy unchanged.

Rationale for 2^10: the error of either route against the exact affine map is
of order k u (|H| U + |r|) with k the staged operation depth plus the m-term
combination, roughly 2 x 35 + m + 24 for the admitted shells. 2^10 leaves about
5x margin and the element maximum absorbs staged intermediate magnitudes.
Relative to element stress level this is 1.1e-13 (C2) and 1.8e-12 (C3). It is a
criterion choice for this contract, not a proof.

Development fixtures (disclosed, not blind): the M8 accuracy tests and M9
diagnostic cases (S3 coefficients 1/.1/.3/3.7/-1.25, S3 rotated pi/7, mixed
free-free cases 0/48/576). Formal assessment holdout, defined now: (A1)
supported S3 with pressure, nodal and gravity patterns, 12 seeded coefficient
cases (seed 16001) including an empty and a single-active case; (A2) the same
S3 rotated 0.37 rad about axis (1,2,3), 6 seeded cases; (A3) mixed free-free
Q4/beam with patterns at positions 17/233/401, 8 seeded cases, whole-model
envelopes; (A4) beam with nonzero prescribed offset, 4 cases. Outcome: GO for
the route on these fixtures only if every C1-C6 check passes; any failure is
recorded unchanged.

Resources: author correctness checks at most 120 process-wall seconds through
`../run_check.py --kind check --benchmark-epoch m8 --jit 0`; no benchmark,
no reserve pooling, M8 ledger stays 540.0326433999871/600. No Git operations.
Mistral is cached unavailable per handover and was not reprobed. Independent
review of M16 is pending; Claude is a different family from the M1-M15 authors
but not from this slice's author.

M16 result (2026-10-09). Implemented the opt-in certified library route in
`prepared_static_response.py` plus an optional record hook in
`prepared_static_shared.py`; default canonical behaviour unchanged. Frozen
product SHA256: prepared_static_response.py
2c8e264a169728f079c23dbba6162edb1c58ef7cc67619dfb48f14e2f3ce1e2f,
prepared_static_shared.py
5172ec74b9b6496d4f80840b1923e4c1e6773143e128022abfd227f1ca9b503e. Pre-M16
comparator source: ../m16-baseline/solver/src.

Formal holdout assessment A1-A4: GO, zero C1-C6 failures across 30 cases,
14,952 linear and 3,208 derived entries, 2,022 envelope entries. Worst error /
limit 0.0058 linear, 0.000094 derived. A3 has 18 governing-identity differences
versus canonical-at-same-state, all near ties under C5. Development fixtures
pass. ANYfem periodic recurrences reconstruct (source ratio 1.5e-17).

Negative control finding: the derived criterion resolves about 1e-10 relative
to the measure, not the 1.8e-12 the rationale stated, because the element scale
is an internal-magnitude scale. First control failed and is preserved; criteria
unchanged.

Pre-existing failures, reproduced on the pre-M16 source: three tests that patch
module globals now hit the M8-final response guard first (envelope one-case
policy, driver constructor alias, packet memory before copy). Not fixed here.

Checks 97.696126/120 process-wall seconds (m16-claude-01..09); no benchmark,
M8 ledger 540.0326433999871/600; no Git. Report:
docs/PREPARED_STATIC_M16_CERTIFIED_ROUTE.md. Next: owner grant of a benchmark
epoch for a representative barge screen of the library route, independent
review, and a decision on the pre-existing authority tests.

### M16 barge benchmark epoch — granted 2026-10-09

User granted a new benchmark epoch `m16` of 600 cumulative process-wall
seconds for the barge screen. Includes preparation, warm-ups and failures; no
pooling with M8 (540.0326433999871/600 stays closed). Runner gains epoch `m16`
(pre-change copy: evidence/run_check_pre_m16.py). Harness
evidence/m16_barge_screen.py is m8_barge_screen.py plus `--stress-execution`.

Question: on the representative barge (fixture SHA256 0f64d971...), what does
the certified library route cost to prepare, what is its recurring per-case
time, and how do its outputs compare with the canonical response route?
Order: library route first (cold, warm repeat, holdout; 4 cases each; block 4;
same fixture/cases as M8), then the canonical comparator on the same M16
source only if at least about 175 s remain, else the recorded M8 response and
direct runs serve as labelled historical comparators. Resource policy estimate
2048 MiB for both (the full-field library is estimated at about 220 MB and would
likely be refused at the M8 1024 MiB setting); the machine has 127 GB.
Promotion criteria unchanged: 2x complete-workload speed or 50% lower peak RSS
with <=5% slowdown, per the adopted plan. Output comparison is offline from
saved histories/envelopes, with no numerical rerun.

M16 barge screen outcome (2026-10-09): INCOMPLETE, no timing result.
- m16-barge-library: harness SyntaxError (my header broke a __future__
  import), 0.07371989999955986 s charged, preserved.
- m16-barge-library-02: certified library route timed out at the 430 s cap,
  430.1047636000003 s charged. Base preparation and factorization finished at
  93 s; the element library did not finish. Process tree confirmed dead, one
  core used, system CPU mean 9.6%, peak sampled RSS 1.28 GB.
- Cause (inference from recorded measurements, not profiled): both library
  loops called the full authority safe point per element, 8,490 times; M2/M7
  measured that check at about 33 ms, roughly 280 s in total. Recoveries are
  roughly 110 s (75 per element at 0.35 ms, from M8 barge recovery phases).
- Epoch m16 used 430.17848349999986/600; 169.82151650000014 s left unspent
  because no library run fits (estimated about 280 s after repair). No
  comparator run; the recorded M8 runs remain the comparators.
- Repair: safe points now once per 128 elements (`_LIBRARY_SAFE_POINT_STRIDE`),
  first element always checked; numerics unchanged. New product SHA256
  8a7a9c88ce12d7d10587cf2fdcdc758d899db1adf2d545700ca423ce40b17c20; assessed
  version preserved as evidence/m16-prepared_static_response-assessed.py.
  m16-claude-10-stride: 16 M16 tests passed, 8.117087000000538 s. Correctness
  checks now 105.813213/120 s. The formal holdout JSON belongs to the assessed
  hash; the diff is only the safe-point frequency.
- Recorded M8 per-history split (warm, canonical response route): next()
  8.61 s of 13.67 s, recovery 5.91 s, outside solver phases 1.01 s,
  serialization 1.55 s. Recovery is the removable part; no measured
  library per-case time exists yet.
Next: a new benchmark allowance (about 600 s: library run about 280 s,
canonical comparator about 165 s, margin) to rerun the screen on the repaired
source.

### M16b barge benchmark epoch — owner-delegated allowance, 2026-10-09

User: "Make your own decisions on benchmark allowance. I approve that."
Decision: new epoch `m16b`, 800 cumulative process-wall seconds; m16 stays
closed at 430.17848349999986/600 (its 169.8 s are not pooled). Allocation:
library route run cap 450 s (estimate about 280 s), matched canonical response
run cap 220 s (M8 equivalent 160.5 s), about 130 s for one diagnosis if a run
fails. Same fixture, cases, block size 4, 2048 MiB policy estimate, harness
evidence/m16_barge_screen.py, repaired source SHA256 8a7a9c88...b17c20.
Promotion criteria unchanged. No automatic extension beyond 800 s.

M16b barge screen result (2026-10-09). Epoch m16b used
601.1913330000007/800 process-wall seconds (library 438.6889210999998,
canonical 162.50241190000088); 198.8 s left unspent, campaign stopped.
Repaired source 8a7a9c88...b17c20, same fixture/cases/settings for both.

| Measure | Library | Canonical |
|---|---:|---:|
| Preparation end | 396.3 s | 118.6 s |
| Cold / warm / holdout history | 13.78 / 13.62 / 14.20 s | 14.24 / 14.08 / 14.74 s |
| Warm recovery phase | 5.01 s | 5.78 s |
| Peak RSS (warm) | 1,536 MB | 1,316 MB |

Disposition: **performance NO_GO** for the M16 library route as implemented
(1.03-1.04x per history, +278 s preparation, +220 MB). The element library
holds 212 MB for 4,245 elements. All 12 cases reconstructed with zero
fallbacks (max source ratio 3.6e-16). Offline output comparison
(evidence/m16b-barge-output-comparison.json, m16_barge_compare.py) against the
canonical route: displacement 5.1e-13 relative to max, selected stresses
1.8e-11 relative to element max, envelope values 2.1e-8 relative to entity max,
zero governing-identity differences in 276,246 envelope values per history.
The 2.1e-8 figure is untraced and the frozen criteria were not evaluated at
barge scale.

Why no gain: per-case cost stays in per-element Python work (record dicts,
derived von Mises loops, envelope folding, reaction diagnostics), which the
library replaces with equivalent per-element Python work. The canonical Q4
staged recovery was already cheap numpy per element. A gain would need a
whole-model vectorized path: one library product per case, vectorized derived
measures and envelope folding without per-element records. That is a new
milestone, not started.

## M17 whole-model vectorized certified route — started 2026-10-09

User: "start that vectorized milestone". Owner Claude; benchmark allowance
decisions delegated by the user. Epoch `m17`: 900 cumulative process-wall
seconds (profile about 160, vectorized barge run about 250, matched canonical
about 165, contingency); m16/m16b closed and not pooled. Correctness reserve
150 s. No Git operations.

Question: on the barge, where does recurring per-case time go once element
recovery arithmetic is cheap (record construction, derived measures, envelope
folding, reaction diagnostics, load evaluation), and can a whole-model
vectorized path remove enough to reach the 2x complete-workload criterion?
First discriminating step: one profiled canonical-route barge history
(4 cases, cProfile on next() only) to attribute the recovery phase. Design is
chosen after that profile. Contract: Option A and the frozen M16 criteria
C1-C6 apply unchanged; any representation change is reassessed on the M16
holdouts before any timing claim.

M17 progress (2026-10-09).
- Profile (m17-barge-profile, 149.67 s, canonical route, 4 cases, profiled
  19.1 s): envelope transaction machinery about 30%, load evaluation with
  per-element routing checks 22%, element recovery 16%, reactions 12%, record
  deep copies 9%. Element arithmetic alone cannot give 2x.
- Implemented opt-in `stress_execution="certified_vectorized"`: new module
  prepared_static_vectorized.py (probed affine maps grouped by schema,
  per-column batched products, vectorized von Mises/principal, array envelope
  accumulator with the same tie rule and associated fields); base factory
  `_new_envelope`; load routing checks once per case (bitwise unchanged,
  pressure-verification suite passes). Pre-M17 comparator ../m17-baseline.
- Defect found by test and fixed: a batched product over several case columns
  rounded differently from one column, breaking exact ties across blocks; now
  one identically shaped product per column.
- Formal holdout A1-A4 (m17-claude-03-assessment): GO, zero C1-C6 failures,
  worst linear 0.0050, derived 0.000091 of limit; A3 16 identity differences,
  all near ties.
- Barge run 1 (m17-barge-vectorized, 119.10 s) refused one beam axial field
  in verification. Diagnostic (m17-barge-probe-diagnostic, 178.86 s): all 4,245
  elements affine to 4.3e-16 against |H||v|+|r0|; the refusal was rigid-offset
  cancellation judged against the observed value only. Verification now uses
  the internal-magnitude scale (still 1e-9); admission-only change, outputs
  unchanged. Assessed vectorized source kept as
  evidence/m17-prepared_static_vectorized-assessed.py.
- Budget: m17 used 447.63/900. Delegated-authority extension: epoch m17b,
  300 s, only for the matched canonical comparator, because the diagnosis used
  the contingency. Correctness checks 45.64/150.
- Matched barge screen (m17-barge-vectorized-02 151.996 s, m17-barge-canonical
  148.709 s): preparation 127.1 vs 105.9 s; warm next() 2.16 vs 7.92 s
  (3.67x); recovery 0.91 vs 5.82 s; warm history incl. serialization 7.91 vs
  14.03 s (1.77x); peak RSS 1,255 vs 1,339 MB; outputs as in M16 (0 identity
  differences). m17 used 748.34/900. m17b was not needed for the comparator;
  decision: repurpose m17b (300 s) for one 40-case cold vectorized history
  (10 blocks of 4) to measure per-case scaling over many blocks. No canonical
  40-case run: its per-case cost is consistent across M8/M16b/M17.
- 40-case vectorized history (m17b-barge-vectorized-40, 164.602 s): ten
  blocks evaluated, case evaluation flat at 2.20 s per four cases; stopped at
  the harness 256 MiB output cap while writing block ten (preserved).
- Regression m17-claude-05-regression: 80/83, the three pre-existing
  authority-test failures only. Checks 80.551/150 s. m17 748.336/900,
  m17b 164.602/300; both stopped.
M17 disposition: holdout GO; barge case evaluation 3.4-3.7x, about 2.5x per
case including harness output, +21 s preparation, no extra memory. Long-history
complete-workload 2x is projected (about 2.4x at 10,000 cases), not measured.
Report: docs/PREPARED_STATIC_M17_VECTORIZED_ROUTE.md. Next decisions for the
owner: a measured long-history screen (needs a lean output sink), independent
review, the pre-existing authority tests, and whether to integrate.

## M18 long-history barge screen — started 2026-10-09

User: "start the long-history screen". Owner-delegated allowance: epoch `m18`,
2,400 cumulative process-wall seconds (estimate about 2,050: vectorized about
310 s and canonical about 710 s per 300-case history, two pairs). m17/m17b
closed, not pooled. Correctness checks: none planned (product source frozen at
the M17 final hashes); evidence tooling only.

Question: does the M17 vectorized route meet the adopted promotion criterion,
2x complete-workload speed (built model to consumed output, including
preparation and factorization) on the representative barge, confirmed on a
distinct holdout?
Design: harness evidence/m18_barge_screen.py = m16_barge_screen.py plus
`--selected-output lean` (per case: displacements at the 18 output DOFs,
selected stresses and reactions, backward error and route labels; same for
both routes; the full constraint-force maps of about 6 MB per case are
dropped). Primary: 300 cases at even saved positions (case-start 0, step 2).
Holdout: 300 distinct cases at odd positions (case-start 1, step 2). Each run is
one cold process, block 4, 2048 MiB policy, whole-model von Mises and all-node
reaction envelopes plus selected histories. Order: primary canonical then
vectorized; holdout vectorized then canonical. Caps: vectorized 450 s,
canonical 900 s. Outcome rule: GO only if both primary and holdout complete
workload ratios are >= 2.0; otherwise report the measured ratios. Outputs are
compared offline (displacements, selected stresses, envelopes, identities).

M18 result (2026-10-09). Product source unchanged (M17 final hashes). Runs:
m18-primary-canonical 625.546 s, m18-primary-vectorized 284.507 s,
m18-holdout-vectorized 301.875 s, m18-holdout-canonical 615.325 s (launched
detached by an operator slip, then monitored; completed exit 0). Epoch m18
used 1,827.25/2,400 s; stopped.

| 300-case history | Primary vect. | Primary canon. | Holdout vect. | Holdout canon. |
|---|---:|---:|---:|---:|
| Built model to consumed output | 281.8 s | 622.9 s | 299.2 s | 612.5 s |
| Preparation | 111.4 s | 99.4 s | 124.6 s | 96.5 s |
| History | 170.4 s | 523.4 s | 174.6 s | 516.0 s |
| Recovery phase | 57.2 s | 403.4 s | 59.0 s | 397.3 s |
| Load evaluation phase | 87.1 s | 89.2 s | 88.1 s | 87.8 s |
| Peak RSS | 1,192 MB | 1,183 MB | 1,191 MB | 1,182 MB |

Complete-workload ratio: primary 2.21x, holdout 2.05x. Both meet the adopted
2x criterion, so the outcome rule recorded before the runs gives **GO for the
speed criterion**; the holdout margin is thin and preparation varied by 13 s
between vectorized runs. Memory is not lower (the 50% alternative is not met).
Per-block time flat over 75 blocks. All 600 cases reconstructed, zero
fallbacks, max source ratio 5.2e-15.
Outputs versus canonical: displacements 6.0e-13 relative to max, selected
stresses 1.5e-11 relative to element max, envelope values 7.3e-10 relative to
entity max. Governing-identity differences: 43,520 (primary) and 45,995
(holdout) of 276,246 envelope values; every one is between samples at the same
phase of the 6 s period, where the route's values are exactly equal (built from
the same phase columns, earliest input wins) and the canonical route's
original-time evaluations differ by rounding. Value gap median 3e-14, maximum
6.7e-10 of entity maximum. Evidence: evidence/m18-analysis.json,
m18-primary-identity.json, m18-holdout-identity.json.
Load evaluation (original-time canonical loads for source agreement) is now
half of the vectorized per-case time and the next lever.
Remaining before any merge: independent review of M16/M17, barge-scale
evaluation of the frozen criteria, the three pre-existing authority-test
failures, and an owner decision on integration.

## M19 speed-up sweep of the vectorized route — investigation only, 2026-10-09

User: "have a sweep and see if there are missed speed ups in the vectorized
implementation". Investigation; no product edits. Owner-delegated profiling
epoch `m19`: 600 s (per-case cProfile of 40 vectorized barge cases, then a
cProfile of vectorized preparation). Findings will be ranked with measured or
estimated gains and contract implications for an owner decision.
M19 result: two profiles (m19-profile-cases 187.244 s, m19-profile-preparation
282.863 s), epoch m19 470.107/600, no product edits. Ranked findings in
docs/PREPARED_STATIC_M19_SPEEDUP_SWEEP.md. Top per-case items: reaction
diagnostics deep-copy constant metadata every case (31% of profiled case time);
np.cross in the canonical pressure kernel (bitwise-replaceable); ANYfem
centroid cache cleared every case (100% misses); per-case native authority
check in the response load path. Contract-level lever: original-time canonical
load evaluation, about half of per-case time. Awaiting owner decision on which
items to implement.

## M20 per-case fixes and compiled pressure loads — adopted 2026-10-09

User: "Implement items 1, 3, 4 and Option 1. Investigate if there are
defensible possibilities in Preparation." Preparation is investigation only.
Pre-M20 comparator: ../m20-baseline (solver and fem src).

Scope (vectorized route only unless stated):
- Item 1: reaction force maps for the envelope computed with the same residual
  and accumulation, without metadata copies or per-MPC records. Selected
  reactions keep full diagnostics with independent per-case metadata copies;
  the copies come from a once-made pickle of the plain snapshot metadata
  instead of `deepcopy` (same structure and types, no shared objects).
- Item 3 (ANYfem adapter, all routes): wet-element centroids and normals are
  computed once at preparation for the owned mesh and returned as copies;
  the per-case clearing no longer discards them.
- Item 4 (response evaluator): the per-case native authority check in
  `_load_vector` is skipped only inside a live owned scope, whose entry and
  exit already perform it for the block.
- Option 1: for PatternCase samples with an original-time canonical packet,
  dead pressure on elements with verified compiled bases is applied as one
  sparse product; other families use the native code. Native evaluation stays
  for direct cases, follower pressure, missing bases or any irregularity. The
  per-case source agreement check (1e-12) against natively assembled pattern
  columns is unchanged. At preparation every pattern column is recomputed
  through the compiled path and must meet C7, else compiled loads are disabled.

Frozen criteria added before any M20 measurement (u = 2^-53):
- C7 load agreement: per DOF |F_compiled - F_native| <= 1e-12 |F_native|
  + 2^10 u (|S| |p| + |F_other|), where |S||p| sums absolute compiled pressure
  contributions and F_other is the native non-pressure part.
- C4' reactions when the load was compiled: per node component
  |r_route - r_can| <= 1e-12 |r_can| + 2^10 u g, with r_can the canonical
  constraint-force diagnostics at u_c with the native load, and g accumulated
  like the reactions from g_dof = (|K| |u_c|)_dof + (|S||p| + |F_other|)_dof,
  using |coefficient| for master-equivalent forces. C4 bitwise still applies to
  natively loaded cases.
- C1 uses the canonical direct solve of the native load. C2, C3, C5 unchanged
  (u_c does not depend on the evaluated load).
- Item 1 and 4 and 3 must be output-identical: full diagnostics equal to the
  pre-M20 function, force maps bitwise equal, centroid/normal values equal.
Assessment holdouts for loads: A1-L, A2-L and A3-L = A1, A2, A3 with each case
also carrying a natively combined original-time LoadCase (sum of scaled
pattern loads; disclosed: these coefficients were used before, not for loads).
Outcome rule: GO for Option 1 only if C1-C7 and C4' pass on all three.

Resources: correctness checks at most 150 s; benchmark epoch m20 1,200 s for a
matched 300-case barge pair after verification. No Git operations.

M20 result (2026-10-09). Items 1, 3, 4 and Option 1 implemented (final hashes in
evidence/M20_FINAL_SOURCE_SHA256.txt). Formal assessment GO on final source
(m20-assessment-02.json): A1-L/A2-L/A3-L worst C7 0.00048, C4' 0.000064, all
other criteria pass; A1-A4 vectorized pass. First assessment run's extra
condition mis-specified (empty case has no pressure), preserved. Checks
143.48/150 s. Barge 300-case matched pair: complete workload 185.1 vs 580.5 s,
3.14x (M18 2.21x); case evaluation 67.9 vs 481.7 s; outputs as M18. Epoch m20
771.12/1,200; stopped. Preparation investigated only: redundant native warm-up
for staged Q4 (about 13-16 s), batched unit probes (8-10 s), load_families for
sources without acceleration (about 7 s, existing API), digest (about 4 s).
Report: docs/PREPARED_STATIC_M20_PER_CASE_AND_COMPILED_LOADS.md.

## M21 preparation items 1 and 2 — 2026-10-09

User: "Implement preparation items 1 and 2". Pre-M21 comparator ../m21-baseline.
1. Recipe capture: attempt the Q4 stage compile first; run the native
   zero-displacement warm-up only when no staged kernel results (the stage
   compile already evaluates it). Acceptance: snapshot content digests, retained
   bytes and recipe identities on fixtures equal those of the pre-M21 source
   (cross-version comparison), all routes.
2. Vectorized build: for staged Q4 recipes the 24 unit probes are evaluated in
   one column-batched pass of the same stage operations; other recipes keep
   per-vector probes; the two per-vector canonical verification probes per
   element stay. H rounding may change, so the frozen M16/M20 criteria are
   re-assessed on A1-A4 and A1-L to A3-L before timing.
Resources: correctness checks at most 120 s; benchmark epoch m21 500 s (one
300-case vectorized history; one short canonical run to measure canonical
preparation). No Git operations.
M21 result: items 1 and 2 implemented; item 1 byte-identical across versions on
fixtures; assessment GO; vectorized barge preparation 113.5 -> 89.3 s, canonical
95.0 -> 79.9 s; 300-case vectorized workload 162.3 s. Checks 59.97/120, epoch
m21 259.07/500; stopped. Details appended to
docs/PREPARED_STATIC_M20_PER_CASE_AND_COMPILED_LOADS.md.

## M22 independent review of M16-M21, in-flight speed-ups, final benchmark — 2026-10-09

User: "Run an independent review of M16 to M21. Any additional speed ups
identified, verify and implement in flight before benchmarking. Let Fable 5.1
do the independent review, using Extra effort."
Reviewer: a separate Claude Fable 5.1 agent at extra-high effort, read-only,
writing only evidence/m22-independent-review.md; it may run checks up to 90 s
process-wall through run_check.py (names m22-review-*), no benchmarks. It is
independent of the authoring session but the same model family as the M16-M21
author, so the handover's different-family gate stays unmet.
Source frozen during review; pre-M22 comparator ../m22-baseline.
After the review: blocker findings are repaired; speed-ups are implemented only
if verified output-identical or assessed under the frozen criteria and within
the adopted contract; anything needing a contract change is reported, not done.
Allowances: author correctness checks 150 s; benchmark epoch m22 1,800 s for the
final matched 300-case primary and holdout pairs. No Git operations.
M22 review received (evidence/m22-independent-review.md; reviewer checks
27.787/90 s). No BLOCKER. SHOULD-FIX: F1 vectorized crash with an element-free
envelope; F2 compiled-load disagreement fallback solved with the compiled load;
F3 bindings/late imports of new classes not pinned by the response guard; F4
vector maps allocated before the memory check. Clarifications F5-F12, optional
F13-F16. Speed-ups S1-S10.
Triage (decided before edits): repair F1-F4 and F8 labelling; implement only
output-identical in-contract speed-ups S1 (no pressure-recipe scope for blocks
whose loads are all compiled or pure pattern combinations; global authority
checks still run at scope entry/exit), S2a (planned reaction diagnostics,
full-record equality with constraint_force_diagnostics), S5 (one pressure
probe object per load evaluation), S8 (envelope field views); report S2b, S3,
S4, S7 as owner decisions; S6, S9, S10 not done.
M22 result: F1-F4 and F8 repaired; S1, S2a, S5, S8 implemented, output-identical
(planned diagnostics deep-equal, M22 assessment GO, barge outputs byte-identical to
M21 vectorized and M20 canonical). Author checks 98.671/150 s. Final barge screen
(epoch m22 1,437.00/1,800): complete workload 4.23x primary (139.2 vs 588.1 s),
4.37x holdout (130.1 vs 568.8 s); case evaluation about 12x; memory unchanged.
Owner decisions reported: S2b, S3, S4, S7. Report:
docs/PREPARED_STATIC_M22_REVIEW_AND_FINAL_SCREEN.md.

## M23 barge-scale criteria, MPC holdout, node-envelope criteria, S2b profile — 2026-10-09

User: "Do items 1-3, then profile S2b". Product source unchanged (M22 final).
Criteria added and frozen before any M23 measurement (u = 2^-53):
- C8a displacement envelopes: values, governing input indices and associated
  fields bitwise equal to the canonical-at-u_c envelope (both fold u_c).
- C8b reaction envelopes (support, MPC slave, MPC master-equivalent): per node
  component |v_route - v_can| <= 1e-12 |v_can| + 2^10 u g, g accumulated per
  bucket like the reactions (C4', using the larger g of the route's and the
  canonical governing case) when that case's load was compiled; bitwise when
  native. Identity differences only as near ties under the same limit.
  Associated fields at the route's governing case meet the same limit.
- C5 extended: stress-envelope associated fields at the route's governing case
  meet C2/C3 against canonical recovery at that case.
New holdouts (pre-registered):
- A5-L: supported S3 with two MPC equations on node 4 (uz = 0.8 uz2; ux =
  0.5 ux2 + 0.25 uy2), patterns pressure/nodal/gravity, native original-time
  loads, 8 cases seed 16005, stress/displacement/reaction envelopes. Exercises
  the master-equivalent part of C4' and C8b.
- B1 barge: certified_vectorized route through the ANYfem periodic adapter,
  saved positions 7, 83, 159, 235, 311, 387, 463, 539 (eight distinct phases),
  all physical Q4/beam von Mises plus all-node displacement and reaction
  envelopes. Criteria C1, C2, C3 (every element, every case), C4' (every node,
  all three buckets), C5 incl. associated fields, C7, C8a, C8b. Disclosed: these
  positions belong to earlier speed screens, which never evaluated criteria.
Outcome rule: GO only if every criterion passes on A1-A5 variants and B1.
Resources: assessment/correctness checks at most 600 s (barge B1 is one run);
profiling epoch m23 300 s for the S2b profile. No product edits unless a
criterion fails; no Git operations.
M23 result: holdouts A1-A5 GO (m23-assessment-01.json); barge B1 GO on every
frozen criterion incl. 3.4 million linear and 0.32 million derived stress
entries, 17,128 reaction entries (7,560 master-equivalent), 313,128 node-envelope
entries. S2b profile: per-constraint records of selected full diagnostics are
the largest per-case cost (39%), metadata copies 10%, per-block authority 15%.
Report docs/PREPARED_STATIC_M23_BARGE_CRITERIA_AND_S2B_PROFILE.md. Checks
121.89/600 s, epoch m23 100.15/300.

## M24 lean selected reactions (opt-in) — 2026-10-09

User: "Implement lean selected reactions as opt-in and benchmark". Contract
amendment to adopted item 7, opt-in only: with
`selected_reaction_diagnostics="lean"` (certified_vectorized route only; other
routes refuse it) selected case results carry `reactions` (combined support and
MPC slave forces per selected node) and `constraint_forces` with only the three
force maps filtered to the selected nodes plus
`diagnostics="lean_selected_reaction_maps"`; no residual vector, norms,
per-constraint records or metadata copies. Default "full" is unchanged.
Acceptance, fixed before measurement: on the MPC fixture, lean reactions and
force maps bitwise equal to full mode and all other outputs identical; frozen
C1-C8 pass with lean on A1-L, A3-L, A5-L and A4; on the barge, lean and full
vectorized histories and envelopes byte-identical (lean harness output omits
diagnostics). Benchmark epoch m24 600 s: vectorized lean primary and holdout,
plus a vectorized full primary run as a same-session drift control against M22;
M22 canonical runs (canonical path unchanged) are the comparator. Correctness
checks at most 150 s. Pre-M24 comparator ../m24-baseline. No Git operations.
M24 result: lean selected reactions implemented opt-in; bitwise equal to full on
fixtures, frozen criteria GO with lean, barge outputs byte-identical. Barge
300-case lean: 104.8 / 107.1 s vs canonical 588.1 / 568.8 s (5.61x / 5.31x;
about 5.2x / 5.0x after the measured 7% drift). Epoch m24 349.57/600, checks
60.80/150. Details appended to docs/PREPARED_STATIC_M23_BARGE_CRITERIA_AND_S2B_PROFILE.md.

## M25 S3 trusted-scope capture and load_families — 2026-10-09

User: "Implement S3 and pass load_families, then benchmark".
- S3: `_capture_owned_local_recovery` enters the pinned native trusted
  operation scope (Q4/S3 factories already used by owned_recovery_scope, factory
  authority checked per capture) around its calls on the freshly cloned private
  element: pressure warm-up, Q4 stage compile and the native warm-up. Guarded
  calls on that element take the native trusted path; the scope performs its own
  per-element runtime-authority checks at entry and exit. Numerics unchanged.
  Acceptance: cross-version digest probe (snapshot digests, retained bytes,
  recipe identities, recovery outputs) byte-identical to the pre-M25 source;
  regression suites; barge outputs byte-identical to M24.
- load_families: the barge workflow passes ("nodal", "element", "pressure")
  (no acceleration in the periodic source), skipping acceleration mass capture
  through the existing API; product defaults unchanged.
Resources: correctness checks at most 150 s; benchmark epoch m25 1,500 s for
matched 300-case primary and holdout pairs (vectorized lean and canonical, both
with the same load_families). Pre-M25 comparator ../m25-baseline. No Git.

### M25 result — 2026-10-09

S3 implemented (`_capture_trusted_scope` in prepared_static_recovery.py); the
barge screen `evidence/m25_barge_screen.py` passes `--load-families
nodal,element,pressure`. Cross-version digest probe byte-identical; M25 tests 7
passed with lean holdouts GO (`m25-assessment-01.json`); regression failures only
the known pre-existing authority tests plus the M24 test refusing to overwrite its
preserved evidence file. Checks 112.25 of 150 s. Barge epoch m25 1,230.74 of
1,500 s: vectorized lean 82.0 / 78.1 s versus canonical 529.1 / 531.3 s, complete
workload 6.46x primary, 6.80x holdout; vectorized preparation 86.5 to 63.2 s and
88.7 to 59.3 s. Vectorized outputs byte-identical to M24, canonical outputs
byte-identical to M22. Report `docs/PREPARED_STATIC_M25_S3_AND_LOAD_FAMILIES.md`.

## M25b review fixes — 2026-10-09

User: "Fix the findings, then rerun the evidence" (12 findings from my review with
Codex gpt-6-astra as independent reviewer; `evidence/m25-review/`).
- Capture span admission (findings 1, 2, 8, 9, 10): the trusted scope is considered
  only for exact Q4/S3 clones (other elements: no checks, guarded route as pre-M25).
  Before entry the capture authenticates its span helpers and the scope tables
  (refuse on change) and admits the span only when the proofs that
  boundary._run_foreign_code_free_load_vector uses hold (builtin NumPy error and
  warning routes, untouched routing classes, exact LoadCase for the pressure
  probe) plus native material/section authority; otherwise the pre-M25 per-call
  guarded route. The proofs are re-checked after the span (refuse on change).
  Plain functions replace the context-manager helper; one `_SCOPE_PAIRS` table
  derives the factory and class tables.
- Table rebinding (finding 3): the owned-scope factory check also verifies that
  the module tables are still the import-time objects (covers owned_recovery_scope).
- Tests (4, 5, 7): repeatable criteria tests (no evidence writes in M24/M25 test
  files; one-shot `test_prepared_static_response_m25_assessment.py` writes
  m25-assessment-02.json); guard counts per code location; trusted-versus-guarded
  capture identity for staged Q4, warped (non-staged) Q4, S3, pressure-only and
  beam; Codex substitution and NumPy-handler scenarios; rebinding and code-swap
  refusals; exception propagation.
- Probe (6): `evidence/m25_digest_probe_v2.py` adds a warped Q4 model and hashes
  numeric identities and warmed owner state.
- Report wording (11) and screen parsing (12).
Evidence rerun: v2 probe pre-M25 versus fixed source; tests and regression suites
(checks at most 200 s); barge epoch m25b 1,500 s for matched lean and canonical
primary/holdout runs. Earlier M25 evidence is preserved.

### M25b result — 2026-10-09

Fixes implemented; v2 probe pre-M25 versus fixed byte-identical; tests 26 M25,
regression 88/88, base 112/115 (known failures), ANYfem 16/16; assessment
m25-assessment-02.json GO; checks 119.13 of 200 s. Barge epoch m25b 1,283.45 of
1,500 s, outputs byte-identical to M24 lean / M22 canonical; preparation within
noise of M25 (canonical runs overlapped the Codex re-review, so their timings are
not clean). Codex re-review of the fixes: 5 of 12 fixed, 7 partially; open BLOCKER
(material proof can run foreign code after the other proofs) and 5 SHOULD-FIX;
see the M25 report. No further fixes made yet; S3 not integration-ready.

### M25c second review fixes — 2026-10-09

User: "Fix the open findings, then run Codex review again". Material proof made
callback-free on the clones and ordered (NumPy routes last); closure-held
authentication facts with a checker held by the capture as a keyword default and
run by every capture caller; opt-in assessment file; plain span arguments; fuller
fingerprints (probe v3); revocation and cancellation tests. Codex blocker
reproduced on the M25b source and closed. Evidence: probe v3 identical; tests
99 + 1 skipped, base 112/115 (known), ANYfem 16/16; m25-assessment-03 GO; barge
lean outputs byte-identical to M24; epoch m25c 392.6 of 400 s, timings
contaminated by machine load (holdout rerun timed out, preserved); admission cost
measured at 279 us per capture. Codex re-review follows.

### M25d — 2026-10-09

Codex re-review of M25c stopped by the OpenAI content filter; before stopping it
found a regression (numpy module __getattr__ during the last proof). Fixed with a
module-hook check (780 modules) and a before/after identity snapshot around the
proofs, proofs back in the boundary's order, cheap exit checks. Tests verified to
fail on the sources they guard (pytest needs -o pythonpath=... because
pyproject sets pythonpath=src). Evidence: probe v3 identical; tests 103 + 1
skipped, base 112/115 (known; also fail on pre-M16/pre-M25 baselines when loaded
correctly), ANYfem 16/16; m25-assessment-04 GO; reproductions safe; barge lean
outputs identical to M24, timings contaminated by machine load; admission ~475 us
per capture (~4.5 s per barge preparation). Codex re-review follows.

### M25e — 2026-10-09

Codex review of M25d: 5 blockers, 4 should-fix, 1 nit. Fixed blockers 1, 2, 4,
part of 3 and should-fix 6, 8, 9 (owner-identity check after every Q4/S3 capture;
refuse on any change during admission; pinned late hooks; module table after all
imports with sys.modules bindings; class-method code in the snapshot; non-raising
pressure-helper proof; proofs' exceptions fall back). Not fixable in-process and
shared with the existing trusted scopes: blocker 5 (tracers, threads, finalizers,
signal and audit hooks), should-fix 7 (authenticating the authenticator), rest of
3. Admission ~650 us per capture (~6 s per barge preparation; S3 nets ~19 s).
Evidence: probe v3 identical; tests 115 + 1 skipped, base 112/115 (known), ANYfem
16/16; m25-assessment-05 GO; barge lean outputs identical to M24 (timings mildly
contaminated). Owner decision recorded in the report: keep, opt-in or remove S3.

### Codex review of M25e — 2026-10-09

2 blockers (S3-specific: private mesh provider / material class not authenticated
by the owner check; runtime module rescan can invoke a descriptor), 4 should-fix
(cancellation swallowed by the new except Exception; append-only rescans; two tests
not independently sensitive; shared primary-exception precedence), 3 nits. Previous
round's blocker 5 and should-fix 7 accepted as residuals under the shared model.
Not acted on yet; owner decision on S3 (keep / opt-in / remove) still open.

### M25f — trusted capture opt-in (owner decision) — 2026-10-09

User: "Go with option 2, make it opt-in". Solver option trusted_capture (default
False) on prepare_static_evaluator / response factory (ANYfem passes it through);
default capture = pre-M25 statements, no admission; opt-in = M25e path via a
context variable set for that preparation's snapshot capture. Round-five findings
remain open for the opt-in path only. Evidence: probe v4 identical (pre-M25,
default, opt-in); tests 129 + 1 skipped, base 112/115 (known), ANYfem 17/17;
m25-assessment-06 GO (opt-in); barge lean outputs identical to M24 in both modes,
timings noisy (machine load 18-28%): default prep 98.6/81.4 s, opt-in 70.9/72.1 s.

### M25g-M25o — Codex review of the opt-in change — 2026-10-10

User: "Run Codex review on the opt-in change. If needed, implement findings, then
send to codex again. Proceed until OK." Ten static Codex rounds (sandbox broken, so
bundles in the prompt; read-only). Rounds 1-9 NOT OK, all fixed: revocable opt-in
token (copied contexts lose it), pre-M25 identity expression, then the default
import/route made to run none of the change's own inspection code (module table,
state table, authentication / pressure-helper / material facts all built on the
first opt-in check; no sys.modules or keyed reads of other modules' globals at
import; the owned-scope factory check on the default route is the pre-M25 function,
the scope-table binding check runs only in opt-in admission). Round 10: VERDICT OK,
one NIT (test count) fixed. Evidence: M25 tests 78/78 (m26-optin-review-tests-10d;
the round-9 test fails on m25o-prefix), ANYfem 1/1, probe v4 byte-identical to
pre-M25 with the option off and on (m25o-digest-default/optin). Review files:
evidence/m25-review/optin/ (bundles 1-10, codex-review-optin-1..11).

### M26 — vector build in one pipelined pass; sampled cost map — 2026-10-10

build_vector_recovery pipelined: each owned scope probes the chunk checked last and
reads the next chunk's zero records; memory_check per chunk on the running
estimate (last call = full estimate; maps still allocated only after a check that
includes them). n+1 safe points and scope entries instead of 2n (barge 68 -> 35).
Documented behaviour changes: partial estimate in a memory refusal, error
precedence between chunks, coarser build cancellation. Evidence: probe
m26_vector_probe (317 elements, 3 chunks) identity equal pre/new; tests M26 9/9
(3 schedule tests fail on m26-prefix), regression 140+1 skipped, base 112/115
(known), ANYfem 17/17; barge ABBA outputs byte-identical to pre-M26 and M25f;
gain only 1.0-1.3 s (vector segment 21.7/21.4 -> 20.4/20.4 s) versus the 4-5 s
cProfile-based estimate. M26b: time-weighted stack sampler (cProfile misleads in
authority-heavy code): preparation 83.5 s = Q4 stage compile 27.9, load maps 17.8
(oracle 8.3), pattern source loads 13.1 (native pressure, 61 patterns), stiffness
8.5, vector build 6.9, digest 2.4. Remaining levers are owner decisions (report).
Epoch m26: 824.2 of 1,500 s used. Keep/revert M26 is an owner decision.

Owner decision 2026-10-10: "Keep it. Investigate parallel. Use high effort for
external review if needed." M26 kept; parallel preparation study started (M27).

### M27 — parallel preparation study (prototype only) — 2026-10-10

Study and prototype in ../m27-prototype (v1 kept in ../m27-prototype-v1); product
source unchanged. Isolated `python -I` subprocess workers (not multiprocessing),
plain pickled builtins with globals refused, private owners rebuilt by value
(clone_plain semantics incl. scalar sharing). Stage compile, pressure warm-up and
pattern pressure kernels in workers; parent keeps order, scatter, witnesses and
serial fallback. Evidence: 3,185 Q4 kernels and 194,285 pressure vectors bitwise
equal across processes; barge consumed outputs byte-identical in 7 runs; barge
preparation 45-48 s with 8-16 workers versus 82-113 s serial (1.7-2.5x); v2
failure checks (8 scenarios fall back or isolate correctly; a tampered
non-witness vector is NOT detected — sample witness limit). retained_bytes not
reproducible across processes (CPython shared-key dict layout). Codex high round 1:
UNSOUND for the prototype's general identity/trust claims (site processing under
-I, handshake not authenticating loaded closure, ambient pool, protocol desync,
codec dtype loss, ...); v2 fixes + corrected report + product requirements list.
Report docs/PREPARED_STATIC_M27_PARALLEL_PREPARATION_STUDY.md; epoch m27 855.8 of
1,500 s used. Codex round 2 (high): SOUND WITH CORRECTIONS (callback can change
both worker owner and the parent's expected digest; witness exceptions abort;
quarantine scope; dtype gates on output paths; diagnostics; numbers per worker
count) -> report corrected, requirements list expanded to 10 items. Round 3:
SOUND WITH CORRECTIONS, four wording fixes, applied. Owner go/no-go on a product
implementation pending.

### M28 — block size and case-parallel study — 2026-10-10

User asked for a recommendation for ~10,000 cases; I recommended block size
first, then case parallelism; user: "Yes". Block size (one owner, 300 cases):
4/16/32/64 -> 0.064/0.053/0.050/0.048 s/case, outputs identical; product default
is already 32 (harness used 4 since M8). Case-parallel study (option A: each
worker prepares its own evaluator and runs a contiguous chunk; parent concatenates
with global indices and merges envelopes with the fold rule): 600 saved cases and
10,000 cycled cases -> per-case records identical and merged envelope
byte-identical to serial. 10k: serial 465.6 s; 4 workers 289 s (1.6x, 4.7 GiB);
8 workers 230 s (2.0x, 9.2 GiB). Contention: per case 1.6x/2.0x slower per
worker, preparation ~1.4x slower (memory-bandwidth bound). Recommendation: option
A at ANYfem level (opt-in), then profile per-case memory traffic; M27 lower
priority for long runs. Report docs/PREPARED_STATIC_M28_BLOCK_SIZE_AND_CASE_PARALLEL.md;
epoch m28 1,409.3 of 1,500 s.

### M29 — per-case profile — 2026-10-10

User: "Do a per case profile first". Barge, block 32, PeriodicSample requests:
38 ms/case = recovery 16.6 (lean reaction maps ~8-11, vector maps 5.5, fold 2.2),
outside solver phases 11.1 (ANYfem load construction 6.6 incl. wet-element cache
cleared per case), solve 3.6 + certification 3.4 (backward error rebuilds abs(K)
per call), load evaluation 2.2. Unprofiled levers, all bitwise identical:
vectorised _planned_compact (est. ~8 ms), cache-blocked evaluate_groups (~2 ms),
cached backward-error norm (1.7 ms/call), ANYfem wet cache kept (2 ms), K
multivector (0.5 ms), authority per block (0.6 ms): ~15-18 ms of 38. Note:
StaticLoadRequest-by-name takes the native load path (~0.3 s/case). M28 wording on
memory bandwidth corrected (all phases slow alike). Report
docs/PREPARED_STATIC_M29_PER_CASE_PROFILE.md; epoch m29 625.7 of 1,500 s.

### M30 — per-case levers implemented — 2026-10-10

User: "Proceed as recommended". Implemented (uncommitted): vectorised
_planned_compact, block-wide reaction residual, chunked evaluate_groups (512),
_certified_backward_error with operator norm data computed once (honours an
injected self._backward_error), ANYfem wet-element cache kept for the prepared
context's lifetime (cleared on a failed case). Not done: authority once per block
(checks sit at caller-code windows). Tests: M30 27 + ANYfem wet cache 2; suites
176+1 skipped, base 112/115 (known), ANYfem 60/60; vector probe identical pre/post;
barge 10k: serial 464.9 -> 310.7 s (22.6 ms/case), 8 workers 229.7 -> 193.6 s;
per-case digests and envelope identical to M28 (serial envelope file
byte-identical). Report docs/PREPARED_STATIC_M30_PER_CASE_LEVERS.md; epoch m30
680.9 of 1,500 s.

M30 platform follow-up (2026-10-10): user asked about Linux/macOS, then "Proceed as
suggested". Block-wide K product removed (macOS untestable). Linux (WSL Ubuntu
24.04, Py 3.12, numpy 2.4.3/scipy 1.16.3): regression 172+1 skipped, base 112/115
(known), ANYfem 60/60. numpy 1.26 (declared min): anysolver import fails on the
pre-existing numpy._core import in pinned boundary.py (pre-M16) -> effective
minimum numpy 2. M25 planted-key test made interpreter-independent (ignores
IMPORT_NAME/IMPORT_FROM reads; Py 3.12 reads __name__ on every from-import).
Final Windows: regression 172+1 skipped, base 112/115, ANYfem 60/60; barge 600
final byte-identical to M28.

### M31 — further identical-result levers — 2026-10-10

User: "Step 1, then independent review". Implemented (uncommitted): ANYfem prepared
wet geometry + lazily filled fluid sides; _plain_deepcopy for the per-case
operator info; closed-form storage estimate for int->float dicts; lean selected
reactions combine only kept nodes. Authority-cost item not done (comparator in
pinned boundary.py). Tests M31 15 + ANYfem 2; Windows suites 187+1 skipped, base
112/115, ANYfem 97/97 (incl. wet-pressure suite); Linux same except 6 ANYfem
wet-pressure tests needing shapely/platformdirs (environment). Paired ABBA 2,000
cases: 22.2 -> 16.7 ms/case (-25%), outputs byte-identical; 10k serial identical
to M28 (timing on a slowed machine: 296.7 s). Report
docs/PREPARED_STATIC_M31_IDENTICAL_LEVERS.md. Next: independent review of M30+M31.


### M31b — review fixes for M30+M31 — 2026-10-10

Codex round 1 (gpt-6-astra high, static, evidence/m31-review/codex-review-1.md):
NOT OK, 1 BLOCKER (empty-norm test; not reproducible on numpy 2.4.3, test now
compares outcomes), 7 SHOULD-FIX, 1 NIT. Fixed (uncommitted): wet caches keyed by
surface identity + content fingerprint (all fields, interior point bytes), drop on
change or reduced reserve, accounting keeps case bytes; fluid-side cache cleared
when its producers change (bindings, code, defaults, named module bindings) and
used only under NumPy default errstate with coordinates < 1e150; public
wet_element_pressures returns fresh writable arrays, solver path pressures-only;
backward-error original captured at import (_ASSEMBLY_BACKWARD_ERROR); norm data
per block after the solve (response: lazily, again after a canonical solve), max
only of finite sums; evaluate_groups chunked only under default errstate with
column-order fallback on non-finite values (one finiteness pass); lean reactions
reverted to pre-M31; _plain_deepcopy memo sentinel; M30 count NIT. Tests: m30 93,
m31 13, ANYfem wet cache 13; mutation check 12/13 caught (13th unobservable on
numpy 2.4.3). Windows: regression 255+1 skipped, base 112/115 (same three also fail
on m30-prefix and m16-baseline), ANYfem 106/106. Linux final: same, ANYfem 100/106
(6 environment). Barge 2,000: byte-identical to pre-M31, about 17.6-18.2 ms/case
(pre-M31 22.2, M31 16.7). Next: Codex round 2 (bundle 2), repeat until OK.

### M31c — round-2 review fixes — 2026-10-10

Codex round 2 (bundle 2): NOT OK, 6 SHOULD-FIX (round-1 1,3,5,6,8,9 resolved;
2,4,7 partial). Fixed (uncommitted): fluid-side reuse decided after the pressure
source (caller code) with a post-callback surface-state check; reuse only while the
whole fluid-side chain is the import-time original (_SIGN_CHAIN: bindings, code,
defaults, closures, named module/builtin bindings and named module attributes) and
for plain WetSurface records (str name/fluid side, float64 point); replaced
functions called every time with fresh writable arrays; run-time FP environment
check (round to nearest, no FTZ/DAZ) for sign reuse and chunked vector maps; norm
data only for exact-CSR immutable bytes-backed buffers with unchanged part objects;
kept selection/fingerprint charged to the reserve (exact-charge test); test
comparator compares warnings. Tests m30 95, ANYfem wet cache 16 (reuse observed by
poisoning kept signs); mutation 19/20 (unobservable max). Windows 257+1 skipped,
112/115, ANYfem 109/109; Linux same (ANYfem 103/109, 6 environment); barge 2,000
byte-identical, 17.2 ms/case. Bundle 3 to Codex.

### M31d — round-3 review fixes — 2026-10-10

Codex round 3 (bundle 3): NOT OK, 6 SHOULD-FIX (in-place dtype reinterpretation of
cached parts; replaced np.matmul call counts; str() on unusual records before the
guard; wrapper installed before import trusted; FP environment not part of the norm
cache; post-callback state retained uncharged). Fixed (uncommitted): parts compared
by object, owner, address, dtype, shape, strides; library bindings captured at import
(_capture_originals/_originals_unchanged in prepared_static_loads, genuineness by
package) checked before every shortcut; FP environment + bindings checked at norm and
at each certification; exact-type fingerprint (None for unusual records -> no
caching at all); sign chain captured only if genuine (own module, file, no closure);
post-source state must equal the charged state; trust-root contract stated in the M31
report. FP probes validated under real _controlfp_s/fesetround changes. Tests m30 102,
ANYfem wet cache 21; mutation 27/28. Windows 264+1, 112/115, 114/114; Linux same
(ANYfem 108/114, 6 environment); barge 2,000 identical, 18.0 ms/case. Epoch m31 has
78 s left. Bundle 4 to Codex (asks to separate OUTSIDE THE CONTRACT scenarios).

Round 4 (bundle 4, 2026-10-10): NOT OK, 8 SHOULD-FIX, all round-3 findings
resolved, trust root accepted. All eight are "a binding replaced after import sees
different calls" (np.any, copy.deepcopy, builder.wet_element_pressures, captured
SciPy method code, NumPy calls in wet-geometry construction, new np.ndim call,
replacement metadata read before rejection, centroid owner vs view passed to the
pressure source). Stopped for the owner's decision on the contract (strict
call-identity for replaced bindings vs. no monkeypatching after import).

### M31e — owner contract decision + round-4 in-contract fixes — 2026-10-10

Owner: "Proceed as recommended" (option 1): replacing library or module functions
after import is outside the supported contract (documented in the M31 report and
the code comments; binding checks stay as defence in depth). Fixed the three
in-contract round-4 items: no np.ndim call in the certification shortcut
(exact-ndarray .ndim), fluid-side bindings compared by identity (_SIGN_FUNCTIONS)
before inspection, pressure source gets an (n, 3) view of a fresh copy as on the
original path. Tests m30 103, ANYfem wet cache 23; mutation 30/31. Windows 265+1,
112/115, 116/116; Linux 265+1, 112/115, 110/116 (6 environment); barge 2,000
identical, 19.1/18.5 ms/case on a busier machine (epoch m31e, 600 s). Bundle 5 to
Codex with the narrowed contract.

Round 5 (bundle 5): NOT OK, 3 SHOULD-FIX + 1 NIT inside the contract; round-4
dispositions confirmed. M31f: norm shortcut only for float64 data / int32-int64
indices (complex data warned twice); contract made precise (FP traps stay masked;
probes must round); kept wet entries revalidated at each request boundary,
fingerprint refuses view-backed interior points and extra attributes; comment fix.
Probe script extended (return codes, control-word readback, full original-vs-new
outcomes under every real mode: 10/10 equal on Windows and Linux). Tests m30 104,
ANYfem 26; mutation 34/35. Windows 266+1, 112/115, 119/119; Linux 266+1, 112/115,
113/119 (6 env). Barge identical; timing unusable (machine loaded by other apps),
added costs measured 1-2 us. Bundle 6 to Codex.

Round 6 (bundle 6): NOT OK, 4 SHOULD-FIX + 1 NIT inside the contract. M31g: sides
reused only for plain float64 magnitudes (custom pressure record iterating code);
the end of the request iteration (end, failure, close) is a request boundary; the
fingerprint includes record-dictionary sizes; records read only through checked
instance dictionaries (exception-free); overhead evidence corrected (helpers with
call counts, < 0.1 ms/case). Contract made precise: only wet-surface records of the
owned copies may change. Tests ANYfem 31; mutation 38/39. Windows 266+1, 112/115,
124/124; Linux 266+1, 112/115, 118/124 (6 env); probes 10/10 in every mode on both;
barge identical, 18.25 ms/case (epoch m31e, 57 s left). Bundle 7 to Codex.

Round 7 (bundle 7): NOT OK, 2 SHOULD-FIX + 1 NIT. M31h: interior point dtype must be
NumPy's float64 dtype object (metadata payload); overhead call counts corrected.
Open (owner): mid-request change of a surface's ref by a custom pressure field — the
pre-M30 prepared path's result depended on whether its per-request memo fitted the
cache reserve; current code always re-resolves. Options: declare mid-request record
changes unsupported (recommended) or reproduce the pre-M30 per-request reserve
accounting. Full re-verification pending the decision.

M31h decision (owner, "Proceed as recommended"): wet-surface records may change
between requests; changing them during a request is outside the contract (pre-M30
result was reserve-dependent). Recorded in code (_wet_key docstring, build.py reuse
comment) and report. Verification: mutation 39/40; Windows 266+1, 112/115, 125/125;
Linux 266+1, 112/115, 119/125 (6 env); probes all modes equal on both; barge
identical, 18.24 ms/case (epoch m31h). Bundle 8 to Codex.

Round 8 (bundle 8): NOT OK, 1 SHOULD-FIX (geometry-only entry kept surfaces
uncharged) + NEEDS non-canonical matrices (confirmed: block path raised where the
original returned inf). M31i: kept selection's surfaces charged; norm shortcut only
for canonical CSR with consistent indptr (SciPy csr_has_canonical_format, fresh).
Owner then: "We will now stop using codex for reviews. If more is needed, have a
round yourself." Round 9 (Claude): full diff walk-through; fixed two stale
docstrings; documented duplicate wet-surface ids (pre-M30 id-keyed cache
reserve-dependent). Final: mutation 41/42; Windows 269+1, 112/115, 128/128; Linux
269+1, 112/115, 122/128 (6 env); probes equal in every mode; barge identical,
18.31 ms/case. Nothing committed.
