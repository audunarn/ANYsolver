# D1 overlap-local swept-gap certificate: review brief

**29 September 2026. Development argument, not independent acceptance.** This
applies only to the planar, small-rotation Q4-source/S3-target interior route
using `q4_source_gap_certificate="overlap_local_dev"`. The corresponding
functions are in `q4_overlap_local_bound.py`; the solver calls them from
`GeneralS3PatchManager._swept_admissible`. Review geometry, moving normals,
floating-point margins and the route's path assumptions before promotion.

## Physical path and signed gap

The admitted shell work map is affine: physical skin vertices equal a fixed
reference position plus a constant work map times the authoritative solver
displacement. Thus linear interpolation between two candidate displacements
gives linear interpolation between their physical vertices, including
director-induced skin motion. The independent small-rotation skin construction
and mapped positions agree along a five-point trial path in
`test_physical_skin_path_matches_linear_swept_certificate_assumption`.

At any path time, write a source Q4 point as `s(u,v,t)` and a target S3 point
as `b(r,w,t)`. For a pair matched by the varying source projection direction
`p(t)`, `s-b=d p(t)`. The physical signed gap is

`g = n(u,v,t) · (s-b) = d [n(u,v,t) · p(t)]`,

where `n` is the unit physical Q4 normal. Positive alignment of the two
normal families is a condition of the projected bound. If this cannot be
certified, the implementation falls back to its full-pair normal-cone bound.

For a fixed unit axis `a` from the initial target face, a leaf's scalar
corner-pair minimum `m` bounds `(s-b)·a` from below throughout the linear
path: positions are convex combinations of spatial corners and time
endpoints. The quadratic Bernstein controls of the projection normal give
`a·p(t) >= c > 0`. When `m < 0`, the matching distance satisfies
`d >= m/c`. Since `0 < n·p <= 1`, a negative `d` gives `g >= d`; a positive
`d` gives `g > 0`. Consequently `min(0,m/c)` is a signed-gap lower bound.
The leaf subtracts a roundoff margin. The controlling denominator is the
projection-normal cone, not the physical-normal cone; the latter establishes
positive mutual alignment. An analytical warped pose independently gives
physical gap `−0.4082482905 m` and projected, swept and overlap-local lower
bounds of about `−0.5000000000 m`, consistent with this inequality.

## Spatial exclusion and subdivision

A fixed frame at the start pose encloses every source subrectangle and target
triangle over the linear path using their endpoint coordinates. The parent
projection-normal Bernstein controls bound the ratio of lateral to frame-
normal motion. Multiplying this ratio by the maximum possible frame-normal
separation expands the source/target boxes enough to retain any pair matched
along the moving projection. A disjoint expanded box therefore contributes
no represented overlap; it returns infinity. Every surviving leaf checks
the physical and projection normal cones before applying the scalar bound.
Failure of a cone check uses the broader full-pair swept bound. The minimum
over leaves bounds the represented region. The separate instantaneous
projected and local bounds are combined only when both bound the same
matching-projection region.

## Limits and remaining review

- This argument uses the small-rotation affine skin map. A finite-rotation
  work map requires a different path enclosure.
- The target is an S3 triangle and the source is the original bilinear Q4;
  this brief does not admit warped-shell structural formulations or physical
  rims to D1.
- The numerical margin is an engineering floating-point allowance, not an
  IEEE interval-arithmetic proof. Review its scale and cancellation cases.
- Existing random moving-warp samples, the affine-path check and the
  accepted shortened-trial check are development controls. A separate coarse
  one-increment press physically caused fractions below one and completed
  with an independent accepted-pose gap inside budget. None of these replaces
  independent certificate scrutiny or a frozen D1 state-safety assessment.
