# D1 interior pressure work — constructive source-motion bound

**29 September 2026. Development discriminator, not qualification.** Source
`712d2bd1` plus the bounded readout change in
[`general_contact_d1_interior_work_spectrum_dev.py`](../../scripts/general_contact_d1_interior_work_spectrum_dev.py).
The [raw four-pose result](d1_pressure_constructive_bound_20260929.json)
used the already retained accepted 16/32/64/128-Q4 interior presses. It
completed in 30.98 s/240 MB under 180 s/1 GB. No production contact law,
structural model, accepted pose or historical gate changed.

## Question and exact finite inequality

Does the full-cover pressure space lose contact work against *free source
vertical motion*, or does the observed minimum mainly reflect the source
structural energy norm? Use the same interior pressure indices and exact
reference Q1 mass `M` as the prior [pressure candidate](D1_INTERIOR_PRESSURE_STABILITY_CANDIDATE_20260929.md).
Let `Q` select actual admissible interior source vertical DOFs after the
structural constraints and path controls. Set

    B = diag(reference_support) D(gbar) Q,
    K = Qᵀ K_struct Q,
    A = M⁻¹ᐟ² B M⁻¹ᐟ²,
    L = M⁻¹ᐟ² K M⁻¹ᐟ².

For every signed pressure combination, the physical contact-work dual norm
over the complete constrained two-body structural space is at least its norm
on `range(Q)`. By the smallest singular value and largest eigenvalue,

    β_full² ≥ β_Q² ≥ σ_min(A)² / λ_max(L).

With `D=Et³/[12(1−ν²)]` and the source minimum cell width `h`, define
`η=σ_min(A)` and `κ=λ_max(L)h⁴/D`. Then the **finite** dimensionless lower
bound is `γ_full ≥ η²/κ`. This is a constructive inequality; its scaled
value is not a mesh-family acceptance threshold by itself.

| Source Q4 faces | Interior modes | `η` | `κ` | Constructive `η²/κ` | Actual restricted `β_Q²D/h⁴` |
|---:|---:|---:|---:|---:|---:|
| 16 | 9 | 0.999999830 | 1386.396 | 0.0007212943 | 0.0007212946 |
| 32 | 21 | 0.999999220 | 277.973 | 0.0035974716 | 0.0035974778 |
| 64 | 49 | 0.999998984 | 469.295 | 0.0021308497 | 0.0021308544 |
| 128 | 105 | 0.999998294 | 78.435 | 0.0127494172 | 0.0127494629 |

The work factor remains within 1.71e−6 of unity. At these saved full-cover
poses, pressure work against a source vertical Q1 motion is effectively its
ordinary Q1 mass pairing; no near-null contact-work direction appears in
this source-motion subspace. The variation of the scaled lower bound is
almost entirely in the structural stiffness factor. Earlier independent
clipped frozen-footprint calculations agreed with the same restricted work
to at most 1.88e−7 relative, but they do not validate all moving geometry.

## Analytic source-energy screen

For a flat, uniformly meshed E4-PL Q4 source with only nodal vertical motion
and zero director variations, the element's actual four-by-four vertical
stiffness equals `As` times the exact tensor-product Q1 gradient matrix,
where `As=(5/6)tE/[2(1+ν)]`. The independent closed matrix for a square is

    [ 2/3  -1/6  -1/3  -1/6 ]
    [ -1/6  2/3  -1/6  -1/3 ]
    [ -1/3  -1/6  2/3  -1/6 ]
    [ -1/6  -1/3  -1/6  2/3 ].

The two-point 1D Q1 mass/stiffness generalized eigenvalues are `0` and
`12/h²`; the two-dimensional tensor sum is therefore bounded by
`12/hx²+12/hy²`. Element assembly preserves this upper Rayleigh bound for
the global source-vertical subspace, including essential boundary
constraints. On a square mesh this yields

    κ ≤ 24 As h² / D.

For `E=10⁵ Pa`, `ν=0.3`, `t=0.05 m` and the coarsest family width
`h=0.25 m`, the right side is **2100**. Its value decreases with h for
uniform square refinement. Four focused local controls at `h=0.25` and
`0.0625 m` reproduce the exact flat matrix to roundoff. At the family's
common slope `10⁻⁴`, the local generalized stiffness exceeds the flat
bound by only `7.1×10⁻⁹` relative; the numerical check permits `10⁻⁷`.
The inclined contribution needs an explicit constitutive upper-bound
derivation before using **2100** as a rigorous family constant.

For illustration only, a future **independently justified** admitted-work
condition `η≥0.9` together with a rigorously enlarged stiffness bound near
2100 would imply a scaled dual lower bound near `0.81/2100 = 3.857×10⁻⁴`.
This number was derived from the element identity and a proposed 10% work
retention margin; it is **not** a frozen acceptance threshold. The retained
positive-cut `θ=0.025` control has `γ≈1.58×10⁻⁴`, below that illustrative
bound, while the full-cover development cases are above it. [Four focused
source-energy checks](d1_source_q4_shear_tilted_20260929.log).

## Decision and limits

This makes a sharper prospective path than another coupled mesh sweep:
derive a mesh-independent upper bound for `κ` from the **qualified** Q4
source element energy and stated shape-regularity restrictions, and a
full-cover physical-work lower bound for `η` under the admitted small-motion
geometry. The retained positive-cut two-hat case must fail the corresponding
work factor or scaled bound, so the measure cannot pass an excluded unstable
family. An independent reviewer must check the derivation and the chosen
physical norms before any threshold is frozen.

The four input poses use mesh-index load weights, refine the target only
from two to four S3 faces, and have one active pressure node each (the
full signed interior spaces were analyzed). They do not establish a
uniform theorem, active-front stability, spatial response convergence or
acceptance. A formal three-mesh family still needs prospective loads,
target refinement, open/recontact states, reference accuracy and criteria.
