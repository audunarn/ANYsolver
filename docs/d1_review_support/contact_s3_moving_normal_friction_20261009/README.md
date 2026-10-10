# Moving-normal S3 material friction (development)

This new opt-in row uses `S3MovingNormalFrictionSettings`, the original physical S3 skins, fine shared P1 pressure, and the existing monolithic supported-force owner. It admits one full source triangle inside one target triangle, all positive pressure with independently checked physical closure, or strict opening with zero pressure. Partial contact, multi-facet moving targets, finite rotations and engineering acceptance remain open.

At finite gap, projected material-anchor displacement changes when only the target normal changes. A source-ray proxy merely moves that defect to source rotation. Neither is adopted as physical friction. The new hard-normal row requires corner AND stored dense friction-point gaps <=1e-10 m at closure; the existing projected return is its off-manifold Newton extension. Full-face P1 support has positive area/3 and consistent-mass rank three. Weak closure alone is not accepted.

The normal force is evaluated at fixed supported force z, with all moving-support quotient derivatives. Friction uses lambda/(source-normal dot target-normal) per source REFERENCE area, not current-area Cauchy traction. Its complete q and z derivatives enter the existing nonsymmetric coupled blocks. Every friction candidate shares the same committed history; validation of the successor precedes material/contact commit.

The path checker encloses physical corner maps and separately stored dense point maps over the entire affine authoritative DOF chord. It checks both orthogonal material projection and source-normal mortar rays, source/target representability, polarity, and full-inside clipping. Matched interval primary operations follow Jet2 reciprocal-then-multiply division and actual scale-squared branch thresholds. This is a conservative one-pair full-inside development certificate, not general swept friction qualification.

## Fixture and proof scope

Two contact triangles are attached to real noncontact S3 support triangles. Source normal coordinates and target normal/ux coordinates are independent; source ux/uy are tied to two path controls and rotations are fixed. The manufactured first load reuses qualified structural K and independently integrates uniform planar P1 skin forces. It is code verification, not an independently solved nonlinear displacement reference. Subsequent unchanged loads produce stick/slip/reversal/open/recontact.

Frozen scientific scales are Fref=.02 N and Mref=.02 Nm separately: equilibrium/wrench <=1e-6, directional tangent <=1e-5, C/Fref <=1e-8, dimensional gap <=50um, work tolerance 1e-12 J. Solver complementarity reference is .001 N, adopted after the original .02 N control failed the existing maximum-declared-load guard. The old refusal is retained; physics and scientific gates were not changed. Endpoint storage/dissipation are not path-integrated work.

Evidence and precise resource ledger: `C:/ANYworkspaceWork/contact_s3_moving_normal_friction_20261009`. Metadata source staging and wheel unpacking are separate from guarded child process-wall accounting. Final outcome/check counts are recorded after closure; no acceptance or release claim is made here.

Completed evidence and exact scope: see OUTCOME.md and IMPACT.md. Accepted-endpoint work bound is not a path-integrated work/normal-gap claim. The measured target-normal delta during slip is approximately7.65e-9 in x and2.46e-9 in y; its birth tilt alone is not the motion discriminator.

The inherited explicit pressure_tolerance remains restart-bound; monolithic acceptance uses force-based complementarity rather than that inherited pressure tolerance. Rotations are fixed in this fixture: the target normal changes through its independently solved nodal normal displacements.
