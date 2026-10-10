# Prepared Q4 invariant-stage prototype

Implemented in the isolated opt-in candidate. The initial implementation was
delivered without timing evidence. The subsequently authorised benchmark below
demonstrates a smaller gain, but **does not meet the2x/50%-memory promotion gate**.
No merge or publication was performed.

Native planar Q4 recovery rebuilds fixed geometry/Jacobians, constitutive data,
the35-field stationary solution and station maps for each physical case. The new
`prepared_static_q4.py` computes these invariant stages during preparation and
stores owned, bytes-backed arrays with their canonical C/F layouts.

Each case still follows the native arithmetic sequence: global/local transform,
stationary parameters and residual, compatible/independent/resultant station
fields, director maps, physical stresses and derived measures. The route does
not flatten these stages or replace per-case GEMV with a differently associated
multiple-RHS product. It serves both selected histories and whole-model envelopes.

Eligibility is deliberately narrow: exact qualified Q4, planar geometry,
homogeneous isotropic material, no generalized section, Hill model or explicit
initial-field inputs. Other admitted features/formulations keep native recovery
with a diagnostic fallback reason. Load-family support and public interfaces are
unchanged. Snapshot memory/digest accounting includes staged data. Existing
authority scopes additionally verify the new kernel's executable facts before
owned-buffer dispatch and after numerical execution; transaction and lifecycle
rules remain intact. Pinned formulation sources and global factor ownership are
unchanged.

Completed verification records:

| Evidence run | Result |
|---|---|
| m3-solver-01 |1passed: preserved governing-case counterexamples |
| m3-solver-02 |7passed: exact staged/native parity, immutable buffers, removed local solve, authority and fallback |
| m3-solver-04 |15passed: block1/8/32 activation, eligibility controls and9ANYfem integration cases |
| m3-root-independent |1passed:33distinct cases, repeated labels,1/8/32blocks and restarts |

The independent check compares binary64 displacement/stress values and envelope
values, governing identities/times/indices and all associated fields against the
native stream. All match exactly. Focused geometry checks include rotated/skewed
planar elements, opposite directors, multiple amplitudes and rigid offsets.
The isolated arithmetic test confirms no dispatch to the native stationary solve
after preparation; public integration independently confirms route activation.
This is operation-removal evidence, not an end-to-end speed measurement.

`m3-solver-03` hit its40-second process limit after73pass dots with no printed
failure. It produced no completed JUnit summary and remains an incomplete broad
run; the subsequent targeted run covers unfinished activation/application paths.
All timeout/partial evidence is retained. The initial-field/generalized/material
controls verify eligibility predicates, not new qualification of excluded physics.
Independent source review found no concrete defect and confirmed final hashes.

Exact commands, durations, hashes, JUnit and full output are under
`C:/ANYworkspaceWork/prepared-static-20261008/evidence/checks/m3-*`.
The independent review is at
`C:/ANYworkspaceWork/prepared-static-20261008/fem/.prepared-static-evidence/prepared-m3-independent-review.md`.
The living task note records allocation accounting and the previous failed evidence.

At prototype handoff the benchmark ledger was524.545961906/600seconds consumed,
75.454038094unused. The next section records the user-authorised use of that
remaining allowance. No production barge memory result or10,000-case qualification
has been established.

## Authorised benchmark follow-up

Frozen product source and unchanged driver; eight serial alternating baseline/
candidate processes. Primary64 and distinct256-case holdout, cold and reused owner,
identical whole-model stress/reaction envelopes and selected histories. These are
small mixed shell/beam fixtures (6elements,8nodes), not the production barge.
Built-model-to-consumed-output timing includes preparation, factorization, loads,
certification, recovery, envelope reduction and output; meshing is excluded.

| Family / cases | Stream cold s | Prepared cold s | Stream reused s | Prepared reused s |
|---|---:|---:|---:|---:|
| Free /64 |1.6468|2.0774|1.4971|1.0539|
| Supported /64 |1.7495|1.8850|1.4238|1.0064|
| Free /256 holdout |5.5148|3.9479|5.3161|3.1960|
| Supported /256 holdout |5.4439|4.0052|5.2354|3.2454|

Holdout speedups including preparation: **1.397x free-free,1.359x supported**.
With a reused evaluator: **1.663x and1.613x**. Preparation (about0.81–0.84s on the
holdout) dominates shorter candidate runs. Stream constructor time alone is not
equivalent preparation: its first block performs the deferred factorization.
The gain is demonstrated on these fixtures; a repeated statistical campaign was
not run, and2x has not been demonstrated.

All1,808,960 compared binary64 values match exactly, with zero strict diagnostic
failures and zero governing-identity differences, including associated components.
Source hashes match across all eight processes; no source changes during runs.
Effective JIT was enabled, NumPy/SciPy/OpenMP/Numba threads1, and each owner performed
one SciPy factorization across cold/reused histories with no stale rebuilds.

Holdout isolated peak process memory: free186.79MiB stream/191.11MiB prepared;
supported186.72/191.48MiB. These include imports/model build. Candidate retained
accumulators were4,230,474–4,231,020bytes free and4,230,552–4,231,722bytes supported
over64/256cases, with fixed array dimensions and minor governing-label variation.
History sink retains0cases; file output storage is accounted separately. There is
no50%memory reduction and no measured10,000-case boundedness claim.

A descriptive affine fit to the two lengths gives marginal costs of19.89ms/case
stream versus11.16ms prepared free-free, and19.85ms versus11.66ms supported.
Including fixed output/first-use costs yields illustrative10,000-case projections
of199.3s versus112.7s free and198.9s versus117.6s supported. **The holdout also enters
this fit: it is not an independent projection validation, a measured10,000-case
result, or a barge prediction.** The raw phase/unattributed times remain in the
machine-readable record; no overhead was dropped from measured totals.

Decision: retain the smaller measured gain as evidence, **NO_GO for the specified
performance promotion gate**. Barge remains INCONCLUSIVE from the prior preserved
timeouts and was not rerun. No tuning, additional campaign or merge follows.

This follow-up consumed66.425949300process-wall seconds. Cumulative benchmark
use is **590.971911206/600s**, leaving **9.028088794s** unused; campaign stopped.
Results/runtime/source manifests: `../evidence/M3_BENCHMARK_RESULTS.json` and
`../evidence/checks/m3-*-64|256*/run.json` (relative to solver root; actual run names
are m3-free-stream64, m3-free-prepared64, m3-supported-prepared64,
m3-supported-stream64 and matching256-holdout names). Exact reproduction commands
are in each manifest. No approval or execution allowance is renewed by these commands.
