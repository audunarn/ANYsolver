# F03 local classical reference: proposed scientific protocol v1

**Draft for independent review — 23 September 2026. No scientific execution
authority.** This protocol follows the completed bounded operator, numerical,
recovery and saved-composition proofs. It does not select a production
multiplier space, qualify native shell/beam mechanics, close F03 or G0B, or
permit G1.

## 1. Purpose and immutable mechanics

The proposed run asks one bounded question: does the independently implemented
classical finite-pad reference produce numerically certified and mutually
settling physical outputs over a manageable nested Q1/Q2 inventory?

Keep the represented constants and geometry from
`_b3_e4_f03_spatial_contract.py` exactly. In particular, preserve the
binary64-prepared `J`, `gamma=J_geom/J`, `Omega`, physical load, pad geometry,
three root pose constraints, free root slope, signed reaction convention,
actual and nominal load integrals, and both raw physical and represented
adjoint moment identities. No penalty, diagonal shift, matrix averaging,
pseudoinverse, repaired state, changed scale, changed tolerance or retry is
allowed.

The scientific route uses the existing local classical operator only. It is
not an E4-PL, B3-GE or B2 element execution and cannot by itself qualify their
coupling.

## 2. Exact case inventory

Start from the exact represented cut tuples `X_CUTS` and `Y_CUTS`. Refinement
level `L+1` inserts the exact Fraction midpoint of every level-L interval.
All grids are conforming, axis aligned and retain every original pad edge.

| Case | p | x by y cells | Physical DOFs | KKT order | Station intervals | Max active trace DOFs | KKT nnz envelope |
|---|---:|---:|---:|---:|---:|---:|---:|
| `Q1_L0` | 1 | 9 by 5 | 96 | 99 | 9 | 40 | 3,792 |
| `Q1_L1` | 1 | 18 by 10 | 374 | 377 | 23 | 96 | 25,268 |
| `Q1_L2` | 1 | 36 by 20 | 1,470 | 1,473 | 47 | 240 | 201,092 |
| `Q2_L0` | 2 | 9 by 5 | 374 | 377 | 9 | 108 | 29,388 |
| `Q2_L1` | 2 | 18 by 10 | 1,470 | 1,473 | 23 | 280 | 234,772 |

These figures came from deterministic topology-only preflight at source
`15202ab8`; no matrix assembly, factorization or equilibrium solve was used to
obtain them. The registration must recompute and bit-bind them before launching
any child.

Required exact prolongations are:

- `Q1_L0 -> Q1_L1 -> Q1_L2`.
- `Q1_L0 -> Q2_L0 -> Q2_L1`.

The equal-order pairs `Q1_L1/Q2_L0` and `Q1_L2/Q2_L1` have equal global node
locations but different piecewise spaces. They receive physical-output
comparisons only; no false inclusion or Ritz identity is claimed between them.

This is a bounded screen. Q2 has only one h-refinement transition, so even a
pass is not a continuum qualification. Any later Q2_L2 or Q3 execution needs a
new resource design, review and registration.

## 3. Assembly and integration

For each case, assemble two descriptions from the same grid:

1. Primary: exact shell helper, beam order `p+3`, load order 48.
2. Alternate: exact shell helper, beam order `p+4`, load order 64.

Use the primary diagonal scales for both descriptions. Separately compare
shell, beam, root and load blocks. Preserve the erratum in
`B3_GE_E4_PL_G0_F03_SPARSE_INTEGRATION_ERRATUM.md`: the original integration
sensitivity and the full saved-state alternate error both have limit `1e-6`,
and the latter includes the primary residual term. Relative shell/beam/root
block limits remain `1e-11`. Undefined bounds fail the numerical screen.

Every positive exact station interval is retained, including intervals whose
binary64 endpoints coincide. Local-coordinate evaluation and active-weight
normality checks remain mandatory. No interval snapping, omission or higher
quadrature retry is allowed.

The shared assembly cap for all five cases is:

```text
max_trace_dofs = 280
max_triplets = 1,045,600
max_trace_integer_bits = 8,000,000
max_assembly_work_bytes = 268,435,456
```

The largest deterministic triplet envelopes are 1,045,600 for `Q1_L2` and
852,000 for `Q2_L1`. Exceeding any cap terminates that registered case.

## 4. Selected numerical certificate

Select candidate A, the complete inverse-column residual certificate, for
this bounded inventory. It is already implemented, connected and reviewed on
synthetic matrices. Candidate B remains unimplemented and is not an authorized
fallback.

For each case:

1. Prepare the primary scaled KKT system once.
2. Produce and independently verify one sparse primal positivity candidate on
   the unmodified scaled primal stiffness.
3. Perform exactly one general SuperLU KKT factorization and one physical RHS
   solve using the frozen `COLAMD`, pivot-threshold 1, no equilibration and no
   iterative refinement route.
4. Stream every inverse column from that same factor in blocks of at most four,
   save every binary64 column once, and independently verify `I-HY` including
   zero-target rows.
5. Require `condition_2_upper <= 1e10` and primary relative backward error
   `<=1e-8`.
6. Reuse the saved inverse columns for alternate-integration verification. No
   factor or solve is available to the saved-only adjudicator.

The complete inverse evidence is 8*N*N bytes per case. The largest registered
case requires 17,357,832 raw bytes; the complete five-case inventory requires
less than 36 MiB before headers and hashes.

Frozen shared sparse/solve caps are:

```text
max_order = 1,473
max_nnz = 234,772
max_block_columns = 4
max_sparse_work_bytes = 67,108,864
max_KKT_factor_nnz = 2,171,202
max_inverse_evidence_bytes_per_case = 17,357,832
```

The primal positivity producer may retain at most 2,162,370 L/U entries and
67,108,864 bytes of canonical factor arrays. The exact verifier caps product
paths at 50,000,000, residual entries at 300,000, individual Fractions at
16,384 bits, cumulative rational bits at 100,000,000, and its declared
Python workspace at 4,294,967,296 bytes. A preflight or observed cap failure is
`FAILED_EXECUTION`; a completed but unresolved/failed positivity or condition
certificate is `FAILED_NUMERICAL_SCREEN`. Neither authorizes another method.

The exact numerical runner must test all budget inequalities before the
corresponding allocation or loop. Native factorization remains externally
supervised because internal caps cannot bound opaque peak workspace.

## 5. Port, state and recovery admission

For every case, archive and independently recheck:

- Exact root rank three and augmented root-plus-free-slope rank four.
- Complete 27-port trace inventory at root, tip and fixed station sides/orders.
- Scaling/state/action identity, primary stationarity, root compatibility and
  energy identity at their existing limits.
- Separate shell and beam integration comparisons.
- Complete saved interface, support/work and 48/64 signed-norm observations.
- The composed one-snapshot result with exactly three deterministic recovery
  calls, two norm observations, zero new equilibrium solves and zero new
  factorizations.
- Actual and nominal load resultants/moments, raw physical force/moment balance,
  represented adjoint identity, origin consistency, endpoint atoms and all
  eight total and line-only bands.

Saved observation production and saved verification must be separate phases.
The producer writes owned arrays and exact schemas once; the adjudicator loads
only those arrays and may not import a factorization or solve route. A digest
binds evidence but does not establish physics.

## 6. Physical settling screen

Retain the 45 signed scalar observables used by the earlier reference:

- Three root reactions.
- Three left and three right shell-edge wrench components.
- Three scaled tip-pose components.
- Shell, beam and total stored energy.
- Three root and three tip atom components.
- Three components for each of eight total fixed-band wrenches.

For a transition `c -> f`, use

`abs(x_f-x_c)/max(abs(x_f),abs(x_c),1e-3*S)`,

with the existing force, moment, pose and energy scales. Require at most 1% for
both transitions in each nested chain and require the last absolute change not
to exceed the preceding change plus `1e-5*S`.

For each nested transition, independently verify prolongation, nonnegative
energy distance, nondecreasing Ritz energy within `1e-10*E0`, and the nested
energy identity defect at most `1e-10`. The complete signed-functional
difference uses the saved 48/64 norm route; require resolution at most `1e-10`,
relative difference at most 1% for both transitions in each chain, and the
last absolute norm difference not to exceed the preceding difference plus
10 N.

Also compare `Q1_L2` with `Q2_L1`. Require all 45 signed scalar differences at
most 1% under the same floors and the full-functional relative difference at
most 1%. This cross-family check is not a nesting identity or convergence
order estimate.

`PASSED_BOUNDED_LOCAL_REFERENCE_SCREEN` requires every numerical, mechanical,
saved, nested-chain and cross-family predicate above. A pass remains bounded
internal reference evidence and does not select a production line space.

## 7. Process and archive resources

Run cases serially with all of these set to one:

`OMP_NUM_THREADS`, `OPENBLAS_NUM_THREADS`, `MKL_NUM_THREADS`,
`NUMEXPR_NUM_THREADS`, `VECLIB_MAXIMUM_THREADS`.

Each child has a 1,800 s wall-time cap and 6 GiB sampled process-tree RSS cap.
The serial launcher stops starting new children after 7,200 s. A child already
started may finish within its own cap. The complete raw archive cap is 512 MiB.
The supervisor samples the owned process tree, preserves peak RSS, terminates
only owned processes on limit/cancellation, and writes an exclusive terminal
receipt. Factorization cancellation is cooperative only after the native call
returns unless the supervisor terminates the child process.

The registration binds source commit, accepted-main identity, runner and
adjudicator hashes, exact cases, package/runtime locations, dependency
versions, thread caps, hardware, resource limits and every tolerance. Each
child writes an exclusive start marker before construction. A started case is
consumed whether it passes, fails, times out or is cancelled. No replacement
case or retry is implied.

## 8. Terminal decisions

Apply this precedence:

1. `FAILED_EVIDENCE` for source, identity, schema, ownership, missing receipt,
   archive or independent-replay defects.
2. `FAILED_EXECUTION` for process, resource, backend, factorization,
   programming or incomplete-case failure.
3. `FAILED_NUMERICAL_SCREEN` for a completed case with any condition,
   positivity, integration, trace/rank, equilibrium, recovery, work, norm or
   physical-balance predicate failure.
4. `UNRESOLVED_LOCAL_REFERENCE` when every case is numerically valid but the
   settling/cross-family screen does not pass.
5. `PASSED_BOUNDED_LOCAL_REFERENCE_SCREEN` only when every registered predicate
   passes.

Preserve every failed and aborted output. Independent postexecution code and
mechanics review must recompute the summaries from saved evidence without
assembling or solving. The terminal result cannot close G0B, enter G1, support
a release, or replace the mandatory external comparisons.

## 9. Work required before registration

This draft does not authorize the run. Before registration:

1. Implement an exclusively-writing case producer, process-tree supervisor,
   saved observation schema and solve-free adjudicator.
2. Add bounded synthetic lifecycle tests for start/terminal receipts, timeout,
   RSS termination, partial evidence, single-use inverse streams, stale
   identities, archive caps and replay without factor/solve access.
3. Demonstrate all declared preflights before their corresponding allocation.
4. Independently review the runner, resource feasibility, mechanics,
   observation independence, status precedence and exact source hashes.
5. Commit a clean source, create one immutable registration and only then run
   its single authorized command.
