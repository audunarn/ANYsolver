# Prepared static evaluator (opt-in)

The milestone-6 mass-capture candidate builds on the milestone-4 shared-recovery route and evaluates arbitrary ordered linear-static cases with
whole-model envelopes and independently selected detailed results. Acceptance and
promotion are not established. Default solve/stream routes remain unchanged; this
candidate remains isolated. The governing record is
`docs/agent_plans/PREPARED_STATIC_IMPLEMENTATION_TASK.md`.

```python
from anysolver import RecoveryConfig, prepare_static_evaluator

selected = RecoveryConfig(element_ids=[1], include_displacements=False,
                          include_stresses=True, include_reactions=False)
envelope = RecoveryConfig(include_displacements=False, include_stresses=True,
                          include_reactions=True)
with prepare_static_evaluator(model, output_dofs=[6, 7, 8],
                              recovery_config=selected,
                              envelope_recovery_config=envelope) as prepared:
    for block in prepared.iter_batches(cases, batch_size=32):
        consume(block.case_ids, block.displacements, block.case_results)
    summary = prepared.envelope_result()
    assert summary.complete
```

`cases` yields existing `StaticCase(case_id, load_case, time)` objects. Repeated
labels and unequal finite times are valid. An optional open native
`AnalysisSession` must belong to the source model, but its factor is never
borrowed. The evaluator owns its snapshot, sparse backend and factor cache;
source deletion/mutation or session closure cannot change captured mechanics.
Explicit close and a weak-reference finalizer share one resource-release path.

## Canonical loads and recovery

Loads retain the canonical full vector, including constrained DOFs. Pressure is
evaluated by the native kernel on owned geometry with the actual case pressure.
Gravity uses each captured element mass matrix times the repeated acceleration
vector, followed by canonical element-order scatter. Model and case-only point
masses are combined before multiplication. This preserves staged arithmetic that
was lost by scaling a unit-pressure vector or multiplying a globally summed
acceleration map. Nodal/element scatter, activity scales, static follower behavior,
and formulation-specific refusals retain the canonical conventions.

`load_families=None` prepares all supported families; an explicit nonempty subset
limits capability. Missing mass or pressure capability fails explicitly when
requested. Native massless beam-shell couplings remain admitted.

Both selected detailed stresses and every envelope stress sample use canonical
native local recovery on private copied element/material/section/initial-field
inputs and a minimal owned mesh. Existing compiled affine maps remain preparation
verification data for detailed recovery, but their collapsed dot products do not
supply emitted stress values. Native von Mises/equivalent measures are retained
without a second arithmetic reconstruction. Requested shell
`principal_stresses_top`/`principal_stresses_bottom` are descending eigenvalues of
the physical symmetric surface tensor, evaluated per physical sample before fold.
Generalized sections preserve their actually available resultants/metadata;
principal stress is refused when physical through-thickness stress is unavailable.
Beam principal stress requires a physical station tensor and is refused. Hill
measures remain an explicit capability refusal. No nonlinear committed-state
loading route is introduced.

The current envelope implementation groups recipes by formulation and uses
bounded one-element/eight-case tiles (shortened at block boundaries). Exact planar homogeneous isotropic qualified
Q4 elements without Hill or explicit initial-field inputs use prepared native
invariant stages. Geometry/frame/Jacobians, constitutive construction, the
35-field stationary solve and four station source/compatible matrices are
captured once. Every case retains the canonical sequence of separate GEMVs:
global-to-local transform, stationary parameters, per-station fields, director
maps, and physical/derived fields. Contiguous C/F invariant layout is retained;
no cancellation-sensitive transforms are collapsed and no cross-case GEMM is
introduced.

Other formulations, warped geometry, generalized sections, nonisotropic
materials and explicit initial-field inputs use the existing owned native
fallback. Prototype ineligibility does not narrow the previously admitted native
capabilities. Both selected detailed recovery and envelope recovery dispatch this
same staged/fallback route. The envelope avoids a whole-model dictionary per
case and does not compile a whole-model affine H. This is invariant hoisting,
not a SIMD/vectorized native batch kernel or a measured speed claim. Diagnostics
expose `prepared_q4_staged_elements`, `native_fallback_reasons`, `execution_route`,
`tile_elements`, `tile_cases`, and `vectorized_native_kernel=False`.

The union of detailed and envelope element selections is recovered once per
physical case. Complete canonical physical fields feed independently filtered outputs;
detailed-only derived measures cannot expand an all-native envelope schema.
Selected history arrays detach from temporary records and tiles. Constraint force
diagnostics are evaluated once per case when either output needs them, retaining
full residual/MPC truth before separately filtering selected force maps.

Only envelope winner reduction is vectorized across the bounded case tile.
Element mechanical arithmetic remains staged per case. Tile winners reduce into
block winners, retaining the earliest input index on exact ties and complete
associated fields from the same sample. Each entity's block winners merge once
into a transaction. Unchanged governing modes share committed storage; changed
modes copy before writing. No committed array changes before publication.
Block diagnostics expose `shared_recovery` operation counts, tile width and
copied-mode count. These counts establish eliminated duplicate operations, not
elapsed-time savings.

M6 changes only mass preparation on the restored M4 candidate. The M5 numeric-tuple/selector experiment did not
demonstrate a reliable speedup and has been archived outside the active source
and tests. See `PREPARED_STATIC_M5_SCREEN.md` for its preserved evidence.

## Detached summary and transactions

`envelope_result()` returns `None` when disabled. Otherwise it returns
`PreparedEnvelopeResult(complete, cases_processed, extrema, snapshot_identity,
diagnostics)`. Diagnostics include the content digest and captured source revision.
Each `PreparedEnvelopeExtrema` identifies `quantity`, `entity_id`, `component` and
`original_shape`, and provides `minimum`, `maximum`, `absolute` (also available as
`absolute_maximum`). Each governing record contains signed `values`, `case_ids`,
`times`, `input_indices` and `associated_fields`. Value/identity arrays have the
original component shape. Associated field arrays have shape
`original_shape + associated_field_shape`, so each winning scalar retains its
coherent same-element requested physical fields from that case. All returned
arrays/mappings are detached from the accumulator.

Stress quantities use `quantity='stress'`; nested numeric component paths are
tuples. Reaction quantities are `support_reactions`, `mpc_slave_forces`, and
`mpc_master_equivalent_forces`, with component `force` and six-component arrays.
All selected nodes, including omitted canonical zero entries, are represented.
Displacement selection uses six-DOF node vectors. Exact ties retain the earliest
input index; no tolerance ties, zero clipping, or independently assembled extreme
stress tensor is used.

One envelope iterator may be active. Starting a new run resets its summary when
iteration begins. A whole block publishes only after solving, backward-error
certification, canonical recovery, output authority checks, progress callbacks
and cancellation checks succeed. Callback errors propagate. Failure, cancellation
or early close preserves only prior certified blocks, with `complete=False`.
Normal exhaustion becomes complete only after input cleanup and final open,
cancellation and runtime-authority checks; an empty normal run is complete.
Callbacks can inspect the prior detached summary, never a partial transaction.

## Authority and resources

Preparation requires reviewed exact native model/mesh/node/element/material and
section providers, plain data and no instance helper shadows. Source coherence
checks include raw containers and executable facts before/after capture. Runtime
scopes bracket package-owned numerical blocks only: no input iteration, callback
or yield occurs inside them. Native class/helper facts and NumPy error routes are
checked at entry/exit. Q4/S3 trusted-scope factory module identities, code/defaults,
closure executables and relevant global bindings are pinned before receiving
private elements. Nested borrowing is revocable. Secondary output-authority
failures attach notes to a primary failure. The new Q4 kernel module bindings,
code/defaults/closures, class executable facts and referenced globals are also
checked before receiving owned buffers. Stage arrays are immutable, counted in
retained storage, and included in the numeric recipe digest identity.
Shared recovery entry bindings and executable facts, reducer method/global-helper
bindings, result classes and the driver constructor alias are checked before
private data is passed. Checks also precede summary copying and resumed block
accounting after a caller yield.

Memory policy includes snapshot/recipe/cache storage, factors (reported storage
or a documented estimate), committed and worst-case transaction accumulators,
block-winner scratch, selected histories, local tiles/gathers, numerical workspace
and actual incoming packet storage. Current retained
label storage is recomputed between blocks. Under an explicit limit, variable
packets use one-case blocks and are checked before copying. Preparation refuses
when factors plus one case and envelope workspace cannot fit. These are bounded
accounting estimates, not an exact process-RSS claim. The output summary is a
caller-owned detached copy.

## Evidence and historical failures

All previous failures remain under `../evidence`; old failures are not acceptance
results for this candidate. Milestone 1's 97-test integrated pass did not establish
promotion: its 200-case holdout had four governing-identity differences and was
slower than stream. Earlier `solver-roundoff-02` isolated load summation and
collapsed-recovery cancellation differences. The original principal failure in
`solver-finish-12` was retained as `tests/prepared_static_qualification_cases.py`.
The later recipe copy/cache failures in `solver-refinement-02/03/04` also remain.

Milestone-2 checks use the separately authorised 180-second correctness budget:

| Evidence directory | Result | Process-wall seconds |
|---|---|---:|
| m2-solver-01 | 29 passed | 16.2718796 |
| m2-solver-02 | 31 passed, 1 fixture typo (preserved) | 15.1659740 |
| m2-solver-03 | 52 passed, including independent contracts/principal | 23.3201360 |
| m2-solver-roundoff-01 | Old case048 exact full F, u and stress | 4.2468654 |
| m2-solver-04 | 7 passed, 1 native-derived reconstruction difference | 11.5436330 |
| m2-solver-05 | 8 passed after native-derived preservation repair | 8.0523250 |
| m2-solver-06 | 16 passed, including factory and exhaustion adversaries | 7.5215955 |
| m2-solver-07 | 2 focused memory/stability tests passed | 4.2789498 |

Worker correctness use is 90.4013583 seconds; 89.5986417 remain. Counts across
runs overlap and are not a unique-test total. Cases000/048/576 now have exact
stream/prepared displacement, stress and envelope values/governing identities in
the focused regression. These are bounded checks; there has been no worker
benchmark or full 10,000-case campaign. Root owns the independent matched screen,
performance measurement and final acceptance.


## Milestone-3 prototype checks and limits

No new benchmark/profiling authority was consumed. The existing remaining worker
correctness allocation was 89.5986417 seconds at milestone start. Evidence:

| Evidence directory | Result | Process-wall seconds |
|---|---|---:|
| m3-solver-01 | Original cases000/048/576 exact history/envelope regression passed | 4.9887507 |
| m3-solver-02 | 7 focused new-route tests passed | 5.1596742 |
| m3-solver-03 | Broad suite timed out at 40s; 73 completed dots, no assertion failure printed; no final test count | 40.0489397 |
| m3-solver-04 | 15 targeted activation/fallback/application tests passed, 6 deselected | 16.9928113 |

Milestone-3 worker use is 67.1901759 seconds, leaving 22.4084658 seconds of the
existing allocation. The broad timeout remains incomplete evidence and was not
rerun wholesale. Focused tests cover exact full-field recovery under rotated/skew
geometry, both director polarities, multiple displacement scales with rigid
offsets, immutable stage buffers, public binding/code authority refusals,
source deletion, warped fallback, and explicit initial/generalized/material
eligibility predicates. An isolated arithmetic-kernel test verifies zero native
stationary-solve dispatches during repeated staged evaluation; the public route
separately refuses that test's monkeypatched native authority. This is operation
elimination evidence, not a timing measurement.

The final targeted check includes real application integration and exact public
activation parity at requested block sizes 1/8/32 with 32 samples. Root independently
reported a passing 33-distinct-case check at block sizes 1/8/32 plus restart,
covering bit patterns of displacements, full stresses, associated envelope fields,
governing identities and time. Root owns that separate evidence and adjudication.
There is still no full 10,000-case campaign, SIMD claim, measured M3 speedup or
promotion decision established by this prototype.

## Milestone-4 shared recovery checks

The separately authorised worker correctness ceiling is 120 process-wall seconds.
All runs use the task runner, `--kind check --benchmark-epoch m4`, single-thread
environment settings and `NUMBA_DISABLE_JIT=1`; full commands, candidate identities,
stdout/stderr and JUnit records remain in the corresponding evidence directories.

| Evidence directory | Result | Process-wall seconds |
|---|---|---:|
| m4-solver-01 | 18 envelope tests passed | 9.4017513 |
| m4-solver-02 | 3 passed, 4 test-oracle failures preserved | 10.3184507 |
| m4-solver-03 | 25 focused/envelope tests passed | 11.7556004 |
| m4-solver-04 | 29 passed, including independent M4 selection/isolation | 15.4429210 |
| m4-solver-05 | 31 evaluator/Q4/application integration tests passed | 24.1139243 |
| m4-solver-06 | 5 authority tests passed, 6 deselected | 3.5357256 |
| m4-solver-07 | 12 final focused M4 tests passed | 6.8087658 |

Worker use is 81.3771391 seconds, leaving 38.6228609 seconds. Counts overlap across
runs and must not be summed as unique tests. Run02 incorrectly used exact decimal
input values as canonical reaction/COW tie oracles; the actual canonical value was
an adjacent binary64 value. The repaired checks use recovered canonical values,
with exact comparisons retained and no tolerance change.

Focused coverage includes overlapping and disjoint selections, detailed-only
principal derivation with all-native envelopes, block sizes 1/8/32 with an uneven
19-case sequence, repeated labels/exact ties, independent node filtering,
copy-on-write mode preservation, binding/helper authority refusal before private
buffer observation, and labelled reduction failures. Existing envelope tests cover
transactional callback/cancellation/cleanup behavior, one-case memory refusal,
stable/reset accumulator storage and historical exact counterexamples. The
independent M4 test checks selected/support separation and returned-array mutation.
No worker benchmark, profiling job or full 10,000-case campaign was run. Root owns
independent review, matched performance evidence and acceptance.

## Archived milestone-5 numeric recovery checks

Root's charged profile (`../evidence/m5-profile-breakdown.json` and `.pstats`)
found record-related work modest: approximately 0.07s in numeric-field discovery
and 0.05s in deepcopy within the profiled sample; shared recovery was approximately
0.90s. These overlapping cumulative profile times do not predict a large end-to-end
gain. This milestone therefore changes only numeric field packaging/selection,
retaining canonical arithmetic and the existing fallback routes.

| Evidence directory | Result | Process-wall seconds |
|---|---|---:|
| m5-solver-01 | 9 new numeric-route tests passed | 6.7135382 |
| m5-solver-02 | 42 existing Q4/envelope/shared tests passed | 23.9642294 |
| m5-solver-03 | 29 evaluator/application integration tests passed | 19.5148943 |

The separate worker correctness ceiling is 120 seconds; 50.1926619 seconds were
used and 69.8073381 remain. All checks used the task runner with `--kind check
--benchmark-epoch m5`, unique preserved evidence, single-thread environment settings
and `NUMBA_DISABLE_JIT=1`. The new tests cover exact full-field native comparison
under rotated/skewed geometry, both director polarities, rigid offsets and multiple
scales; tuple-to-record detachment; public numeric/fallback activation at block
sizes 1/8/32; principal fallback; numeric helper authority; and nested schema paths.
Existing tests preserve historical exact counterexamples, coherent governing
fields, transaction/cleanup behavior, memory refusal and real application parity.
There were no failed M5 worker checks. No worker profiling or benchmark job ran;
root owns independent review, comparative measurements and acceptance.

M5 performance disposition (2026-10-08): the numeric-envelope experiment passed
correctness checks but did not establish an incremental complete-workload gain.
It is archived under `../evidence/m5-experiment`; M4 has been restored byte-for-byte
as the active source. Do not describe M5 as a measured speedup.
See PREPARED_STATIC_M5_SCREEN.md for the NO_GO screen and preserved M4 comparator.

## Milestone-6 mass preparation

Preparation captures each admitted element's native mass matrix once into immutable
owned storage, in canonical element order. Those same matrices supply the existing
per-case `M_element @ acceleration` arithmetic and scatter. Model point masses and
case-added masses still combine once before multiplication at translational DOFs;
load activity scaling and constrained-node loads are unchanged.

The removed internal `acceleration_map` had no evaluation consumer. Three canonical
unit-acceleration assemblies previously built that unused global basis; they were
not oracle comparison checks. `_verify_maps_against_oracle` remains unchanged and
still performs its independent canonical full-load acceleration comparison, including
case-added masses. No new cache, native method replacement or trusted scope was added.
The prior unit assemblies also implicitly checked whether unit-acceleration loads
were finite. That capability boundary is retained by applying the three unit axes
to the captured matrices, with canonical element scatter/activity and combined
model point masses, then checking each full vector. These transient checks do not
recompute native masses or retain an acceleration basis. No stricter blanket
matrix-finiteness or shape criterion was introduced.
If native mass capture raises a capability error, partial mass maps are discarded
and acceleration is unavailable, while other admitted load families remain usable.
The snapshot digest changes because the obsolete internal field is absent.

A focused call-event regression records exactly two native beam mass evaluations
and one canonical full-load assembly during acceleration-only map compilation:
one capture and one unchanged verification pass. The old source contains five
mass passes (three basis assemblies, capture and verification); that baseline count
is source-derived, not a newly measured timing. The deterministic test callback
records code-call counts only, restores the prior callback in `finally`, and does
not alter package authority. No speedup is inferred from these counts.

| Evidence directory | Result | Process-wall seconds |
|---|---|---:|
| m6-solver-01 | 6 focused mass-capture tests passed | 3.7410248 |
| m6-solver-02 | 65 evaluator/contract/envelope/independent tests passed | 22.6023992 |
| m6-solver-03 | 31 real application integration/envelope/shared tests passed | 14.4853677 |
| m6-solver-04 | 9 mass-capture/refusal tests passed, 2 expected warnings | 3.6899692 |
| m6-solver-05 | 18 mass-capture/independent tests passed, 2 expected warnings | 5.6500886 |

The separate M6 worker correctness ceiling is120 seconds:50.1688495 used and
69.8311505 remain. Counts overlap across runs. All runs use the task runner with `--kind check
--benchmark-epoch m6`, unique preserved evidence, single-thread settings and
`NUMBA_DISABLE_JIT=1`. New coverage includes exact full-F axis/general acceleration,
nontrivial load activity distinct from mass activity, structural and changing
case-added point masses, constrained loads, immutable mappings/mass arrays,
post-capture material/activity/point-mass mutation, native massless couplings,
partial capture failure preserving nodal loads, and cancellation at the load
preparation boundary. No failed M6 worker checks, worker performance profiles or
benchmarks occurred. Root owns independent review and performance adjudication.
Independent Read review identified that invalid mass data could otherwise escape
the acceleration capability boundary into final verification. The repair adds
native NaN/Inf and finite individual matrices whose full-vector accumulation
overflows as explicit refusal regressions; nodal loads remain usable. Runtime
warnings from those intentional invalid inputs are preserved in evidence.

## M7 preparation authority amortization (candidate)

Pressure-map verification now evaluates its private pressure recipes in one
existing owned operation scope. The canonical full-load oracle remains outside
that scope, with the original probes, arithmetic and residual criterion. Ingress,
probe-record, evaluation-helper and recipe authority are checked before entry.
Runtime case load evaluation already used a block scope and is unchanged here.

Envelope preparation admits and captures all requested native recipes outside the
numerical scope, then samples their zero-displacement schemas in one owned span.
Configuration/source observations and conversion of selection metadata remain
outside; exact plain component names and helper/record executable authority are
checked before private sampling, with native and helper checks again on exit.
Unknown components still fail explicitly and the scope is revoked on failures.
No canonical stress arithmetic or envelope governing/tie rules changed.

The representative pilot explicitly requests stress envelopes for all physical
Q4/beam elements and reactions for all nodes. Couplings remain in the mechanics
and reaction calculation but do not advertise von Mises stress. This scope is
logged in the pilot artifacts; it is not an all-component qualification claim.
Focused M7 checks and operation counts are recorded in
`.prepared-static-evidence/m7-solver-handoff.md`. Representative timing, independent review and final verification are recorded in `PREPARED_STATIC_M7_SCREEN.md`. Preparation authority-call reduction alone is not a measured end-to-end speedup.

M7's recurring-cost candidate also avoids copying/discarding the whole entry
header when constructing an empty entity reducer. Retained-memory accounting uses
a private lazy cache of the existing exact `_storage` calculation, invalidated
before allocation or mutable-mode updates. Fresh transactions recompute their own
storage and own their schema-index header. This changes neither envelope values
nor tie/associated-field semantics. The resource model counts retained solver
allocations; it is not an operating-system RSS limit. The paired representative holdout measured 21.7% less warm history time; cold complete-workload gains were smaller. See `PREPARED_STATIC_M7_SCREEN.md`: the 2x complete-workload / 50% memory promotion target was not met.

