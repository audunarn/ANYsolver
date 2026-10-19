# Opt-in prepared static evaluation (revised plan)

Revision 2026-10-08, after review of the previous draft. This is a proposal: it
authorizes no implementation or publication and makes no performance claim.

## 0. Changes from the previous draft

| Area | Previous draft | Revised |
| --- | --- | --- |
| Sequence | Pattern responses (slice 3) before ANYfem integration (slice 4) | ANYfem adapter and direct-route adjudication first; pattern responses only after a measured screen (D3) |
| Pattern outputs | Precomputed selected-response matrices, plus a full-state certificate | Outputs recovered from the certified state by the same prepared recovery as the direct route; no selected-response matrices |
| Certificate right-hand side | "The original reduced/augmented equations" | The reduction of the case's full load, computed exactly as in direct execution |
| Factor ownership | "Evaluator owns its handles" | Factor detached from the shared PARDISO pattern slot at preparation |
| Recovery compilation | "From canonical formulation calculations" | Canonical calls under one preparation lease; no edits to pinned sources; affinity certificate |
| Refusal | "Unqualified formulations fail preparation" | Refusal per requested output or load family, not per model |
| Acceptance | "Existing scientific tolerances" | Tolerances named and frozen before assessment (D2); bit identity expected only where arithmetic is unchanged |
| Benchmarks | Route-specific GO | Explicit comparators (R1 against the current route, R2 against R1), complete-workload definition, budget split |

## 1. Decision, evidence and scope

Adopt the central idea: **prepare an owned numerical model once, then evaluate
many static cases with prepared operators.**

### 1.1 Evidence (motivation, not a claim)

The eight-case barge holdout (26,094 DOFs; three selected nodes, three selected
elements, reactions and 40 envelope quantities; solver `b246a985`, application
equivalent to ANYfem `3e4eb7f`; one native/Numba thread; warm) spent:

| Phase | Seconds | Share |
| --- | ---: | ---: |
| Recovery (stresses and reactions) | 13.19 | 53% |
| Input and snapshot observation | 6.32 | 26% |
| Load assembly | 2.57 | 10% |
| Solve, reduction, reconstruction, certification | 0.20 | 0.8% |
| Total measured | 24.72 | |

Source: `C:/ANYworkspaceWork/static-batch-20261007/selection-slice/baseline-barge.json`.
The one-case profile in the same directory (`profile.txt`, instrumented, nested
cumulative times overlap) attributes the time to per-element qualified Q4 guards
(50,960 calls), `_model_state` (about 0.35 s per call, 16 calls), constraint
audits (about 0.19 s per call) and ANYfem structural freezing (about 0.13 s per
call). The cheaper-observation prototype was 10% slower and was rejected
([static batch evidence](../static_batch_performance.md)). Changing the
ownership contract targets the dominant cost. A pattern-response route can at
most remove the solve and load-evaluation share of the prepared direct route.

Expected outcome, stated as a hypothesis for section 5 rather than an
acceptance criterion: prepared direct execution brings warm per-case time on
the barge holdout to roughly the numerical floor (tens of milliseconds) plus
ANYfem load evaluation.

### 1.2 First-release scope

Committed:

- Prepared direct execution for arbitrary supported loads (`direct_prepared`).
- Prepared selected displacements, rotations, stress components/resultants,
  derived stress measures, reactions and envelopes.
- A snapshot-aware ANYfem adapter with prepared load operators for every
  supported static load family.
- Supported and free-free models, including disconnected bodies.
- Time histories: load values and coefficients may vary arbitrarily with time,
  including nonlinear functions, discontinuities and independent case values.
  Each sample receives its existing linear-static response. Time introduces no
  proportional-loading assumption and no structural dynamics; inertia enters
  only as declared acceleration loads. The route is valid for quasi-static
  loading.

Agreed scope, implemented only after the D3 screen passes:

- Exact pattern responses (`response_basis_exact`) for explicitly declared
  affine load families.

Deferred: recovery archives, automatic basis discovery, adjoint/influence
methods, approximation and new backends. Numerical rank detection does not
establish exact representation; SciPy's interpolative decomposition explicitly
takes an approximation rank or error target
([SciPy documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.linalg.interpolative.interp_decomp.html)).
These need a separate accuracy contract.

## 2. Ownership, interfaces and load coverage

### 2.1 Solver API

`prepare_static_evaluator(model, *, outputs, constraint_mode="auto",
allow_unbalanced_free_free=False, patterns=None, resource_config=None,
session=None)` returns a context-managed `PreparedStaticEvaluator`.
`iter_batches(cases, *, batch_size=32, cancellation_token=None,
progress_callback=None)` yields bounded array blocks: selected displacements
(DOFs by cases), component arrays per selected element, reaction arrays,
envelope-ready records and diagnostics.

Case records:

- `StaticCase(case_id, load, time=None)`: an arbitrary load, always evaluated by
  `direct_prepared`.
- `PatternCase(case_id, coefficients, time=None)`: accepted only by an evaluator
  prepared with `patterns`; coefficients refer to declared columns.
  Representability is declared by construction and never detected numerically.
  A case with any non-pattern contribution is a `StaticCase`.

Put the evaluator in a new module (for example `prepared_static.py`).
`static_batch.py`, `iter_linear_batches`, `solve_linear`, `solve_linear_many`
and their defaults remain unchanged.

### 2.2 Snapshot and ownership

- Preparation runs the existing admission, constraint audit, activity and
  consistency checks once, under the existing leases.
- The evaluator holds the session's existing plans by reference: stiffness,
  constraint `T`/`u0`/`K_red`, static operator, scaling, rigid modes and output
  plan. They are already read-only buffers (`_immutable_csr`,
  `_immutable_array`), so no copy is needed. Everything else it builds (load
  operators, recovery, reaction operator, mass-load columns) is owned and
  read-only.
- Snapshot identity is a UUID plus a SHA-256 content digest over owned arrays
  and source identities. Every block carries both.
- After preparation nothing observes the live model. Editing or deleting it
  cannot change results.
- **Factor residency.** At preparation, transfer the existing numerical factor
  from the shared PARDISO pattern slot into an evaluator-private solver. This is
  a transfer, not a refactorization. Later same-pattern factorizations or LRU
  slot eviction (four process-wide slots by default) then cannot make it stale.
  Release it on close or finalization. Factorization attempts and stale rebuilds
  stay counted; a rebuild during a measured run is reported as a defect.
- An internal session may be closed after preparation; a caller-supplied
  session remains caller-owned. Do not create a second factorization cache.
- Inputs are converted to owned finite numeric buffers before execution;
  internal writable storage is never exposed. No operation lease crosses a
  provider call, progress callback, iterator observation or yield.

### 2.3 Solver load operators

Each load family compiles at preparation to a fixed linear map from owned
per-case parameters to the global load vector. The map is built by evaluating
the canonical element kernels at unit amplitude under one guarded lease:

- Nodal forces and moments: scatter.
- Element load vectors: scatter with fixed activity scales.
- Dead pressure, scalar or three-value affine: a sparse map over the loaded
  element set. Follower-labelled pressure compiles through its existing
  linear-static kernel path, including the strict-flat S3 V2 refusal.
- Translational acceleration: three columns `M e_x`, `M e_y`, `M e_z` from the
  consistent element mass and assigned point masses. Per-case added node masses
  are per-case data.

Compile maps for the families declared at preparation; a case using an
undeclared family fails with a diagnostic. Columns exist for every element the
canonical assembly accepts for that family, so no capability is lost.

### 2.4 ANYfem adapter

`prepare_linear_static_evaluator(...)` freezes structural mappings, coordinate
systems, connection resolution, target resolution, wet-element sets and
centroids/normals, then prepares the solver evaluator. Per case it evaluates
load definitions into owned arrays over frozen index sets (for example, pressure
per wet element) rather than solver `LoadCase` dictionaries. It takes no
per-case project or mesh snapshots.

Covered families: point forces/moments and distributed scopes; shell pressures
and arbitrary element-pressure fields; wet pressures from expressions, mappings,
tables and trusted Python callbacks; line loads, surface tractions and
connection forces/moments; gravity and translational acceleration with
structural, assigned and added-mass semantics; combinations, coordinate
transformations, envelopes and follower-labelled semantics.

- **Load-definition semantics.** Geometry and targets are frozen. A case's load
  definition is observed once when the case is requested, copied, and resolved
  against the frozen geometry. A definition that cannot resolve there fails
  that case. Each case reports a load-definition digest.
- **Load-side superposition.** A load item with a fixed spatial distribution and
  a scalar envelope compiles to one fixed full-length vector `F_i`. A case load is
  `F = sum_i f_i(t) F_i + (per-case non-separable vectors)`. This is exact up to
  rounding and needs no new certificate. These columns are the pattern columns
  of section 3.5.
- Callbacks execute once per required evaluation outside numerical spans; their
  results are copied into owned finite buffers. Sampled callback values are
  never used to infer separability. Changing wetting and arbitrary spatial
  fields go through direct execution. Existing invalid inputs remain invalid.
- Geometry, stiffness, constraints, prescribed offsets, material state and
  activity are fixed per snapshot. Changing them requires a new evaluator.

### 2.5 Refusal

Preparation fails only if a requested output or a declared load family needs a
formulation without a prepared operator. Unselected elements, including
application elements such as spring connectors and beam-shell couplings,
contribute only through the assembled stiffness. `iter_linear_batches` remains
the route for refused requests (D4).

## 3. Numerical implementation

### 3.1 Prepared direct execution

Per block, the steps are:

1. Assemble `F` from the prepared load maps.
2. Reduce: `b = T^T (F - K u0)`, with `K u0` precomputed.
3. Solve the scaled or augmented block system with the owned factor.
4. Reconstruct selected and, where needed, full displacements.

Supported scaling, free-free augmentation, rigid modes and the imbalance policy
are unchanged.

### 3.2 Prepared recovery

$$
y_e = y_{e,0} + H_e u_e
$$

Add a `J_e l_e` term only for a formulation whose canonical recovery consumes
element loads. The current linear recovery, `compute_stresses(mesh, u_e,
material)`, takes no load argument.

- Obtain `y_{e,0}` and `H_e` by evaluating canonical recovery at preparation for
  the zero state and the local unit states, inside one guarded preparation
  lease. For large selections, batch the probes across elements that share no
  DOFs. Probing preserves element orientation, station/layer ordering, shell
  shear conventions, beam condensation, fixed offsets and constant initial-field
  terms by construction.
- Do not modify byte- or live-pinned sources (`elements.py`, `plasticity.py`,
  `vectorized_nonlinear.py`, `e4_pl_element.py`, `e4_pl_s3_element.py`).
  Existing non-pinned batch kernels (`RecoveryS4Batch`, the reference S3 batch)
  may be reused on owned data where they apply. Changing pinned sources needs
  the runtime-guard successor record and independent review; that is outside
  this plan.
- **Affinity certificate.** For each compiled family, check
  `y(a+b) - y(a) - y(b) + y(0)` and `y(s a) - s y(a) - (1-s) y(0)` on random local
  states against the frozen recovery tolerance (D2). On failure, refuse that
  output; nothing is silently linearized.
- Compile only linear components (stress tensors, resultants). Compute principal
  stresses, von Mises and signed envelope measures from superposed components
  with the canonical formula functions; do not re-implement them.
- Generalized sections expose only quantities their existing mechanics define.
- Include compile time and `H_e` storage (about outputs times local DOFs per
  element) in the preparation cost, memory estimate and break-even analysis.
- Provenance records the formulation, the compile route and the snapshot digest.
  Using preparation-time authority for qualified formulations is decision D1.

### 3.3 Prepared reactions

From one guarded constraint audit at preparation, build the row-restricted
`K_c` for fixed and MPC-slave DOFs, bucket index arrays and MPC coefficient
arrays. Per case:

- Compute `r_c = K_c u - F_c` from the case's full load.
- Map support reactions, MPC slave forces and master-equivalent forces through
  fixed sparse maps. Nullspace diagnostics are reported as now.
- Return arrays. Per-equation dictionaries are produced only on request.

Because the full load is used, cases with equal reduced right-hand sides but
different loads on constrained DOFs give their correct, different reactions.

### 3.4 Certification for every delivered case

- The relative backward error of the reduced or augmented system must not
  exceed `_LINEAR_STATIC_BACKWARD_ERROR_LIMIT` (1e-10); evaluate it blockwise.
- Free-free cases keep per-body compatibility on the case's reduced load, plus
  the multiplier, gauge-residual and imbalance-policy checks.
- Tests add independent physical checks: the compiled gravity resultant equals
  total mass times acceleration; a uniform pressure resultant equals `p A n` on
  flat panels; reaction resultants balance applied-load resultants in force and
  moment.
- No successful-looking substitute results are emitted.

### 3.5 Exact pattern responses (conditional on D3)

For a declared family with full-load columns `F_B` and offset load `F_0`:

$$
b = d_0 + B c,\qquad B = T^\top F_B,\qquad A w_0 = d_0,\qquad A X = B
$$

- Solve `A X = B` once as a block and certify every column.
- Per block: `q = w_0 + X C` (a dense multiply) and `F = F_0 + F_B C`.
- The certificate right-hand side is the reduction of the case's full load,
  computed as in direct execution, never `B c`. An inconsistent pattern
  declaration therefore fails the certificate instead of passing silently.
- Outputs, reactions and envelopes come from the certified `q` and `F` through
  sections 3.2 and 3.3. There are no selected-response matrices and no second
  rounding path for outputs.
- Free-free pattern columns may be unbalanced. Every physical combination must
  meet its requested policy. If a case's compatibility measure falls in a narrow
  band around the refusal threshold (fixed before assessment, for example 0.5-2x),
  the case is re-evaluated by direct execution. Accept/refuse decisions near the
  threshold therefore use the direct route's arithmetic.
- A failed certificate triggers a direct solve of that case. A failed direct
  solve terminates execution with case diagnostics.
- Added masses must be identical across a pattern family; otherwise those cases
  go direct.
- `X` takes `n_red x p` storage. If it exceeds the budget, use direct execution.

### 3.6 Resources

Blocks default to 32 cases, reduced by `ResourceConfig`. The resource account
includes:

- shared immutable plans, counted once;
- the factor, using PARDISO-reported memory where available and an estimate
  otherwise;
- load, recovery and reaction operators;
- the basis, when present;
- block workspace.

If one direct case cannot fit, refuse before execution.

## 4. Verification

Freeze before the first assessment:

- source identities, fixtures and output selections;
- effective runtime settings;
- the D2 tolerances for load vectors, recovery components and reactions.

Bit identity is expected only where arithmetic is unchanged, for example the
solve given an identical reduced load. Compiled load and recovery operators
change the arithmetic order. The oracles are the current `iter_linear_batches`
and canonical assembly and recovery.

| Slice | Required checks, in addition to existing suites for touched code |
| --- | --- |
| 1 Direct | Supported, free-free and disconnected models; weighted/eccentric MPCs; nonzero prescribed offsets. Empty input, uneven blocks, repeated labels, cancellation, provider errors, early close. Source mutation/deletion after preparation, caller aliases, wrong-snapshot inputs. Factor residency: a same-pattern factorization after preparation causes no rebuild. Refusal before execution when one case cannot fit. |
| 2 Recovery and reactions | Component agreement per qualified family (Q4, S3, beams including condensation and offsets, coupled beam-shell). Constant initial fields. Affinity certificate, including refusal of a deliberately non-affine test formulation. Derived measures from superposed components. Identical reduced RHS with different full loads/reactions. Reaction bucket separation. Physical resultant checks. Pinned-source hashes unchanged. |
| 3 ANYfem | Every load family through public ANYfem APIs. Mixed envelopes and nonlinear-in-time histories. Callback mutations. Per-case load-definition digests. Project edits during streaming do not affect results. |
| 4 Patterns (if D3 passes) | Exact, duplicate and nonrepresentable patterns. Severe coefficient cancellation. Private unbalanced columns, per-body imbalance and opt-in imbalance handling. Route agreement inside the threshold band. Detection of an inconsistent pattern declaration. |
| All | Component, derived-stress and envelope comparisons, including exact ties and near-tie governing cases. |

A small residual alone does not replace physical-output checks.

Before slice 2 merges, obtain an independent review of the ownership/authority
argument and the compile route, preferably from a different model family, per
the repository review workflow.

## 5. Performance adjudication

- **Cap.** Benchmark execution is capped at 600 cumulative process-wall seconds,
  separate from required correctness tests. Warm-ups, profiling, failed attempts
  and both routes count against it; record consumption across continuations.
  Planned split: at most 120 s for pilots and profiles, at most 330 s for paired
  comparisons, at least 100 s for a distinct holdout and at least 50 s in
  reserve. One current-route barge run takes about 43 s of driver time for eight
  cases, so keep current-route barge histories short and let the cheaper
  prepared route carry the longer histories.
- **Comparators.** R1 compares `direct_prepared` with the current exact stream
  (solver main, product code `b246a985`; ANYfem `3e4eb7f`). R2 compares the
  pattern route with R1 on identical cases, outputs and settings.
- **Complete workload.** From the built `FEModel` or ANYfem `BuiltModel` to
  consumed outputs, including session, factorization and evaluator preparation,
  excluding meshing. Report JIT-warm and cold runs separately.
- **Workloads.**
  - The barge selected stress/reaction/envelope holdout.
  - A reusable pressure/acceleration pattern history.
  - An independent-field history, run through direct execution.
  - Free-free and disconnected controls.
  - Optional, if budget remains: whole-model shell-envelope preparation cost.
- **Report.**
  - Preparation time and warm per-case marginal time.
  - Break-even case count.
  - Complete time at the measured case count, and modelled at 100 and 600 cases
    (labelled as modelled).
  - Factorization attempts and rebuilds.
  - Peak working set and retained bytes by category.
- **D3 screen, before implementing section 3.5.**
  1. On the pattern history under R1, compute `f` = (load evaluation + solve) /
     warm per-case time.
  2. The pattern route can remove at most that share, so its warm speedup is at
     most `1 / (1 - f)`. This is a necessary condition, not a sufficient one.
  3. Implement section 3.5 only if `f >= 0.5`, which the 2x target requires,
     unless the owner sets another threshold.
- **GO criteria per route.** A confirming holdout must show either 2x
  complete-workload speed, or 50% lower peak memory with at most 5% slowdown, at
  unchanged output scope and accuracy. Report `GO`, `NO_GO` or `INCONCLUSIVE`.
  Do not extend the campaign automatically to obtain a favorable result.
- **Informational only.** A multi-thread solver run, and a comparison with
  ANYfem's approximate compression on the seaway history (an ANYfem decision).
- Coordinate with concurrent heavy work when timing requires it, and record any
  interference.

## 6. Delivery order

1. Snapshot ownership and prepared direct execution (solver, new module).
2. Prepared selected recovery and reactions (solver). Needs D1 and D2, plus the
   independent review before merge.
3. The ANYfem prepared adapter with load operators, examples and R1
   adjudication.
4. The D3 screen, then either exact pattern responses with R2 adjudication or a
   recorded deferral.

The public examples show arbitrary time histories, independent load fields,
supported and free-free cases, resource limits and incomplete-run handling.
They show pattern coefficients if slice 4 lands.

Working trees: ANYfem currently has unrelated uncommitted UI edits. Do the
adapter slice in a separate worktree, or touch only `src/anyfem/solve/` and new
files. ANYsolver has unrelated local changes as well. Keep all unrelated dirty
work intact.

## 7. Reserved decisions

- **D1 Authority.** For qualified formulations, establish qualification
  authority at preparation. Operators compiled under the full guards are then
  applied to owned read-only data without per-use element guards. This moves
  where authority is checked, so adopt it explicitly before slice 2 merges.
- **D2 Tolerances.** Name and freeze the tolerances for load vectors, recovery
  components and reactions wherever arithmetic changes. Use existing tolerances
  where they apply; define any missing one prospectively, with its rationale.
- **D3 Pattern route.** Implement it only if the screen in section 5 passes.
- **D4 Refusal policy.** Refuse per requested output or family, with
  `iter_linear_batches` as the alternative (recommended), or add a slower
  canonical fallback inside the evaluator.

## 8. Completion

- Record actual tests, failures, timings, memory, capability limits and baseline
  identities in the living task note.
- Rejected performance candidates keep their evidence and do not enter the
  default route.
- Deferred items remain separate future decisions.
