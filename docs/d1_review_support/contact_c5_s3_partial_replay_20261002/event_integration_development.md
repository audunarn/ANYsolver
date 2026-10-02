# Partial S3 friction: event-resolved replay candidate

2 October 2026. Development only; no C5 acceptance or application admission.

## Reason for the change

The coupled opening path contains a genuine interval of contact with inactive
endpoints. A retained material point enters at path fraction 0.15682001897 and
opens at 0.17309344047. A later material query can expose this interval in an
already committed pose segment. Current-step cutback cannot reconstruct its
missing friction work. The previous endpoint-only candidate correctly rejects
such a query; its failed evidence remains applicable to that candidate.

## Discrete constitutive contract

Explicit `event_subdivisions > 0` selects
`material_event_partition_actual_pressure_midpoint_return_v2`. Zero retains the
endpoint-only development rule. Both remain separate from scientific admission.

For each material point and each immutable affine pose segment:

1. Intersect the polynomial convex-boundary inequalities and separation-positive
   normal gap to identify all positive-length active intervals.
2. Divide each interval into the declared number of equal parts and visit their
   midpoints in time order. Visit inactive intervals to release traction, then
   evaluate the actual endpoint.
3. Evaluate the unchanged shared mortar normal law on every stage pose. Endpoint
   pressure interpolation is not used. Stage poses are disposable constitutive
   evaluations, not additional accepted structural equilibria.
4. Apply the existing material-anchor Coulomb return at these stages. Sum plastic
   slip and endpoint-cap times plastic-slip dissipation. Retain storage released
   at intermediate separations, including a pulse that ends open.
5. Commit only the accepted structural pose and pressure frame. Later material
   queries reconstruct the same discrete constitutive path. Restart identity
   binds the event rule and numerical settings.

Points with identical stage fractions may be batched. Their stage sequence does
not depend on other queries, quadrature numbering or point order. Actual-pressure
evaluations and return stages are bounded; exhaustion rejects the evaluation.

This is a refinable discrete return sequence. Midpoint stage locations do not
make its endpoint-cap work quadrature second order or exactly energy conserving.
Whole-path constant-normal/convexity restrictions remain. General rotation,
nonconvex patches, beam friction and engineering admission are not established.

## Evidence so far

- `contact-friction-replay-event-work-20261002.log`: 2 checks passed in 5.68 s.
  A material point traverses a one-metre fixed target while open at both segment
  endpoints. The independent continuous slider reference is
  `1.5 * (1 - 1.5/1000)` Pa m. Subdivisions 4, 16 and 64 give decreasing
  dissipation error; the finest is below 1%. Final storage is zero and released
  storage is positive. A query alone and in a batch agrees exactly. Resource
  rejection preserves committed state. The old full-coverage endpoint profile
  still agrees with its existing owner.
- `contact-friction-replay-event-report-20261002.log`: 2 checks passed in 4.17 s.
  Captured interval endpoints agree with independent scalar polynomial roots;
  candidate diagnostics leave physical state unchanged. Centroid and both-body
  virtual work checks also pass.

Raw logs are under `C:/ANYworkspaceWork`. Complete coupled execution, derivative
checks for this new rule, integration refinement, restart, installed-package
verification and independent assessment remain open. No runtime improvement is
claimed.


## Measured cost slice: exact stage cache

An LRU cache uses exact start/end local pose bytes and the stage fraction. It
stores immutable frame geometry and actual pressure, bounded by the existing
stage cap. Changed poses miss; resource eviction recomputes, never changes the
law. The penalty-only admission makes stage pressure independent of solver
multipliers. Restore validation uses a fresh disposable cache.

The same instrumented partial-slide residual changed from0.140699 to0.084844s,
with exactly identical force, storage, released storage and dissipation. Actual
pressure evaluations changed15->4;11 stages hit. Three focused checks passed
in5.33s. This is one local measurement, not a whole-route speed claim.

The actual nonguided coupled retry still timed out at180s. Recorded process-tree
elapsed190.1067s includes teardown; peak sampled194404352B. Seven candidate
evaluations completed and only the press frame was committed before timeout.
The synthetic profile understates the number of distinct event times in a
nonuniform coupled pose. Retain candidate_cost.jsonl under the cache-coupled
portable root for the next bounded decision.


## Exact full-coverage stage pressure specialization

For a source S3 face with physical unit normal ns and target plane (o,nt),
the source-normal projected nodal gaps are
`g_i = ((x_i-o) dot nt)/(ns dot nt)`. Projection points are `x_i-g_i*ns`.
Eligibility requires positive polarity, exact target planarity and strict
interior containment of every projected source corner in the validated convex
target union. Ambiguous/rim/partial cases fall back to the unchanged mortar law.
Existing same-side overlap and face validation checks remain.

With reference triangle area A and P1 basis, exact moments are
`S_i=A/3`, `G_i=A*(sum(g)+g_i)/12`. Accumulate S and G across source faces before
normalizing shared nodal gaps. Apply the existing penalty pressure
`p_i=epsilon*max(-G_i/S_i,0)`. This specializes integration only; it does not
replace the source normal by the target normal or alter the pressure space.
Only the admitted penalty owner with no reduced pressure basis is eligible.

Checks:24 tilted-source/deformed-planar-target poses match the unchanged mortar
within1e-12 relative/absolute, and partial coverage rejects the specialization
(1passed4.36s). An unequal-area two-source-face case matches the existing shared
mortar pressure at shared nodes (1passed3.77s). Recorded coupled press residual
profile changed1.374217s ->0.857003s with exactly equal force and work outputs.
The corresponding profile/pulse selection passed2checks6.31s. These local
measurements do not establish complete-route acceleration or qualification.

A separately registered integrated development run now uses the goal's900s
ceiling with953MiB memory and unchanged mechanics. Its exact source hashes and
one-shot execution decision are in event_integrated_development_registration.json.
Earlier180s failures remain retained failures.


## Registered integrated result and disposition

C5_PARTIAL_REPLAY_EVENT_INTEGRATED_DEV_20261002 is terminal and consumed.
The original nonguided route accepted press and partial slide, then raised the
explicit4096 pressure-stage cap during reversal, while replaying an earlier
segment for1296 quadrature queries. Pytest441.05s; process-tree442.669s;
peak sampled235950080B. The time/memory ceiling was not reached. No completed
workflow/restart or acceptance is claimed. Five registered source files have
been retained byte-for-byte against their prospective hashes under the run's
frozen_source directory; see event_integrated_development_result.json.

Next is a bounded stage-batching design, not an automatic cap increase or repeat.
The pressure-stage limit and the physical return-stage limit must remain explicit;
any changed accounting requires a new identified candidate, not relabeling this
failure. The independently required work/tangent/integration gates remain.

Post-run inspection correction: cache counters have been removed from accepted
physical summaries. Cold/warm prepare_commit gives identical physical summaries
without committing state (1passed6.01s, physical-summary log). Evaluation counters
remain available as disposable diagnostics. Future resource exceptions also save
the candidate pose/history, instead of capturing only tangent failures.


## Prepared affine pressure path — not yet connected to replay

New s3_friction_prepared_path.py represents source-edge cross product C(t) as a
quadratic polynomial and nodal target-plane heights h_i(t) as affine polynomials.
For one fully covered source triangle,
`g_i(t)=h_i(t)*norm(C(t))/(C(t) dot nt)` and
`p_i(t)=epsilon*max(-(sum(g(t))+g_i(t))/4,0)`.
It evaluates arbitrary time batches from these coefficients, without rebuilding
mortar overlap. This is the same reference P1 pressure law, not interpolation of
endpoint pressure. Multiple-source and uncertified paths remain fallback cases.

Eligibility uses exact rational coefficients derived from the supplied binary
floating-point endpoint coordinates. Conversion from power coefficients to
Bernstein coefficients proves sign over the entire unit interval. The source
projection denominator and reference polarity, target-face polarity, target
planarity and boundary convexity are checked. Source-normal projected boundary
distances become polynomials of degree at most4 after multiplication by the
positive projection denominator; all must be strictly positive. Inconclusive
Bernstein tests return no prepared path. Endpoint/sampled checks are not substituted
for these certificates. Existing owner topology supplies the conforming disk.

Focused discriminator: recorded actual press path plus nonuniform tilted source,
28intermediate fractions each, matches unchanged mortar at1e-12 relative/absolute.
Batch/single query identity passes. A half-turn square with valid endpoints but
interior collapse rejects, as does a partially covered path.1passed4.30s in
contact-friction-prepared-pressure-20261002.log. The prepared module is not yet
called by production replay. Next integrate bounded batches with explicit counters
and parity against the existing event-return implementation. The previous4096
failure and consumed integrated authority remain unchanged.


## Prepared batches connected — explicit development selection

`prepared_pressure_paths=True` now connects certified paths to `_step_events`.
DefaultFalse retains the ordinary event evaluator. Settings bind restart identity.
Only a certified single-source, exactly constant-plane/full-coverage segment uses
prepared frames; all others retain ordinary stage geometry and its existing4096
preparation cap. The previous failure remains a failure of that earlier route.

Resource accounting is explicit: ordinary geometry constructions keep their cap;
prepared scalar samples count against `maximum_path_samples`; temporary prepared
frames use `maximum_prepared_stage_batch` (default256); the stage LRU stays bounded
by4096 entries. Prepared-path caches use the existing history-frame cap. This
changes the computation, not the number/location of physical return stages.
Cache counters stay outside accepted physical summaries. No contacts are dropped.

History/traction/force/work parity against the ordinary evaluator passes at
1e-11relative/1e-12absolute, including fallback rejection with a one-frame ordinary
cap and bounded LRU eviction. The1296point discriminator computed6480prepared
samples in9.573s, ordinary constructions0, resident stage frames4096, batch cap16.
A single-point requery agrees exactly. The recorded press residual profile is
0.417111s, versus1.374217s originally and0.857003s with stage moments. Reference
force norm3.85316e-10N; difference norm7.54386e-16N. Its tiny stored energy differs
by4.6335e-27J. Do not describe this new ordering as bitwise-identical to the old
stage geometry or infer complete-route speed from these local measurements.

Evidence: prepared-batches2passed8.10s; prepared-cost3passed16.07s; prepared-tangent
1passed5.24s with both-body directional error<=1e-5 at two perturbations. Raw logs
under C:/ANYworkspaceWork/contact-friction-*. Full coupled/restart and scientific
acceptance remain open. Bounded Mistral review is in progress; no approval claimed.
