# P5 private native station-state and assembly integration

Parent `3d22d624a5907d1b09627f49be82b5463913a2c9`, tree
`841b53c8be0c39795adc57cb91c8c48f435bdf24`.

## Purpose and actual native routes

Move the preserved curved, coupled directed-hardening mechanics through the
real ANYsolver element interface, scalar nonlinear dispatch, reference global
nonlinear assembler and coordinated material/rotation transaction store.
This adds a private `Element` subclass, not a legacy B3 subclass, and not a
public selector or qualified formulation. The existing P3 public element and
accepted P3/P4/P5 evidence remain untouched.

The private formulation identity is
`CANDIDATE_GE_BEAM3_DC_CURVED_OBJECTIVE_LIFT_NATIVE_V1`; its station schema is
`GE_BEAM3_P5_PRIVATE_NATIVE_STATION_STATE_V1`. It evaluates the preserved
compensated local mixed kernel, with zero coordinate-low parts, using the
previously tested native chart pullback. No mechanics or numerical coefficient
changes. Each local solve retains its 25-update/64-evaluation ceiling and
1e-12 first-order force-accuracy estimate; this estimate is not a rigorous
bound or a replacement for the physical residual requirement.

Native interfaces exercised without modifying them:

- `Element` six-DOF mapping and model-owned reference node coordinates;
- `create_model_native_rotation_store`, with frozen model connectivity,
  reference directors and authoritative shared nodal matrices;
- `evaluate_nonlinear_element` rather than direct legacy mechanics;
- `_assemble_nonlinear_system`, including its real sparse assembly and
  exception cleanup, not a replacement test scatter routine;
- `NonlinearStateStore` staging, replacement, materialization, commit and
  discard, coupled to the same native rotation transaction.

The generalized section is explicitly registered under a private per-element
material name so the actual assembler returns that exact owned section. The
ordinary model's default steel material is not used as an implicit substitute.
Registration occurs only after successful private initialization.

## State safety

State binds exact keys, formulation/schema/model hash, epoch, total bookkeeping
displacements, physical positions, authoritative matrices, fixed prior origins,
new station histories, full local response and integrity hash. Hashes are
integrity checks, not authenticity or a complete load-history certificate.

Replay reconstructs the accepted local solve from the previous origins. It
never applies the accepted strain to the newly advanced plastic history to
pretend that is the same algorithmic state. Replayed local response, station
ordering/counts and histories must match. Initial state is explicitly virgin,
stress free, zero displacement and identity spatial operators. Missing state
is rejected; it is not synthesized during a nonlinear trial.

The mandatory private session owns the actual store. Generic dictionary
fallbacks do not know P5's history schema, so the session validates every
candidate and accepted-origin replay before invoking the native commit. It
rejects missing element candidates, altered staged/store copies, dirty geometry,
section or DOF ownership, stale trials and detached native views. Actual active
views are rechecked before and after mechanics. Each candidate uses the same
committed station origins; line-search replacement discards rejected histories.
All elements validate before any material or rotation commit. No child element
commits independently. Replay and discard leave accepted state unchanged.

This private session is mandatory: bypassing it and manually committing the
generic fallback store is not an authorized P5 path. A production-native
validator/transaction extension, independently reviewed with the existing
shell lifecycle unchanged, remains necessary before ordinary driver exposure.

## Focused verification

Tests exercise active plasticity, loading/unloading/reversal, zero-advance
accepted replay, line-search candidate replacement, two-element shared-node
state, actual sparse assembly equality to scalar scatter, post-plastic-commit
force/tangent directional agreement, missing native context, unsupported-route
rejection, returned-copy isolation, stale/detached views, DOF/section mutation,
re-sealed history/response/identity/pose mutations, and late-element/replay
failure atomicity. The real assembler cleans up both transactions on failure.

Initial focused run: 18 passed in 7.15 seconds. Expanded actual-assembly run:
20 passed in 7.99 seconds. Neither run had a failure. The final recorded
regression result below supersedes these development inventories; counts are
never added across runs.

Final checkpoint run: **101 passed in 11.25 seconds**, comprising 23 new
native-material tests and the 78-test chart/native-rotation/nonlinear-mixed/
compensated-mixed regression inventory. The added initialization-failure test
confirms that failed setup publishes neither a section registration nor an
element/session ownership link. Two earlier 100-test regression runs also
passed (11.26 and 11.30 seconds); these are not additional scientific records.

Executed with Python 3.13 `-B -m pytest -p no:cacheprovider`, `-q --tb=short`,
one thread in each of OMP/OpenBLAS/MKL/NumExpr, source PYTHONPATH for this
worktree plus ANYfileIO, and a fresh external temporary basetemp. Exact suite:

- `tests/test_ge_beam3_curved_p5_native_material_probe.py`
- `tests/test_ge_beam3_curved_p5_native_chart_probe.py`
- `tests/test_native_rotation_state.py`
- `tests/test_ge_beam3_curved_p5_nonlinear_mixed_probe.py`
- `tests/test_ge_beam3_curved_p5_compensated_mixed.py`

These are small correctness tests, not a performance or large-mesh wave. No
formal resource request was generated, consumed or retried. Existing tolerances
were retained: 1e-7 directional checks and normalized 1e-11 symmetry/equality
checks, with exact byte/digest comparisons for deterministic state replay.

## Remaining work and limits

This is same-author integration evidence, not an independent physics oracle,
scientific qualification aggregate, engineering benchmark, or production
activation. The private class fails closed for standard linear stiffness,
mass, geometric stiffness, out-of-transaction forces, fibre stresses and
serialization. It has no public alias and is not exported by ANYsolver.

Next priorities are native Newton/line-search acceptance and rejected-step
tests under the actual driver; a formulation-owned native validation hook
instead of the private commit boundary; production-compatible objective
section adapters; restart and recovery integration; then static, locking,
prestressed-modal/buckling, package and independent-review gates. The existing
finite-precision onset uncertainty remains unresolved and is not superseded
by these tests. Fine-mesh coordinate-low transport remains an interface gap.
The beam-shell connection remains separately unqualified.

No public API, package/default, B2/B3/Q4/S3 mechanics, source coefficients,
historical evidence or existing test was changed by this checkpoint. The
inherited branch does contain prior GE-B3 source additions; it is not accurate
to call the entire branch research-only. No push, merge, release or resource
request execution is part of this checkpoint.
