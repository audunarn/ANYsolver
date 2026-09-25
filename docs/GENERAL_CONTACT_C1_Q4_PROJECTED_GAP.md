# Q4/Q4 projected-gap development profile

`Q4_Q4_GENERAL_NODAL_PRIMAL_MORTAR_AUGMENTED_STATIC_DEV_V1` is an opt-in
development candidate for one explicit qualified Q4 face on each side. Set
`q4_source_gap_certificate="projected_matching"` with the existing general
primal-mortar and augmented-normal settings. The multi-control path uses
`Q4_Q4_PATCH_GENERAL_AUGMENTED_PATH_DEV_V1`. The default `whole_face` selector
retains both V0 identities and their restart contracts.

## Static lower bound

At one current pose, let `n` be the unit projection direction defined by the
Q4 source. The registered mortar overlap maps a source point `x_s` and target
point `x_t` to the same point in the plane normal to `n`. Consequently,
`x_s - x_t = δ n`. Choose an oriented target-edge direction `a` with
`a·n > 0`. Q1 source and target positions are convex combinations of their
four corners, so for every matching point:

```text
L = min_i(a·S_i) - max_j(a·T_j)
δ >= L / (a·n)
```

The physical source normal `m_s` has `0 < m_s·n <= 1` while the Q4 projected
Jacobian is positive. The physical signed gap is `g = δ(m_s·n)`. Therefore
`min(0, L/(a·n))` is a lower bound on that gap. The kernel subtracts an explicit
roundoff allowance and takes the greater of this bound and the existing
full-pair cone bound. It falls back to the latter when `a·n` is poorly
conditioned. This limits only the matching projected overlap; shell rims and
unrepresented features need separate kernels.

## Swept lower bound

During an admitted linear nodal trial, source and target corner trajectories
are linear in path time. A matching-point difference is a convex combination
of corner-pair differences at the same time. Its component along a fixed
target axis `a` is bounded below by the least corner-pair component at either
endpoint. The source projection normal and each source physical corner normal
are quadratic in time. Their three quadratic Bernstein controls bound their
axis cosines over the entire trial. The projected formula is used only when
all these cosine lower bounds are at least 0.75. This sufficient condition
keeps the physical and projection normals mutually acute. Otherwise the V0
full-pair swept cone remains in force. Both formulations bound the same
matching-point gap from below, so their maximum is also a lower bound.

The finite-difference/contact integration method is unchanged. V1 changes
which trials the independently checked gap and sweep controls can certify;
its profile and restart identity therefore differ from V0. The new selector
is rejected for other contact combinations. Checkpoints bind the selector.

## Development evidence and limits

Independent Q4 shape, normal and projected-target inversion code sampled
matching points on planar and warped targets, opening, rigidly transformed
poses, and moving-target paths. It also checked the analytic planar-target
projection distance and a large-rotation fallback. All four focused geometry
tests passed (`q4-projected-static-swept-oracles-first.txt`). These samples
support the derivation; they are not themselves a continuous proof or an
engineering acceptance result.

The exact Q4/Q4 profile admission and rejection checks passed. A synthetic
single-corner trial that the V0 whole-face cone rejects at 0.1 mm was
certified by V1 in both static and swept checks
(`q4-projected-v1-admission-geometry-first.txt`). Public ordinary force and
displacement solves, a 0.2 mm four-phase path and its opening-checkpoint
restart passed. One 0.04 mm closure with 10× normal stiffness met the declared
0.05 mm independent gap check (`q4-projected-v1-50um-first.txt`). The V0
tight-gap rejection still passed after this change
(`q4-projected-v1-v0-regression.txt`).

The 0.05 mm run is a single candidate, not mesh, integration or enforcement
convergence. Numeric roundoff allowances are bounded development guards,
not directed interval arithmetic. Pressure-space stability, partially
contacting nonmatching meshes, edge ownership, reference-warped Q4, independent
review, installed-package verification of V1 and application adapters remain
open. No C1 engineering acceptance is claimed.
