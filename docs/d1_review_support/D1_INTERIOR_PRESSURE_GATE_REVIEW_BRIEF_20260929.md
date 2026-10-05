# D1 interior pressure gate — review brief, not a frozen criterion

**29 September 2026.** This brief requests independent mechanics scrutiny
before a claim-bearing pressure gate is registered. It does not promote the
saved development runs or alter the Q1 pressure law. The retained cut-front
failure remains failed and belongs to D2.

## Precise proposed claim

For the planar, fully covered, small-motion Q4/S3 interior profile, test the
complete **signed interior Q1 pressure space** against admissible physical
source-normal displacement, while allowing all other structural variations
in the complete energy dual norm. The claim is confined to a registered
three-mesh family and its press/open/recontact poses. It is not a theorem for
arbitrary front cuts, warped surfaces, prescribed-normal source nodes,
finite-rotation tangents, or all structural boundary conditions.

Let `M=∫NᵀN dAref` on the full source patch, restricted to the pressure
modes under study. Let `Q` map one scalar displacement at each free interior
source node into its physical reference-normal translation in the actual
constrained structural coordinate space. Check `Q` against every support
and path control. At each pose, use the production physical gap derivative
to form `B=diag(S)D(gbar)Q`, and contact-free structural energy
`K=QᵀKstructQ`. Define

    A=M⁻¹ᐟ² B M⁻¹ᐟ²,    L=M⁻¹ᐟ² K M⁻¹ᐟ²,
    η=σmin(A),          κ=λmax(L)hmin⁴/D,
    γ=βfull² D/hmin⁴,   D=Et³/[12(1−ν²)].

The finite-matrix inequality `γ≥η²/κ` follows by restricting the
structural energy dual supremum to `range(Q)`. It makes no assumption
that the actual coupled Newton tangent is symmetric; `Kstruct` is the
separate contact-free symmetric material energy operator for the stated
elastic small-motion profile.

## Analytical reference and review questions

On a flat, fully covered reference patch with parallel skins and constant
gap, source-normal Q1 variation gives `B=M`: the source area and normal
have no first-order change in their normal component, and each normalized
weighted gap varies by the exact Q1 mass pairing. Thus `η=1` there.
For a planar affine Q4 cell with physical local spans `hx,hy`, the
independently checked E4-PL normal-motion block is

    Kij=As[(hy/hx)K1(ix,jx)M1(iy,jy)
            +(hx/hy)M1(ix,jx)K1(iy,jy)],

where `As=(5/6)Et/[2(1+ν)]`, `K1=[[1,-1],[-1,1]]`, and
`M1=[[2,1],[1,2]]/6`. The tensor-product generalized eigenvalue
bound is `λmax≤12As(1/hx²+1/hy²)`. For the registered square-XY
family of at most 0.25 m cells, a common reference slope only enlarges
the physical x span, giving `κ≤2100` at the coarsest width and less
on uniform refinement. [Element checks](d1_source_normal_q4_shear_20260929.log)
pass for slopes 0, `10⁻⁴` and 0.1.

Reviewer questions:

1. Are the physical work map and Q1 mass paired in exactly the stated
   reference measure for this full-cover profile, including the skin
   offset and movable interior active front?
2. Does the selected constrained source-normal subspace remain admissible
   and independent for every proposed path control and mesh?
3. Is the structural energy bound valid for the exact admitted E4-PL
   configuration at the assessed poses, and how should the tiny nonlinear
   geometric-stiffness correction be bounded or measured?
4. Is the same `D/hmin⁴` normalization and physical L² pressure norm used
   for the held-out positive-cut counterexample, without reinterpreting
   its historical failed result?

Four saved full-cover poses give `η=0.99999827–0.99999982` and
`κ=78.43–1386.40` under physical-normal source motion. These are
development readouts, not a criterion. The corrected positive-cut
`θ=.025` control has `γ≈0.0001579` under the same pressure/structural
norm family and scale; as the cut shrinks its ratio tends to zero.
[Constructive derivation](D1_INTERIOR_CONSTRUCTIVE_PRESSURE_BOUND_20260929.md),
[historical cut control](D1_INTERIOR_PRESSURE_STABILITY_CANDIDATE_20260929.md),
and the [two-hat derivation](d1_cut_front_two_hat_counterexample_20260929.md)
retain the supporting evidence.

## Prospective assessment design for review

One physically motivated candidate is to require `η≥0.9` (at most 10%
loss of the ideal mass pairing) and a verified `κ≤2110` (the exact 2100
linear bound with a separately justified nonlinear allowance). This would
give a certified finite lower bound `γ≥0.81/2110≈3.84×10⁻⁴`, while the
retained cut-front control falls below it. **These numbers are proposals
for review, not frozen acceptance criteria.** The 10%/allowance values
must be justified independently of the saved positive outcomes.

The claim-bearing family should use one fixed physical load definition,
exact source/target mesh identities and scales, at least three meshes,
full signed interior pressure rows including inactive modes, and actual
accepted press/open/recontact poses. Record `M`, `B`, `K`, singular/eigen
residuals, `η`, `κ`, the direct complete-space `γ`, supported modes,
contact geometry and source identity. Independently derive or check the
work block on representative rows. Preserve positive support; no
post-hoc pressure-mode deletion or changed law is permitted.

The new [exact Q1 manufactured interior case](D1_INTERIOR_MANUFACTURED_Q1_REFERENCE_20260929.md)
provides a cheap three-mesh analytical code-verification family with
1/9/49 active nodes. Its exact representability and very small errors do
not establish stability of the *full signed* pressure space or spatial
accuracy of a deformable two-body engineering case. The pressure gate and
the 2% response gate remain separate.
