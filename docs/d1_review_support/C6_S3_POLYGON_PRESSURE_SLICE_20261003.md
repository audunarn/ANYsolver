# S3 polygon-pressure certification — 3 October 2026

Development implementation/source/installed checks; no independent engineering
acceptance or release. Parent `d7a257bc`. [Source/environment manifest](contact_c6_s3_polygon_20261003/source.json)
and [89 raw records](contact_c6_s3_polygon_20261003/raw.zip) preserve inputs,
commands, failed diagnostics, source snapshots, runtime settings, review and wheel.

## Implemented change

The original spatial-cell proof now updates exact rational nodal totals locally
and uses a largest-area heap with monotone insertion IDs. Bounds, tie order,
cancellation and finite-budget decisions match the previous list algorithm.

Explicit `normal_s3_polygon_pressure_bounds_dev=True`, with the normal-S3 owner,
selects `NORMAL_NODAL_S3_POLYGON_PRESSURE_NEWMARK_EVENT_DEV_V4` and checkpointV16.
Guaranteed/possible overlap polygons enclose the actual temporal overlap. Exact
inner P1 moments retain source-vertex temporal cancellation; signed uncertain-band
contributions enclose joint weighted-gap/support expressions. Unresolved bounds
refine in time within the original controls. All modes and physical reference
area remain. [Derivation and disposition](S3_PRESSURE_PATH_BOUND_DESIGN_20261003.md).

V4 changes only conservative pressure certification. The original strong complete-
path gap, polarity and hidden-material-point test at the original event tolerance
remain. Jet2 work/tangent, masses, Newmark equations, equilibrium/response targets
and physical commits are unchanged. V3 remains default; incompatible algorithms
fail restart explicitly. The proposed omitted-guard policy has **not** been adopted.

## Evidence and failures

49 passed scoped outcomes, not unique cases: partitionA19/B2, polygonA11,
profileA16 and legacyC1. PartitionA's two test defects assumed an inexhaustible
depth-limited queue and a cancellation callback count not reached by its fixture;
their corrected focused checks pass. One invalid-selector exit4 is retained;
the verified V15 active-restart selector subsequently passes. Effective CI records
confirm owned imports, JIT off, one Numba/BLAS thread and actual outcomes.

Independent polygon checks cover exact P1 moments, physical reference area,
six changing geometries at31poses each, tiny positive/absent support, hidden weak
phase, limits and cancellation. These numerical checks complement the enclosure
derivation; sampling alone is not a path certificate. V16 active split continuation,
changed algorithm/tolerance rejection and preserved hidden guard pass.

Saved original weak-path results:

| Candidate | Disposition |
|---|---|
| Original/incremental at128/512cells | Exact bounds/status/counter parity |
| Incremental at10000cells | Budget failure in12.17s |
| Polygon certificate, original controls | Resolves624queries/13panels in1.464s |

Component timings have differing instrumentation and statuses; no whole-route
speed ratio is inferred. C4's recorded helper snapshot is retained; later exact
mass batching/empty-band elimination is covered by the affected profile corpus.

The first hidden-path diagnostic reversed projection displacement and separation
sign. Its wrong output is retained. The corrected independent calculation finds
a real approximately65nm pulse below zero between open endpoints, so removing
the safeguard is a scientific policy change, not a bounds optimization.

Source/isolated installed V4 default example matches all fields and235 imported
hashes. Installed V3 matches previous fields and234 current source hashes. Wheel
SHA256 `4320e4456158a12166e070c1d7313c18a4f84bd4ff9115512001c71b6dbca8dd`.
Packaging observations overlapped the coupled run; no performance comparison.

## Coupled outcome and next decision

C5/V4 retains Nx8/16faces/21coordinates, KN2e10,100µm tilt, original target,
dt25µs/end3ms,20µm physical gap and all original response/momentum gates.
It times out900s (910.089s including cleanup), sampled peak180826112B.
Last time1.7977902818679808ms:870endpoint calls/90.937s;868strong paths/
642failures/655.090s;218weak proofs/zero failures/10.324s, maximum816queries/
17panels. No full trajectory or numerical acceptance. Startup/owner effective
settings and partial rejected-work counters are retained.

Pressure certification now resolves the encountered paths; hidden-approach
cutbacks dominate this fixture. Do not automatically repeat it or increase caps/
tolerances. A user decision is pending on a separate event-policy experiment that
would preserve the swept20µm limit and discrete pressure-phase checks while omitting
the tighter material-point safeguard. Until authorized, preserve that safeguard
and progress other required rows. C0–C9 remains incomplete; forecast unsupported.
