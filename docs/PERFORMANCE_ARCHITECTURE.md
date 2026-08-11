# Performance architecture

This document describes ownership and invalidation boundaries for the promoted
Sol Ultra paths. Numerical formulations and public analysis behavior remain in
the ordinary solver modules; performance modules may retain only data whose
lifetime and fallback are explicit. See `NONLINEAR_PERFORMANCE.md` for
eligibility details and operational diagnostics.

## Design contract

Every promoted path follows four rules:

1. the existing scalar or full-coordinate implementation remains the oracle;
2. eligibility is checked before retained optimized data is used;
3. a revision key or solver lifecycle bounds every mutable object; and
4. diagnostics identify activation, fallback, retained memory, and work counts.

Optimization is not allowed to change convergence criteria, constitutive
commit order, public contact records, recovered components, or constraint
semantics. A failed optional setup returns to the oracle unless continuing
could conceal stale state; wrong-model and closed-session use therefore raise.

## Ownership map

| Layer | Owner | Retained data | End of lifetime |
| --- | --- | --- | --- |
| JIT | Process | Compiled kernels and bounded execution diagnostics. | Process exit or explicit diagnostic reset. |
| Model assembly | Weak model association | Nonlinear element groups, reference arrays, CSR and reduced scatter maps. | Relevant model revision, explicit cache clear, or model collection. |
| Mesh reference | Mesh | Corotational reference data, contact geometry, large-selection recovery plan. | Relevant mesh/model revision or explicit recovery clear. |
| Nonlinear state | One static or arc-length solve | Contiguous committed/trial shell history and owned dictionary fallbacks. | Final materialization/solve completion. |
| Analysis session | Caller | Bounded structural/constraint/output plans and factorization handles for one model. | Revision invalidation, bounded eviction, or `close()`/`release()`. |
| Impact solve | One transient impact call | Tangent handle, contact work arrays, reduced assembly controller, and damage K/M plan. | Policy invalidation or solve completion. |
| Result | Caller | Public histories, states, contact records, recovery values, and diagnostics. | Caller-controlled. |

The important separation is that model/mesh caches contain immutable reference
or sparsity information, while committed material state and impact work arrays
remain solver-local. Reusing a topology plan cannot commit or resurrect a
rejected constitutive candidate.

## Nonlinear assembly and state flow

The weakly model-associated `NonlinearAssemblyPlan` groups compatible elements
and owns local response buffers plus full/reduced CSR scatter maps. Its key
includes model revisions and shell layer count. Static and arc-length solvers
may then create a `NonlinearStateStore` for qualified plastic shell groups:

```text
accepted state
    -> begin generation-checked trial
    -> evaluate local response into inactive arrays
    -> scatter force/tangent into retained CSR values
    -> accept: swap/commit buffers
       reject/retry: discard inactive candidate
    -> materialize owned public dictionaries only at an explicit boundary
```

Unbatched elements and incompatible state dictionaries live in an owned
fallback map. Immutable initial stress/prestrain and provenance fields are
sidecars; attempts to mutate them are rejected. A token from another store,
another generation, or an already completed transaction is an error.

For constrained models, direct reduced assembly retains either a selector map
or a weighted-MPC expansion and scatters directly into `T.T @ F` and
`T.T @ K @ T`. Memory and estimated-work gates run before activation. Static,
arc-length, and the qualified nonlinear-impact scope consume the same reduced
plan contract; ineligible calls assemble full coordinates and project.

## Constitutive and shell kernels

Elastic S4 batches cover isotropic, homogeneous orthotropic, and
pre-integrated generalized sections. The generalized layout preserves the
distinct membrane/bending coupling blocks, shear terms, areal inertia, and
resultant state required by the scalar element. Triangles, Q8/Q8R, unsupported
sections, and exact initialized-state overrides remain scalar.

Hill-48 batches flatten compatible shell material points and pack each
canonical ANYmaterial hardening curve into immutable arrays shared by the
points in that constitutive call. Custom curve protocols or
pathological rows return to the safeguarded scalar/numerical-oracle behavior.
Execution counters distinguish compiled points, scalar points, and row reasons.

Corotational response owns only reference geometry and metadata on the mesh.
The ordinary rotated path transforms forces and tangents with 3x3 node blocks.
The consistent-tangent path retains its dense chain-rule construction because
frame sensitivities are part of that formulation and serve as its oracle.

## Analysis session flow

`AnalysisSession` is optional and belongs to exactly one live model. It weakly
references the model and protects internal cache operations with a lock. Load
values do not enter structural keys, allowing repeated load cases to reuse K,
T, Kred, and a compatible direct factorization.

Invalidation is dependency-ordered:

```text
topology/geometry/material change
    -> rebuild K
    -> clear dependent reduced plans and factorizations

mass change
    -> rebuild M and Mred

constraint structure change
    -> rebuild T/u0/Kred, output rows, rigid modes, and factorizations

prescribed-value-only change
    -> refresh u0 while retaining unchanged T/Kred/factorization
```

Canonical constraint equation fingerprints supplement revision counters so
direct edits cannot silently reuse stale data. Selected-output plans and
factorizations use bounded entry counts. Context-manager exit calls `close()`;
a closed session and a session passed to a different model fail immediately.

Linear transient integration stores base/patch load vectors in reduced
coordinates. Selected history mode retains only requested rows of T/u0 and
avoids full-vector reconstruction unless full/envelope output or stress
recovery needs it.

## Impact flow

The nonlinear impact loop separates four independent optimizations:

- `ImpactTangentReuseController` decides when a solve-local effective tangent
  handle may be reused. Its zero budget is full Newton, and all state/contact/
  convergence/time-step invalidations are counted.
- `ContactWorkBuffer` owns compact candidate/active arrays and scatters directly
  to the full load vector. Public records are lazy at saved/result boundaries.
- `ImpactReducedAssemblyController` owns eligibility and a retained reduced
  scatter plan. It is qualified for elastic material response; material
  hardening/Hill history, beam-fiber plasticity, damage, affine constraints,
  unsupported kinematics, cost, memory, or JIT conditions keep full-coordinate
  assembly.
- `DamageMatrixPlan` owns a fixed CSR pattern plus per-element value positions.
  It is constructed only after projected future events pass the measured
  break-even and the combined retained footprint fits the solve's bounded
  memory allowance. That footprint includes both the plan and the cached
  legacy element-term arrays kept simultaneously for exact fallback.
  It applies only changed scales, keeps point masses independent, and returns
  to an exact cached-term rebuild if its model revision or input validity
  changes.

These controllers do not own public histories or relax the accepted-state
boundary. Contact selection remains deterministic, and damage/deletion changes
force tangent refresh.

## Recovery flow

Selections below the measured plan threshold use legacy scalar recovery
directly. Large requests build a revision-aware plan, group elements by
formulation, run eligible isotropic S4/S4R items through the compiled kernel,
and preserve unsupported items in deterministic scalar chunks. The execution
report records both sides of a mixed run rather than labelling the whole request
as accelerated.

## Thread nesting

`ResourceConfig` exposes three independent controls:

- `solver_threads` scopes native BLAS/OpenMP work;
- `assembly_threads` scopes Numba assembly; when greater than one, nested native
  pools are limited to one thread; and
- `recovery_threads` scopes compiled recovery or coarse scalar chunks; a scalar
  thread pool also limits nested native pools to one.

Omitted values preserve backend defaults. No policy infers a default from
logical-core count. Every scope restores the prior Numba/native setting on
normal return and exception. Public contact helper buffers are thread-local;
caller-owned sessions should still be scoped deliberately around related work
rather than treated as process-global state.

## Diagnostics boundary

Each layer reports actual work: plan builds/hits, setup time, retained bytes,
eligible and fallback elements/reasons, state commit/discard/materialization,
full versus direct-reduced assembly, tangent and factorization reuse, contact
record materialization, changed damage terms, selected-output reconstruction,
recovery backend, and requested/observed thread policy. These fields are the
source for the Sol Ultra comparison and decision reports; wall time alone is
not activation evidence.

Static and arc-length results also carry a task/thread-local
`nonlinear_performance` payload. Execution hooks record into a `ContextVar`
scope, so concurrent analyses are not inferred by subtracting process-global
counters. Nested preload work is explicitly counted, source-plan cumulative
timings are labeled, and fast block rotation is distinguished from the dense
consistent-corotational oracle.
