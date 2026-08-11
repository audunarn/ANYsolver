# Sol Ultra promotion decision log

This is the closed qualification record for the Sol Ultra performance campaign
on `performance_2`. A decision of **promote** applies only to the eligibility
envelope stated below; the scalar or full-coordinate implementation remains the
correctness oracle and fallback.

## Qualified revisions

- Immutable baseline: `575ddd3fd7712378e6a24b901c647cf101d7b0dc`
- Qualified source: `eb41e73c28205e7dc147895bc847b3153b0f879a`
- Incoming ANYfem functional commit: `e1facbb630c824a60671af345b297ac22c4c3c5c`
- Semantic merge preserving that functionality: `5ad9af078e2dee2aa9bf2af943649cc393f72fe9`

Both `sol_ultra_final.json` and
`sol_ultra_numerical_comparison.json` identify the exact qualified source SHA.
The commit containing this report and the generated artifacts is intentionally
a report-only descendant; it changes no production, test, script, or
documentation source relative to the qualified source.

## Closed qualification evidence

| Gate | Result |
| --- | --- |
| Complete test suite | **769 passed**, 0 failed, in 321.73 seconds from a clean detached checkout of the qualified source |
| Independent numerical comparison | **13/13 passed**, 0 failed, 0 unavailable, 0 metric failures; 3 expected candidate-only impact reuse diagnostics |
| ANYfem compatibility | **8/8 passed** for prescribed actions, capacity, arc length, support reactions, imperfection, and affine-coordinate constraints |
| Final performance campaign | **16/16 completed**, 0 failed, 3 warm repeats, matched environment and immutable merge base |
| Aggregate warm-median sum | 4.940335 seconds to 1.541581 seconds: **3.205x** |
| Final source audit | **GO** for affine/reaction semantics, thread ownership, PyPardiso locking, and incoming ANYfem contracts |

The two mandated nonlinear-assembly commands were also repeated at the final
source SHA with ten warm samples:

| Case | Candidate legacy | Candidate persistent | Candidate direct | Direct gain vs candidate legacy | Mature-path change vs baseline |
| --- | ---: | ---: | ---: | ---: | ---: |
| Selector | 4.965 ms | 1.445 ms | 0.562 ms | **8.830x** | persistent +3.73%; direct +4.46% |
| Weighted MPC | 8.780 ms | 1.460 ms | 0.559 ms | **15.716x** | persistent +2.03%; direct +2.76% |

## Representative regression audit

No regression is hidden by the aggregate speedup. Every final case above the
five-percent review threshold was investigated and dispositioned:

| Case | Final three-repeat result | Audit and disposition |
| --- | ---: | --- |
| Isotropic S4 nonlinear | **1.013x faster** | Mature isotropic assembly remains within the gate. |
| Weighted MPC | **1.073x faster** | Final full-case result and both mandatory mature paths pass. |
| Arc-length oracle | 3.5% slower | Passes the gate. An adjacent clean 11-repeat pair measured +4.7803%, with identical peak, step, and Newton histories. |
| Factorization reuse | **1.054x faster** | A separate safety-overhead audit measured +4.8% total and +0.6% in the factorization phase; process-wide PyPardiso serialization is retained. |
| Linear shell K/M assembly | 6.0% slower in the short final sample | A longer clean unchanged-path audit measured +1.8% total, +2.7% K, and +1.7% M. The short-sample total is classified as timing variance; the experimental CSR replacement remains rejected. |
| Selective recovery consistency | 9.8% slower | The measured small-selection two-thread safety path is explicit opt-in and is **not** promoted as a performance path. Its targeted serial recovery phase was 2.3% faster. Production qualification uses one recovery thread; the large compiled S4 case was **10.841x faster**. |

Other material final gains include transient selected output at 9.446x,
Hill-48 at 5.962x, orthotropic S4 at 1.578x, generalized S4 at 1.290x,
rotated shell at 1.477x, rotated beam at 1.161x, and nonlinear impact at
1.020x. Wall-clock evidence captured while antimalware activity was observed
was discarded and is not used by this record.

## Decision table

| Workstream | Qualification and evidence | Decision |
| --- | --- | --- |
| Persistent nonlinear state | Static/arc commit, rejection, restart, initial-field, snapshot, and materialization parity; 9.08x synthetic transaction throughput and qualified lifecycle parity | **Promote** qualified von Karman static/arc lifecycle; **defer** nonlinear-impact state transactions |
| Hill-48 | Scalar-oracle parity for canonical curves, mixed elastic/yielding rows, state, and tangent; 5.962x final case | **Promote** compiled canonical-curve path; retain scalar and numerical-tangent row fallbacks |
| Orthotropic S4 | Material-axis and geometry parity; focused 11.571x linear and 127.745x nonlinear; 1.578x final case | **Promote** qualified homogeneous orthotropic S4 |
| Generalized S4 | Force, tangent, mass, nonsymmetric `B`, and resultants-only recovery parity; 1.290x final case | **Promote** qualified pre-integrated `A/B/D/As` S4 |
| Rotated corotational | Rigid rotation, objectivity, force, and tangent checks; 1.477x shell and 1.161x beam final cases | **Promote** direct 3x3 block rotations; **defer** broader frame/local-response batching and consistent-frame replacement |
| Impact tangent reuse | Exact zero-budget oracle; contact, active-set, damage, deletion, plastic, cutback, and refresh checks; 46--59% fewer factorizations | **Promote** conservative opt-in modified Newton |
| Direct reduced impact | Selector and weighted-MPC parity; 3.113x assembly and 98.97% of eligible full assemblies avoided | **Promote** elastic, zero-affine-offset scope; **defer** plastic/fiber/damage/deletion/affine scope |
| Compact impact contact | Exact force/order/sticky/public-record parity and fivefold fewer record materializations | **Promote** solve-local compact work buffers |
| Incremental damage matrices | Exact K/M and point-mass parity; combined cached-term plus plan memory gate; 11-update break-even | **Promote** only when event-density and combined-memory gates pass |
| Analysis session | Reuse/no-reuse parity; topology, geometry, material, constraint, value, foreign-plan, close, and concurrent-cache tests; 2.562x repeated static evidence | **Promote** optional caller-owned bounded sessions |
| Transient reduced data | Exact preprojected-load and selected-row parity; 9.446x final case | **Promote** selected-output/reduced-load path |
| Recovery batches | Component, frame, surface, ordering, provenance, and fallback parity; 10.841x large final case | **Promote** large qualified S4 recovery; retain scalar path below 100 selected elements and for unsupported formulations |
| Arc-length bookkeeping | Exact reaction/history/progress/constraint contracts and accepted-force reuse; final and 11-repeat audits within five percent | **Promote** qualified force-driven optimizations; prescribed paths retain their exact affine formulation |
| Automatic thread selection | Zero numerical differences, but no repeatable scaling benefit and recovery worsened with more workers | **Reject** automatic/default scaling; qualify and recommend explicit thread count 1 |
| Experimental CSR linear assembly | Production performance gate was not demonstrated | **Reject** production promotion; retain qualified COO implementation |

## Qualification boundaries

- Persistent state transactions cover qualified von Karman static and
  arc-length shell lifecycles. Nonlinear impact retains its dictionary
  checkpoint/cutback model.
- Compiled Hill-48 accepts canonical ANYmaterial curve packs. Custom protocols
  and invalid or pathological rows use the safeguarded scalar oracle.
- Orthotropic/generalized batching is restricted to eligible S4 elements.
  Triangles, Q8/Q8R, unsupported laws, and exact initialized-state overrides
  remain scalar. Generalized recovery reports resultants and does not invent
  ply stresses.
- Corotational promotion replaces dense block rotations only on the ordinary
  rotated path. The consistent tangent keeps its frame-sensitivity terms.
- Direct reduced impact requires Numba, von Karman kinematics, nonidentity
  constraints, exact zero `u0`, no plastic/fiber history, and no
  damage/softening/deletion. Cost and retained-map caps still apply.
- Damage eligibility accounts for the peak combined footprint of the plan and
  simultaneously retained exact-fallback terms.
- `AnalysisSession` is optional, model-owned, bounded, rejects stale/foreign
  plans, and explicitly releases its caches.
- Recovery selections below 100 elements deliberately retain scalar recovery.
  The small two-thread path is a safety option, not a promoted speed path.
- Q8R acceleration, persistent impact state, upper-triangle-only integration,
  broad corotational batching, GPU acceleration, and language replacement are
  outside this campaign's promoted scope.

## Incoming ANYfem functionality

The incoming prescribed-displacement functionality is preserved, not replaced
by performance code. The semantic merge retains optional prescribed-only
reference actions, capacity and imperfection workflows, affine constraints,
arc-length prescribed paths, support-reaction histories/progress payloads,
restart scaling, and constraint postchecks. The focused compatibility audit
passed all eight checks against the live ANYfem checkout.

## Thread and backend decision

The reproducible sweep observed no useful default scaling: nonlinear assembly
from 1 to 16 threads ranged from 0.988x to 1.016x, PyPardiso solve from 1 to 8
threads ranged from 0.905x to 0.977x, and recovery slowed as workers increased.
All output differences were zero and normal/exception restoration passed.
Qualification therefore uses and recommends one explicit thread. The API still
honors explicit caller choices, prevents nested-pool amplification, serializes
the non-thread-safe PyPardiso lifecycle, and leaves SuperLU concurrent.

## Normalized phase coverage

A null normalized phase means **unavailable**, never zero. The baseline exposed
timers for model preparation (6/16 cases), constraint planning (1/16), K (5/16),
M (4/16), KG (1/16), nonlinear local response (5/16), reduced scatter (1/16),
force and tangent projection (1/16 each), factorization (3/16), linear solve
(1/16), stress recovery (2/16), and total wall time (16/16). It exposed no
normalized timer for constitutive update, state packing/commit/materialization,
full scatter/reconstruction, contact search/load, or history storage. The final
comparison retains explicit `n/a` coverage and fabricates no phase timings.

## Release closure

The required eight artifacts are:

1. `sol_ultra_environment.json`
2. `sol_ultra_baseline.json`
3. `sol_ultra_baseline.md`
4. `sol_ultra_final.json`
5. `sol_ultra_comparison.md`
6. `sol_ultra_decision_log.md`
7. `sol_ultra_independent_verification.md`
8. `sol_ultra_numerical_comparison.json`

The final and numerical captures are clean and SHA-matched, the final campaign
has three warm repeats and the complete 16-case inventory, the numerical suite
has no unavailable cases, and all reviewed regressions have a recorded
disposition. The comparison report is generated deterministically from these
artifacts plus the transient thread-scaling evidence. No ninth release artifact
is committed.

## Reproduction commands

Run from a clean checkout of the qualified source in PowerShell:

```powershell
$env:PYPARDISO_MKL_RT = 'C:\Python\Python313\Library\bin\mkl_rt.3.dll'
$python = 'C:\Github\ANYsolver\.venv\Scripts\python.exe'

& $python -m pytest -q --basetemp=.pytest_tmp_sol_ultra_final
& $python scripts/verify_sol_ultra_numerics.py capture --solver-root (Resolve-Path .).Path --label candidate --suite full --output .sol_ultra_verify_candidate.json
& $python scripts/verify_sol_ultra_numerics.py compare --baseline .sol_ultra_verify_baseline.json --candidate .sol_ultra_verify_candidate.json --json-report reports/performance/sol_ultra_numerical_comparison.json --markdown-report reports/performance/sol_ultra_independent_verification.md
& $python scripts/benchmark_nonlinear_assembly.py --nx 20 --ny 10 --repeats 10
& $python scripts/benchmark_nonlinear_assembly.py --nx 20 --ny 10 --repeats 10 --weighted-mpc-rows 12
& $python scripts/benchmark_sol_ultra_performance.py --suite full --repeats 3 --label final --output reports/performance/sol_ultra_final.json --no-markdown
& $python scripts/compare_sol_ultra_performance.py --baseline reports/performance/sol_ultra_baseline.json --final reports/performance/sol_ultra_final.json --numerical reports/performance/sol_ultra_numerical_comparison.json --thread-scaling .sol_ultra_thread_scaling.json --decision-log reports/performance/sol_ultra_decision_log.md --output reports/performance/sol_ultra_comparison.md
```

The thread-scaling JSON is an input to the comparison renderer, not a committed
release deliverable.
