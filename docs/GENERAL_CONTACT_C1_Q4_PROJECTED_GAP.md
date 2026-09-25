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

For a planar Q4/Q4 pair with half-face overlap, independent tensor-Gauss
integration of the original Q1 pressure basis reproduced the implemented
reference support and pressure Gram to `1e-10`. The pressure Gram had positive
rank, its row sums equalled the support weights, and a fixed 10 Pa augmented
pressure over 0.54 m² produced 5.4 N with balanced body forces. A separate
2%-width overlap retained positive Gram rank. The Gram condition estimates
were about 58 at half overlap and 86,000 at 2% overlap
(`q4-partial-pressure-second.txt`, `q4-partial-pressure-conditioning.txt`).
This is a local consistency and conditioning observation, not an inf-sup or
mesh-refinement stability result. The first test attempt used a nonexistent
test-side field and is retained as `q4-partial-pressure-first.txt`; the
corrected tests passed without a production-kernel change.

The 0.05 mm run is a single candidate, not mesh, integration or enforcement
convergence. Numeric roundoff allowances are bounded development guards,
not directed interval arithmetic. Pressure-space stability across meshes,
partially contacting nonmatching meshes, edge ownership, reference-warped Q4, independent
review and application adapters remain
open. No C1 engineering acceptance is claimed.

The runnable [V1 Q4/Q4 example](../examples/general_contact_q4_q4_projected_gap.py)
uses the 0.04 mm closure and 0.05 mm gap budget by default; `--four-phase`
selects the 0.05 mm closure and 0.2 mm gap budget lifecycle case. The source
default run completed with one active pressure DOF, seven augmentation passes,
0.1211 N normal force and a −0.0400 mm conservative lower gap
(`q4-projected-v1-example-tight-source.txt`). The source four-phase run
completed with zero multipliers on opening and four active pressure DOFs on
recontact (`q4-projected-v1-example-four-source.txt`). These are development
settings, not general regularization recommendations.

A wheel built from clean source commit `590cb5ad` has SHA-256
`941d9322e904afe78cf90bae81e101677f8bbbd41fdf67e53aa64022504bd10d`.
It was installed offline without dependencies into an isolated target, and the
import origin was checked there. Both example modes completed against that
installed package. Their complete outputs matched the source outputs byte for
byte (`q4-projected-v1-example-tight-installed-590cb5ad.txt`, output SHA-256
`679562622b986036e6db48555a5d6cae5dbdd92206482388bfba24f933cc8806`;
`q4-projected-v1-example-four-installed-590cb5ad.txt`, output SHA-256
`352d47e244c1b4d12db0ab19a320c831afbb312af9fa085ee6e9a8a01fcb19f3`).
No package was published. Installed agreement does not establish numerical
qualification or application integration.
