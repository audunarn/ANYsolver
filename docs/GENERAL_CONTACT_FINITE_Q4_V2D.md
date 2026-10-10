# Finite Q4 / S3 V2D development workflow

Status: verified against the assigned development criteria on the declared
2Q4/2V2D fixture, including installed fresh workflow, saved assessment, real
restart, strict release separation and caller safety. No engineering acceptance
or release is established by this example.

The opt-in profile composes the existing consistent corotational structural
driver with exact elastic Qualified Q4 source and NativeParity S3 V2D target
owners. The formulation-native total-Lagrangian S3 companion remains excluded.
Old Q4/Q4 profiles and default contact settings are unchanged.

## Public invocation

```powershell
Set-Location C:/ANYworkspaceWork/ANYsolver-contact-main-reconcile-20261001
$env:PYTHONPATH='C:/ANYworkspaceWork/contact_finite_q4_v2d_delivery_20261009/installed-candidate-v2/site'
$env:NUMBA_DISABLE_JIT='1'; $env:NUMBA_NUM_THREADS='1'
$env:OMP_NUM_THREADS='1'; $env:OPENBLAS_NUM_THREADS='1'; $env:MKL_NUM_THREADS='1'
$env:BLIS_NUM_THREADS='1'; $env:VECLIB_MAXIMUM_THREADS='1'
& C:/Python/Python314/python.exe -m examples.general_contact_finite_q4_v2d --through-step 16 --output fresh-new.json
& C:/Python/Python314/python.exe -m examples.general_contact_finite_q4_v2d --through-step 15 --output prefix-new.json
& C:/Python/Python314/python.exe -m examples.general_contact_finite_q4_v2d --through-step 16 --restart prefix-new.json --output suffix-new.json
```

The tested private wheel is
`C:/ANYworkspaceWork/contact_finite_q4_v2d_delivery_20261009/installed-candidate-v2/wheel/anysolver-0.4.7-py3-none-any.whl`,
SHA256 `eb00e0aaaacf9efb9d8be578116ab433886ac786227359743aa801579a71ccc0`.
Its 649 package payload files and actual imported private modules are checked
by `built-install-v2.json` and the guarded Python 3.14 runtime. Run from this
checkout with that private site on the import path, JIT disabled and all
numerical thread pools fixed to one. Commands shown above need new output
paths; evidence files are immutable and must not be overwritten.
Reproduction requires prospective numerical authority; these instructions do
not reopen a consumed development scope.
The default prefix is four steps; existing output files are refused. A report
stores returned accepted suffix poses, pre-terminal-seal snapshot states,
producer diagnostics/history, and the genuine terminal owner checkpoint. Bare
or report-contained checkpoints use the ordinary model/analysis validation.
Earlier poses are not invented when restarting from a bare checkpoint.

## Fixture and limits

The first fixture has two nonmatching Q4 source faces and two P1 V2D target
faces, ten nodes and sixty authoritative coordinates. The .05 m thick Q4 uses
its supported centered reference; V2D has reference-surface offset .01 m.
Physical source bottom offset is -.025 m and target top offset is .015 m;
source reference z=.0300002 m and target z=-.01 m preserve .2 micrometre clearance.
Material is isotropic elastic, E=1e5 Pa, nu=.3. Six-coordinate body anchors,
source clamp and target vertex-normal/yaw supports are explicit. Target vertex
normal coordinates are guided; its non-anchor bending/director rotations remain
unknowns. No artificial drill gauge or stiffness is added.

Twelve rigid-tilt increments precede force press, .02 m slide, open and
recontact. Maximum tilt is pi/3 within the existing 1.2 rad total-rotation cap.
Local deformation limits (.1 rad and translation/edge .01), the 50 micrometre
whole-face gap budget, fine shared Q1 source pressure, all positive support
rows and original quadrature tolerances remain in force. Production admission
uses complete disjoint connected homogeneous owner partitions, not fixed counts;
testing this first fixture does not qualify arbitrary meshes.

## Work, geometry and state

Physical positions use X+u+h Exp(theta)d. Spatial force pullback uses the
virtual-spin map B; additive-coordinate differentiation uses A. The tangent is
B.T H A plus the derivative of B.T acting on physical forces. These maps are
distinct at nonzero rotation. The focused theta=1 rad counterexample stays
inside the total-rotation envelope.

Finite sweeps enclose the entire exponential path and use Q1/P1 chart and
directed whole-pair bounds. Endpoint safety alone does not admit a path.
Projection ties, folds, unsafe gaps and unresolved branches retain refusal.

Q4 records bind owner-local reference deformational24 coordinates. V2D records
retain global committed18/COROTATIONAL metadata and untouched local
committed-constitutive18 coordinates, using the actual owner validators/seals.
Incoming checkpoints are validated without migration, stripping V2D metadata
or resealing. Snapshot records and terminal sealed records remain distinct.

## Verification scope

Fifteen unchanged source-overlay discriminators and the corrected exact native
companion refusal on the new installed wheel passed. These include actual
structural/contact q/z tangents, independent decimal work mapping, typed owner
round trip and mutation refusal, triangle sweep refusal and old Q4 manager
admission. The native-companion factory-alias test defect and unsupported Q4
offset constructor attempt remain retained failures.

The fresh installed public 16-step workflow passed in 39.2968414 s. Two saved-field
checks passed in 22.1246286 s across all 16 actual poses: current assembled
force/moment equilibrium and L1NCP, control values, physical/nodal wrench
balance, positive support, independent source-chart integration and physical
skin gap enclosure. Worst scaled force equilibrium was 1.132e-7 (gate 1e-6),
L1 NCP 2.026e-10 (gate 1e-8), and conservative gap lower−31.169µm (gate−50µm).
Reference orders 4/8 and adjacent finite-difference controls are empirical uncertainty
checks; they are not rigorous integration error bounds or a universal finite
geometry proof. Stored control reactions participate in the assembled current
equilibrium check; complete historical owner replay is not independently
reconstructed by the saved assessment.

A genuine installed 15-step prefix passed, followed by exactly one recontact
increment and a separate zero-increment terminal restoration. Full displacement
and all six supported-force comparisons passed inherited tolerances; supported
forces matched exactly. All four typed model-bound owner records and elastic
constitutive histories passed validation. Actual returned suffix/terminal
reports and checkpoints are retained. Free target bending response was
8.417e-7 rad against the inherited 1e-10 rad witness and 1.191e-13 rad roundoff
bound.

The independent rational-interval release check proved strictly positive
separation from both target P1 planes across both source Q1 faces, with minimum
distance lower 1.464e-7 m. It uses enclosed Decimal directors, corner numerators,
an upper target-normal norm and positive mutual chart margins. This is a
fixture-specific positive opening witness. The original 50 micrometre safety
gate is unchanged.

Cancellation after actual structural/material and contact trial work preserved
committed states, input checkpoint, model identity, contact context and restored
hooks. The affected old Q4 profile also passed a real 15-to-16 continuation and
zero-increment restore on the new wheel. The 22 test obligations were covered
in impact-selected stages, rather than one repeated whole suite. Full evidence,
failed attempts, exact resource accounting and source/result hashes are in
`C:/ANYworkspaceWork/contact_finite_q4_v2d_delivery_20261009/FINAL_HANDOFF.md`.

This evidence covers elastic frictionless contact on the declared fixture.
Formulation-native S3, arbitrary meshes, deterministic tied full-Hessian
ownership, folds, larger rotation envelopes and engineering acceptance remain
outside this tested row. Broader programme acceptance and historical mandatory
independence gates are not transferred by this delivery.
