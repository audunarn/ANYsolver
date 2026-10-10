# Representative M4 diagnostic pilot

2026-10-08. M4 remains active and unchanged. This is a bounded diagnostic,
not a demonstrated representative-model speedup or a qualification campaign.

## Outcome and next decision

The complete barge did not reach a certified load case within the60second
profiled process limit. After stiffness and constraints, preparation continued
without completing load-map preparation. An isolated load-map diagnostic also
timed out; its stack samples located pressure probing followed by canonical
gravity/mass-matrix computation during unit-acceleration assembly.

The next bounded implementation candidate is **reuse of preparation work for
mass and acceleration**, retaining independent canonical full-load checks,
activity, structural/point/added masses, accumulation order and mutation guards.
Source confirms repeated mass-related operations; neither their total cost nor
prospective savings is established. No optimization is implemented by this pilot.

## Model and explicit output scope

Input is the saved complete ANYfem floating-barge project/mesh at
`C:/ANYworkspaceWork/static-batch-20261007/barge07.fixture.json`.
It contains4348nodes,3185Q4shells,1060beams,1248mesh couplings, four supports,
one connection and601load-case definitions. The diagnostic selected saved
`Seaway_000` and `Seaway_001`, retaining the actual inherited definitions.

A complete-geometry remesh requested2m instead of0.7m but produced exactly the
same counts. No mechanical members were removed; no further sizing sweep ran.
This observation does not establish why the effective discretization was unchanged.

All-native-field envelopes are unsuitable for an assumed small pilot: the existing
Q4 envelope schema has144scalar locations and144associated scalars per mode.
Associated float storage alone is497664bytes/Q4, approximately1.59GB for3185Q4s,
before identities, objects, other elements and simultaneous transaction copies.
This is a storage calculation, not measured full-barge peak memory.

The barge diagnostic therefore explicitly requested whole-model **von Mises and
reactions**, plus selected full histories on physical shell/beam elements, with
a1GiBmemory policy and64MiBserialized-output cap. It does not cover all-resultant
output qualification. Preflight was a conservative provisional estimate; actual
solver resource policy remained enabled. No whole-model envelope was delivered.

## Actual runs

All runs used the required ANYsolver venv, frozen M4 source, JIT enabled and
single-thread environment. The barge reported effective single-thread BLAS pools.
There were no product-source changes during any attempt.

| Attempt | Result | Process-wall seconds |
|---|---|---:|
| representative-build2 | Complete project remeshed; counts unchanged |15.326198000|
| representative-barge-m4 | Timeout before load preparation completed; zero certified cases |60.092775500|
| representative-free-control | Four certified cases, envelope complete |11.874619300|
| representative-loadmap-probe | Timeout during isolated load-map preparation |30.064737400|

Both timed-out process trees had no surviving PIDs. All partial output/stacks
were preserved. Total **117.358330200/120seconds**, leaving2.641669800unused.
The campaign is stopped. Previous benchmark ledgers were neither pooled nor reset.

Barge flushed stage-wall timestamps, relative to the diagnostic harness start:

- Built/selection: approximately3.93s; preparation began3.95s.
- Admission event:6.14s.
- Stiffness event:24.99s, approximately18.85s after admission.
- Constraints event:25.96s; no subsequent loads-complete event before timeout.
- Peak observed at a checkpoint: approximately522MiB. This is not a proven
  whole-process peak, because later preparation was terminated between checkpoints.

The constraints callback is followed by a source witness before entering
`compile_canonical_load_maps`; the uncompleted interval must not be attributed
entirely to that compiler from wall events alone.

## Narrowing the preparation work

The isolated diagnostic built the complete barge, applied boundary conditions,
and called the actual `compile_canonical_load_maps` with all four enabled load
families. It omitted stiffness assembly, so its cache state differs from the
full pilot. It is a mechanism diagnostic, not a replacement timing comparison.

Five-second traceback snapshots showed pressure probing first, then three
complete snapshots in mass-matrix/gravity assembly at `prepared_static_loads.py`
line867. The final snapshot was partial. These samples do not identify which
unit axis was running or establish percentages of execution time.

Source review independently confirms:

1. Two scalar pressure probes and, where supported, node-count-plus-one tuple
   pressure probes for each eligible element.
2. Three full canonical unit-acceleration assemblies.
3. Owned pressure recipe construction and pressure warmup.
4. Another per-element mass-matrix evaluation to retain prepared mass maps.
5. Native/prepared verification by enabled family, including acceleration.

Mass caching and guards affect the real cost. Any reuse proposal must preserve
the required independent verification; dropping tests/probes solely to obtain
speed is not an accepted repair. Pinned formulation sources remain unchanged.

## Free-free control and limits

The larger control uses eight disconnected balanced mixed shell/beam bodies,
48elements and64nodes, with pressure, nodal and acceleration combinations.
It is a scale/control case, not a free-floating barge qualification.

Stage-wall intervals under profiling were approximately4.19s from constraints
to loads complete and2.93s from loads complete to recovery preparation complete.
Four executed cases reported summed solver phases: loading0.377s, solve0.071s,
certification0.0028s, recovery/envelopes0.611s. The complete envelope retained
1310359estimated accumulator bytes. These are instrumented observations, not
unprofiled speed estimates or a10,000-case projection.

Two diagnostic limitations are retained explicitly:

- Dumping/restarting cProfile inside public progress callbacks interrupts parent
  frame accounting. Inclusive preparation-frame times in profile JSON must not
  be interpreted as contiguous preparation duration. Use stage-wall records.
- The control's exploratory JSON call used `skipkeys=True` on tuple-keyed leaves,
  suppressing those serialized values. It supplies **no output-serialization
  evidence** and is not a complete consumed-output benchmark. Its certified case
  and envelope status remain genuine. The executed harness is preserved as-is.

The production barge never reached application case loading, recovery or output;
those requested phase costs remain unmeasured. No accuracy/speed claim is made
from the incomplete production run. No additional broad tests or fixes ran.

## Evidence

Under `C:/ANYworkspaceWork/prepared-static-20261008/evidence`:

- `REPRESENTATIVE_M4_RESULTS.json`: ledger, exact commands and status.
- `checks/representative-*`: manifests, full logs and timeout cleanup records.
- `representative-barge-m4/stages.jsonl`, `latest.pstats`: flushed progress.
- `representative-loadmap-probe/stacks.log`: preserved sampled call stacks.
- `representative-free-control/profile.json` and run stdout: control evidence.
- `representative_m4_pilot.py`, `representative-m4-design.md`: worker harness.
- `representative-independent-review.md`: independent interpretation.

No product changes, commits, merges or pushes. M4 remains the selected candidate.
