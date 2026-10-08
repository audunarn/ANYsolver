# Prescribed-edge Q1 pressure null — analytic and saved-shell check

**29 September 2026. Development mechanics finding; no production-law edit.**
The saved guided 16×8 Q4/S3 pressure work has 153 positive-support Q1
pressure functions and scaled numerical rank 144 after source constraints.
This check asks whether the nine missing directions are physically redundant
or a finite-element work null. It uses the independently verified scalar
reduction of this fixed-target, rotation-guided planar fixture, then checks
the saved nonlinear shell work at the same pose.

## Exact discrete construction

Let `M_x` be the positive definite Q1 mass matrix along x, with 17 source
nodes. The source transverse displacement is fixed at x=0 for each of nine
y rows. Define `r_x=M_x^{-1}e_0`. For any admissible **discrete** transverse
virtual displacement `v_h`, its x=0 coefficient is zero, so
`v_h^T M_x r_x=v_h^T e_0=0`. With any y pressure hat `q_j`, the tensor pressure
field `p_j=r_x⊗q_j` therefore has zero work against every admissible Q1
transverse displacement. The nine `p_j` are linearly independent. Clipping
the y mass at the target rim `y=.9` leaves all nine supports positive.

These are **not physical annihilators**. The continuous displacement
`v(x,y)=x r_x(x)q_j(y)` is continuous, piecewise polynomial, belongs to H1
and vanishes at x=0. Its pressure work is
`(∫ x r_x(x)^2 dx)(∫_0^.9 q_j(y)^2 dy)>0`. Each pressure also has strictly
positive L2 mass. Because `r_x` is finite, a sufficiently small signed
multiple can perturb a strictly positive nodal pressure field while keeping
all coefficients nonnegative. Positivity alone cannot remove the local
pressure indeterminacy at an active clamp.

Exact polynomial line mass and a separate two-point integration of the
continuous witness yield:

| Quantity | Result |
|---|---:|
| Tensor Q1 pressure modes / free transverse coordinates | 153 / 144 |
| Exact tensor work rank / predicted null count | 144 / 9 |
| `M_x r_x−e_0` norm | 1.59e-16 |
| Scaled work of all nine tensor null vectors | 1.48e-18 |
| Minimum pressure Gram eigenvalue | 4.00e-8, positive |
| Continuous admissible work over nine y hats | 3.78e-6 to 0.1333, all positive |

The earlier saved shell energy check reports 144/153 scaled rank. Replaying
the accepted nonlinear pose gives source-`uz` pressure work within 2.88e-8
relative of the independent tensor mass, and the nine analytic vectors have
3.85e-9 scaled work against **all** reduced admissible shell coordinates.
The saved nonlinear pose is only near the flat tensor reference, so this is
a near-null comparison, not an assertion of exact shell nullity at that pose.
An independent read-only reviewer checked the exact clipped mass, tensor
null, continuous witness and saved-shell comparison and found no concrete
defect. The reviewer emphasized that each `r_x` changes sign; the result
does **not** prove failure of the actually settled right-side unilateral
active cone, which had full rank. It prevents a full-supported pressure-space
stability or physical-quotient claim.

The [raw result](d1_prescribed_edge_null_20260929.json),
[captured log](d1_prescribed_edge_null_log_20260929.txt),
[resource record](d1_prescribed_edge_null_resource_20260929.json) and
[probe](d1_prescribed_edge_null.py) preserve the calculation. It ran in
10.49 s at 206.12 MB process-tree peak under 180 s / 1 GB. Run source was
`46b9c80ea002b63bfa7377d478e8b0f43b548bc0` plus offline probe SHA-256
`ba5697b53e274841d0d038aa8483a77ff5f365c65a3ce196895ee21c5a5da62c`;
the saved pose SHA-256 was
`8293e528837cc2a8a25444aa079944c9f8371f5a5b50280bb6dc91816d19b852`.

## Decision boundary

The nine positive-support directions cannot be excused by declaring a
**physical** prescribed-edge quotient. An admitted profile with strictly
positive contact pressure through this clamped edge needs a changed discrete
method, such as a separately derived pressure stabilization or enriched
structural test space, with its own consistency, derivative and convergence
qualification. A bounded first handoff away from active clamp contact may
remain admissible if it explicitly excludes this case and independently
checks its actual active pressure space. The present finding does not prove
an instability in the saved right-side active set or the deformable-target
workflow, and it does not authorize dropping small positive supports.
