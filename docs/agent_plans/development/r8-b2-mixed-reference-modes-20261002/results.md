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

## Matched Q4/US3 two-level modal discriminator — 2 October

The installed solver `80ca5f5e...d5` was used unchanged; all 391 module bytes
match its frozen source inventory. A virgin 1 x .2 m plate, h=.035 m,
E=210 GPa, nu=.3 and rho=7850 kg/m3 has the same physical nodes and all-six
x=0 clamp in each pair. Q4 has 64/256 cells; US3 has 128/512 triangles.
Native Q4 uses complete stationary stiffness and canonical physical director
mass. Normal spin remains massless and in free-row equilibrium. There are no
beams, attachments, prestress or imposed loads in this component comparison.

| Physical mode | Native 16x4 Hz | US3 16x4 Hz | Native 32x8 Hz | US3 32x8 Hz | Fine signed gap |
|---|---:|---:|---:|---:|---:|
| 1 | 29.552973 | 29.599760 | 29.518805 | 29.535230 | -0.0556% |
| 2, in-plane | 163.773412 | 178.498500 | 162.853180 | 166.892100 | -2.4201% |
| 3 | 185.711618 | 185.787300 | 184.225939 | 184.281900 | -0.0304% |
| 4 | 279.677590 | 283.765000 | 275.874331 | 277.862600 | -0.7156% |
| 5 | 525.380336 | 524.857600 | 514.207027 | 514.242900 | -0.0070% |
| 6 | 855.768528 | 872.116600 | 841.656150 | 848.649700 | -0.8241% |

Full 8x6 common-Q4-mass MACs identify dominant matches 1–6 at each grid.
Across grids, saved fine nodal fields are restricted to the identical coarse
nodes and compared with the coarse physical Q4 mass: native/reference matching
is consistent with both cross-family assignments. Minimum selected MAC over
these six tracks is .9998966 native and .9987612 external. This is a nodal
shape diagnostic, not exact US3 P1 integration or repeated-eigenspace acceptance.
Massless rz is excluded from MAC and its differing shapes are reported separately.
The reported rz difference is an unweighted nodal norm, not a mesh-independent
drilling convergence measure. Coarse-node restriction can miss variation between
those nodes; neither diagnostic is a substitute for physical strain/work checks.

The disputed in-plane gap shrinks from -8.2494% to -2.4201%; native frequency
changes -0.5619%, external -6.5022%. It establishes a substantial discretization
contribution, without isolating interpolation, membrane/drilling stiffness,
clamp treatment or external eigensolve error. US3 membrane is Kb+Kh with
drilling coupling, not a plain CST oracle. Near-unit MAC does not prove equal
drilling response or strain energy. No rotation-axis or inertia repair follows.

Native controls: six local rigid fields <=1.1e-16; representative first-cell
actual GE historical/algorithmic zero-state tangent parity <=2.5e-16; analytical
uniform inertia error <=1.6e-16. Fine native original-equation residuals
<=3.4e-15; one sparse factor and 27 solves, no global dense inverse/nullspace.
This is representative local GE parity, not a measured whole-owner tangent check.

Both jobs completed within 600 s / 1 GiB at effective one-thread settings,
JIT off. Native fine run: 3.596 s / 186,875,904 B sampled tree RSS; external:
.176 s / 12,476,416 B. Seven/four total process threads include infrastructure;
numerical pools and actual CCX logs use one. These are resource records, not
speedup measurements. Six MAC source controls and the changed 32-grid preparation
check passed in distinct focused runs. An initial postprocessor syntax failure
is retained; corrected saved-field interpretation required no numerical rerun.

**Decision:** retain the component operators. Stop this diagnostic after the
single planned refinement. Prepare a prospective three-level, physically
matched spectral assessment with reference-error controls before claiming
converged 2% accuracy; do not automatically launch nx64. Two grids, a shrinking
gap and small native residuals establish neither reference convergence nor the
external equation error. F07/F12/G4B/M4, coupled modal physics, free-free,
prestress and full programme acceptance remain open. This plate-only result
does not select BL5 mechanics or consume formal F03 authority.

[Coarse raw/result](q4-us3-compare-n16-v1.json) and
[fine raw/result with cross-grid fields](paired-modal-discriminator-n32-v1.json)
bind their versioned ZIPs. The fine archive has 53 files, SHA-256
`48ac40187dd5b1bf2eeb32b444214d65a48f3dd679c701a32da470c5019eac7c`.

### Environment-recording correction and dissemination restriction

The canary recorder copied the full inherited environment into metadata. Review
found nonempty credential variables in the earlier committed canary archive and
the new local raw metadata. Future recording now uses an explicit runtime
allowlist; the integration-style mocked supervisor regression passed 1/1 and
does not execute an engine. No scientific input/output or numerical run changed.

The new archive contains a separately named sanitized metadata derivative with
the original SHA and omitted-field disposition; original local bytes are retained.
All proposed fine archive members were checked against the credential values
without printing them. **Do not push or redistribute the earlier canary archive
or its Git history until credentials and history have been remediated.** The
historical archive/history have not been rewritten under scientific-preservation
authority. This requires coordinated cleanup and rotation of affected keys,
separately from numerical acceptance; the new archive has no credential values.
