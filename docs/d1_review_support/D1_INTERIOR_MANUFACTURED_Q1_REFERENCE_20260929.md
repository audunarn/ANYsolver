# D1 interior analytical Q1 benchmark — development result

**29 September 2026. Development only.** This is a bounded analytical
code-verification candidate for the admitted interior Q4/S3 shell-static
profile. It is not a retrospectively registered acceptance pass, a
representative spatial-accuracy reference, or independent assessment. The
source was `378cb10c` plus the uncommitted fixture extension. The local
solver mechanics were unchanged from that commit.

## Exact weak solution and independent loads

Use a 1 m square guided E4-PL Q4 source with all director rotations fixed,
transverse displacement fixed at its physical perimeter, and its bottom skin
40 µm above the fully covering, fixed S3 target top skin. The two target
triangles have nonmatching nodes and their outer edges lie beyond the source.
The shifted lower target edge avoids an exact artificial-diagonal/source-corner
tie without changing full coverage. Shell thickness is 50 mm, Young's modulus
`10⁵ Pa`, Poisson ratio `0.3`, and transverse shear resultant

    As = (5/6) Et / [2(1+ν)] = 1602.56410256 N/m.

In normalized source coordinates `X,Y∈[0,1]`, define

    φ(t) = 4t              on [0,1/4],
           1               on [1/4,3/4],
           4(1−t)           on [3/4,1],

    ψ(t) = 0               outside [1/4,3/4],
           4(t−1/4)        on [1/4,1/2],
           4(3/4−t)        on [1/2,3/4].

The exact guided-shear obstacle fields are `w=−40 µm φ(X)φ(Y)` and
`p=4 Pa ψ(X)ψ(Y)`. The pressure is nonnegative and supported strictly in the
interior, where `w=−40 µm`; elsewhere the physical gap is nonnegative. Since
`∫ψ=1/4`, the analytical contact reaction is **0.25 N** at centroid
`(0.6,0.6) m` in world coordinates. Its force moment about the global origin
is `(0.15,−0.15,0) N·m`.

The independently specified external nodal loads are the continuum weak
functionals

    f_i = As ∫∇w·∇N_i dA − ∫p N_i dA.

The fixture integrates these functions with separate 8×8 Gauss quadrature
on each source cell. It does not read the ANYsolver stiffness or contact
matrices to construct loads. `w` and `p` are exactly tensor-Q1 on all three
grids, so this checks the structural/contact work and nonlinear solver
without a structural interpolation error. A prior local element control
independently checked the E4-PL guided-normal block against the analytical
Q1 shear matrix. Small nonlinear membrane effects may remain and are measured.

## Bounded development runs

| Q4 grid / S3 faces | Active pressure nodes | Reaction relative error | Elapsed | Peak process memory |
|---|---:|---:|---:|---:|
| 4×4 / 2 | 1 | 2.79×10⁻⁸ | 19.08 s | 300 MB |
| 8×8 / 2 | 9 | 3.55×10⁻⁸ | 52.01 s | 427 MB |
| 16×16 / 2 | 49 | 4.28×10⁻⁸ | 178.46 s | 482 MB |

Every case completed two force increments. On the 16×16 case, maximum
nodal displacement error against the analytical Q1 field was
`3.42×10⁻¹³ m`, maximum nodal pressure error `5.34×10⁻⁷ Pa`, independent
nodal lower gap `−1.00×10⁻¹³ m`, and maximum physical rim pressure zero.
The full coupled residual norm was `9.97×10⁻¹⁶`, relative force
complementarity `2.09×10⁻¹⁵`, and source/target wrench imbalance near
roundoff. The independent nodal gap check is sufficient here because the
source skin is flat with fixed directors and its bilinear gap to the planar
target attains its minimum at a Q4 corner.

[Four-cell result](d1_manufactured_q1_4_20260929.json),
[eight-cell result](d1_manufactured_q1_8_20260929.json),
[sixteen-cell result](d1_manufactured_q1_16_20260929.json), with adjacent
logs and resource records, retain the raw evidence. The fixture is
[`scripts/general_contact_d1_interior_analytic_strip_dev.py`](../../scripts/general_contact_d1_interior_analytic_strip_dev.py).

## Failed paths and limits

The initial one-dimensional both-end-supported strip would have produced
active pressure on the source's physical y rims, outside the D1 interior
profile. Its unshifted target stopped at an artificial-diagonal clipping
tie; the explicit tie policy then rejected a conflicting raw gap direction.
Shifting the target edge removed the tie, and the D1 profile correctly
rejected an active y-rim reaction of `0.0213496 N`. Preserve these results
as admission evidence; the 1D strip is parked.

A separate smooth C¹ two-dimensional manufactured field was admissible
but has `5.85%` and `3.40%` reaction errors on the 4×4 and 8×8 grids. It
shows ordinary spatial error and remains available as a spatial convergence
discriminator. Its result does not weaken the exact Q1 code-verification
case or establish the 2% representative response gate.

The exact Q1 benchmark is intentionally representable and its target is
fixed. It cannot replace a refined continuum comparison of a deformable
two-body response, moving-front pressure stability, free director work,
transaction/restart checks or installed-package qualification. A formal
claim-bearing run needs prospectively frozen source, inputs, scales,
tolerances and independent assessment; none of these development outputs
are retrospectively promoted.
