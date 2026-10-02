# Experimental mixed B2 reference modes — 2 October 2026

The existing B2 owner now admits explicit virgin supported reference modes for
mixed Q4/native-S3 and all-S3 panels through `B2MixedReferenceModalDefinition`.
The B2FAST profile and existing creation API remain unchanged. Historical static
definitions do not acquire S3 mass or modal dispatch implicitly.

## Mechanical and public contract

Each S3 facet uses its existing native
`S3_V2D_TRANSLATIONAL_LUMPED_SECTION_AREAL_MASS_V1` operator once: rho*h*A/3 at
each vertex in translation, zero rotational contribution. **All S3 facet rotary
inertia is omitted**, including bending rotation. Shared nodes can retain Q4
director inertia. Q4 director mass and declared physical B2 section inertia use
their existing operators. Capabilities list each facet's policy explicitly.

The existing sparse constrained descriptor retains multiplier and zero-inertia
coordinates. No artificial mass, global dense nullspace, static dynamic reduction
or change to native element equations is introduced. New input requires complete
positive representable density/mass, coordinate supports detecting all six rigid
fields, zero prescribed offset and no prestress or footprints. Free-free,
geometric metadata and continuum-frequency qualification remain unsupported.

Cancellation/recognized backend failure publishes no partial modes; unclassified
programming errors propagate. Numerical thresholds remain unchanged. The new
definition's ANYfem persistence is not implemented; historical static and Q4 modal
consumer schemas retain their meanings. Complete F07/F12/G4B/M3/M4/G6 remain open.

## Verification actually executed

- Initial focused source run: 133 passed / 1 failed. The new failure fixture
  incorrectly expected an arbitrary RuntimeError to become nonconvergence.
  Corrected to the established backend diagnostic and added a separate unchanged
  programming-error propagation assertion. Product exception handling unchanged.
- A mistyped source node selector produced exit 4 with no execution; retained.
  Correct selectors pass 5/5 failure/cancellation checks.
- Independent review identified fixed interior drilling coordinates in the
  modal fixtures. Eight final dense-pencil comparisons now cover mixed/all-S3,
  reversed/forward connectivity and free/fixed interior normal spin. All pass,
  including massless spin stiffness and equation balance.
- Fresh installed run: **429/429** (262 solver, 167 consumer), including all 33
  final new cases. Analytic lumped inertia, first moment, frame covariance,
  section kinetic integration and an independently assembled small dense
  singular pencil check the claimed discrete mass/modal behavior.
- Two installed public examples complete, with static response unchanged before
  and after modes, one modal factor and the original one static factor each.

| Example | First three illustrative frequencies, Hz | Largest equation / constraint residual |
|---|---|---|
| Mixed Q4/S3 | 0.4671424, 1.5976477, 1.9370099 | 4.74e-16 / 2.68e-16 |
| All-S3 | 0.4429411, 1.4422463, 1.8703339 | 7.73e-16 / 2.54e-16 |

These frequencies are fixture outputs, not engineering references. Dense
oracles do not establish continuum accuracy or spectrum completeness.

## Artifacts, settings and retained evidence

Solver wheel SHA256:
`f41f07b2554e24ff843e73281479f09b965e878b4ce06f8693a4737055216fc0`.
Unchanged ANYfem wheel:
`15eb01d0ac2a0ae1e378a676cdf26bd27ea2bd5f0696ff66a374c0dab79b76f6`.
All 391 solver / 98 consumer Python modules match actual source, wheel and site;
275 imported modules stay in the selected site. Python 3.14.2, NumPy 2.4.6,
SciPy 1.17.1, Numba 0.65.1; effective BLAS/OpenMP/Numba each one thread, JIT off.

The installed suite took 36.994 s under supervision (pytest 34.20 s), sampled
peak process-tree RSS 223,223,808 bytes; each example about 1.68 s / 145 MB.
All within 180 s / 1 GiB. Timing records do not establish development or solver
speedups. Source uses the portable focused coordinator, not CI inventory scans.

[Independent review](review.md), [raw manifest](raw-v1.json), [raw archive](raw-v1.zip).
Archive retains failed/source runs, final fixtures, wheel, manifests, commands,
actual imports/settings and executed logs. Build/site copies are reconstructible
from wheel/source and omitted from duplicate archival storage.
Original root: C:/Users/AudunArnesenNyhus/AppData/Local/Temp/r8-b2-mixed-reference-modes-installed-v1.

No main merge, publication, default/version change, formal F03 consumption or
aggregate acceptance. Next consumer work must use a distinct explicit modal
input schema; full physical/spectral/external/scale acceptance remains required.

## Follow-on consumer and external-route development

The distinct modal input consumer is now delivered at ANYfem `cabb6ed`, with
224 installed checks and mixed/all-S3 Project examples. The original artifact
record above remains unchanged in scope; the new paired artifact and consumer
evidence are [recorded separately](C:/Github/ANYfem/.worktrees/experimental-ge-panel-consumer/docs/development/r8-b2-mixed-modal-consumer-20261002/results.md).

One US3 plate modal output canary now completes on the pinned CalculiX 2.23
executable `27a9426a...c9c5f`: 1 x .2 m, thickness .035 m, E210 GPa, nu .3,
rho7850 kg/m3, nx16/ny4, 85 nodes, 128 triangles, all-six root clamp. No beams,
attachments, prestress or imposed load. Six ordered modes and all six nodal
coordinates are parsed by eigenvalue-number headers. The first illustrative
frequency is 29.59976 Hz. Bending modes have nonzero rx/ry; the second in-plane
mode has nonzero normal spin. Coordinate activity is reported separately, in
the external normalization, without treating mixed-unit norms as accuracy.

Actual logs report one numerical CPU for matrix/stress assembly and spooles.
Supervision: 0.1032 s, sampled peak process-tree RSS 8,474,624 bytes, four total
process threads including infrastructure, within 600 s / 1 GiB. No error/warning,
resource abort or missing node/rotation inventory. Printed mass-normalization
diagnostics are observations, not certified eigen-equation accuracy.

Initial decoder checks exposed a NaN input reaching an untyped Decimal exponent
error: 12 pass / 1 fail, preserved and corrected with a finite-value guard.
Then 13 pass. Independent pre-execution review required standalone parsing to
validate actual execution status/resource outcome and reject FATAL. Those guards
and corruption/duplicate/missing-mode controls pass 16/16. The changed coordinate
activity output passes its affected 1/1 check. No engine repeat was needed.

This resolves route feasibility only. Retained source hardcodes ARPACK tol1e-2;
rounded frequency and displacement output cannot establish the required 1e-8
eigen-equation residual. No native comparison, spectrum completeness, refinement
convergence, 2% reference acceptance or F03/G4B acceptance follows. The continuous
US3 translation/director kinetic law is compatible with physical Q4 mass; it is
not a same-inertia oracle for the native S3 policy that omits rotary inertia.

Action: use these recoverable modal observables for a physically matched native
Q4 comparison, retaining native residual checks and a prospective convergence
argument. Do not repeat isolated B2 frequencies, change inertia, or automatically
add refinement. Raw output, deck, executed/prepared runners, fields, failed and
repaired decoder controls are in [the canary archive](us3-modal-canary-v1.zip)
and [identity/result manifest](us3-modal-canary-v1.json). Review is separate
implementer Read scrutiny, not different-model-family qualification.
