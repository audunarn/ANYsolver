# Guided shell/free sphere — shared-driver development slice

Parent checkpoint7b7a88c2; final source identities in
[manifest](contact_c6_free_shell_sphere_20261003/source.json),
[raw records](contact_c6_free_shell_sphere_20261003/raw.zip).
Full C0–C9 remains active. No acceptance, release, publication or default change.

## Decision and implementation

Native variable-front envelopes do not bound the closed event-sensitive tangent:
alpha_q=-G_q/G_alpha and elastic mixed work derivatives remain unresolved at grazing.
Retain those nonpasses and restrictions. Choose a separate required D5 boundary
instead of another native refinement campaign.

Extend the shared radial work mapper explicitly to qualified planar-reference Q4
physical skins. For shell unknowns u and sphere centre offset c, translation
covariance gives R=[f;-A.T f] and K=[K,-K A;-A.T K,A.T K A]. A maps contacting
nodal translations only; offset-rotation terms remain in the shell force Hessian.
Normal displacement modes are retained independently. Actual constraints enforce
zero rotations and in-plane translations. Three physical centre coordinates and
supplied mass join the same constrained Newmark equations. Isotropic central-force
spin is exact and decoupled. The existing aggregate nodal-pressure potential remains.

Exact rational tensor Bernstein controls enclose degree(1,1,3) relative position
and degree(2,2,6) squared distance across both face coordinates and time. All faces
contribute; subdivision budget is shared. Source review identified a separate
selected-side domain: a distant sphere can pass radial distance while the shell
crosses behind it between endpoints. An exact scalar cubic centroid-side certificate
now precedes acceptance and shares the distance subdivision budget. The second
review finding was aggregate constraint normalization hiding free tangential motion
beside a1e14 normal MPC coefficient; normalized columns are checked separately.
Both counterexamples and a rotated-normal MPC positive case are covered.

The geometry worker owned only the new bounds module/tests. Lead inspected source
and reran all43 geometry outcomes. Worker read-only scrutiny of lead-owned work,
driver and tests found the two corrected guards and no further concrete block in
the follow-up delta. Same-family independent authorship is source scrutiny, not
the independent engineering/cross-family acceptance gate.

## Actual development evidence

Effective Python3.14, JIT off, BLAS/Numba threads1, reconciled source imports.
Explicit portable selector commands and runtime/resource records are retained.
Routine180s/953MiB limits remain. Final distinct affected outcomes: eight new driver
checks,43 geometry outcomes, five existing beam/Q4 response/work/restart outcomes.
Passed evidence is reused only for unaffected behavior; this is not one56-test run.

| Check | Observation |
|---|---|
| Smooth local work/tangent | Two full shell/body directions at h=1e-7 meet1e-5; energy work, translation invariance and both-body wrench pass; no perturbation-interval qualification claim |
| Symmetric continuum/two-body oracle | Independent24×24 integration and independent Newmark; max position error6.322e-11m, force error4.078e-9N |
| Both-body dynamics | 44 accepted dt=.0005s steps, zero cutbacks, press/open; nodal shell modes retained; impulse/normal momentum and equal/opposite force pass |
| Energy refinement | Independent continuum penalty potential, positive translational energy scale with spin checked separately; dt=.0005/.00025 defects0.004623181/0.001132720, improving and below1% |
| Geometry and side | Independent polynomial, analytic minima, hidden interior crossings, physical offsets, both body velocities, multiple faces, exact extremes, budget/cancellation controls; selected-side counterexample rejects |
| Restart/state | Active.014s split reproduces displacement/centre1e-10; changed mass rejects; cancellation/exception leaves model/definition/context reusable |
| Compatibility | Existing Q4 mass-spring and free B2/B3 work/response/active restart checks pass |
| Installed example | All numerical fields and208 loaded module hashes identical; wheel SHA2565462ac6159aa315d3dc5d9d411b483024aeee41e7b7b7de6924d6e1088a3f4d8 |

Final example max residual8.409e-11N, max reaction0.081038508N, minimum represented
swept gap-0.001573989m within the explicitly selected2mm development budget,
normal momentum error1.626e-19kg m/s; final open. This budget is not the programme
qualification budget. The symmetric case does not establish spatial convergence.
Nonuniform normal-mode response passes momentum but has no continuum reference.

The final side/full driver run:16.080s/182898688B,6passes. Geometry+energy run
20.415s/193708032B had45passes/two test-API failures, retained below. Changed-mode
run17.913s/181878784B had one real dynamic pass and one test-API failure. Corrected
MPC selector4.888s/181657600B passes. Existing compatibility/corrected interruption
run13.243s/188268544B,4passes. These are bounded development measurements, not savings.
Installed example4.027s/159973376B; source example4.140s/160964608B; paired mechanics
only, no performance claim. Neither full engineering admission nor release follows.

## Retained defects / open boundaries

Geometry worker a/b/c turning/refinement-starvation failures are preserved in raw
records; final independent fixtures pass at unchanged limits. Lead energy run had
two cancellation-fixture failures from wrong keyword `cancel_token`; correction
uses `cancellation_token`. MPC regression first used the wrong constraint-builder
signature/unpacking; corrected actual API passes. Initial wheel build could not
write the default pip cache; `--no-cache-dir` and owned temporary directory build
succeeded. No tolerance, mechanics or resource limit was changed for these repairs.

Nodal-history/work branch still requires a shell-specific integrated test. Arbitrary
finite rotation, S3/free-body, anisotropic inertia, friction, nonlinear material,
event-time localization, mesh/enforcement/time qualification and full C6 are open.
The interpolation enclosure is not a continuum collision certificate. Installed
accepted D1/D2 artifact and scientific dispositions remain unchanged. Native failed
evidence/consumed run authorities are unaffected.
