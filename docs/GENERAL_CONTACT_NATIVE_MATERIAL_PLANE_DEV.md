# Retained native material patch / plane — development

## Precise angular partition correction — 4 October

Source f11f6ce7 resolves the reconstructed nearly uniform axial integration failure
in the tested straight native material profile. Bounded50-digit scalar gaps, roots
and quadrature coordinates preserve tiny positive arcs; existing Jet2 derivatives,
Gauss8/16 dimensional controls and64interval cap remain. Unresolved root separation,
grazing and zero quadrature measures reject explicitly. Plane/material-S3 numerical
identities change; historical native line checkpoints replay. Old failure retained.

38fresh installed checks pass:26geometry checks47.669s/189325312B and12lifecycle
checks114.098s/328114176B.519source files/220imports match; JIT disabled,pools1.
Uniform tangent errors1.64e-10/4.89e-10, independent energy error3.12e-17J.
Yielding9-target split restart remains exact, gap19.203um, supportF/M6.93e-9/6.49e-9;
complete plastic tangent3.38e-8/2.21e-9. Supporting scrutiny, not independent
acceptance, release or measured speedup. Convergence, curved geometry, friction,
dynamics and application admission remain open.
[Evidence](d1_review_support/contact_native_material_s3_20261004/angular_summary.json),
[review](d1_review_support/contact_native_material_s3_20261004/angular_review.md).

An explicitly selected straight B3-GE interior half-cell material patch now uses
the existing retained static owner. It preserves all 42 structural coordinates;
physical cell rotations move the declared round section and carry contact couples.
This is a material-surface profile, distinct from centreline-tube line contact.

Run `python examples/general_contact_native_material_plane.py` in the reconciled
checkout. The example reports its development profile, reactions about the global
origin, normal storage, continuous patch gap lower bound and checkpoint identity.
The API remains internal/experimental; no engineering or application admission.

## Equations and ownership

For the straight reference, `x(t,alpha)=(1-t)p0+t*p1+Uc*R0*rho(alpha)`.
The penalty potential is `0.5*k*integral(min(g,0)^2 dA0)`, with explicitly supplied
`k` in N/m³ and fixed reference measure `r*|reference chord| dt dalpha`.
Axial integration is analytic on open/full/partial branches. Angular Gauss 8/16
controls energy, force and tangent independently under a finite interval cap.
Local nine-coordinate Jet2 blocks map to all 42 retained coordinates; one spatial
chart conversion is applied after assembly. Algebraic nodal rotation traces and
resultants are not assigned contact position work or fictitious inertia.

The material scalar projection now uses bounded50-digit gap/partition arithmetic
near angular extrema. Numerically unresolved queried activation poses at an extremum or
material arc boundary fail before quadrature; the arithmetic eligibility band is
bound into restart identity. This does not prohibit first touch along a certified
trial path or claim the absence of grazing throughout that path.
This is not a penetration/work tolerance, dropped contact or changed penalty law.
The existing S3 normal integration keeps its prior numerical convention.

The owner shares native equilibrium, constraints, histories and authenticated
checkpoints. The actual exponential trial path uses radius-dependent gap speed
and surface orientation bounds. A hidden rotational penetration with open
endpoints and midpoint is rejected. Cancellation or a staging exception retains
the last accepted prefix. Incompatible definitions/settings reject continuation.

## Evidence and limits

Source checks cover independent area energy/force/moment, complete directional
tangents, fixed-node section work, common rigid transformation, a fresh S3
both-body work/cross-block comparison, coupled reaction balance, split restart,
hidden crossing, unresolved grazing, staging exception/cancellation and example.
At explicit k=1e6 and 1e7 N/m³ the coupled gaps are 30.269 and 11.067 micrometres,
within the unchanged 50 micrometre budget. The reaction changes 2.21%; this is
penalty sensitivity evidence, not completed enforcement/continuum convergence.

Retained failures: k=1e5 cannot meet simultaneous gap/equilibrium for this fixture;
the original independent oracle emitted roundoff warnings; the unanchored k=1e7
projection exhausted 64 intervals. Their raw inputs/results remain preserved.
[Evidence](d1_review_support/contact_native_material_plane_20261004/README.md).

Only one beam, one fixed plane and one strictly interior straight untwisted
reference half-cell patch are admitted here. Unselected surfaces, end caps,
interfaces, curved reference, nonlinear material qualification, friction, native
dynamics, deformable-target owner and multi-beam ownership remain required work.
No general rim regularity or mesh acceptance follows from this discrete slice.
