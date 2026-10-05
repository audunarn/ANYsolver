# D1 pressure-work repair: bounded method decision

**29 September 2026. Development decision; no production law changed.** The
[two-body counterexample](d1_cut_front_two_hat_counterexample_20260929.md)
rules out cut-uniform stability of the unchanged fine-Q1 pairing for its
admitted touching 8-Q4/2-S3 family. This record compares two repairs without
changing D1 breadth, pressure positivity, acceptance gates or historical
evidence.

## Question and discriminators

Can a repair retain every supported fine-Q1 pressure hat, represent physical
Q4/S3 work and avoid domination of the small positive cut by a numerical
term? The bounded alternatives were (1) a conforming transverse source-shell
displacement bubble in the physical energy and skin map, and (2) a full
reference-edge pressure-gradient-jump term restricted to supported hats.

An independent planar Q1 screen
([script](d1_jump_stabilization_screen.py),
[raw output](d1_jump_stabilization_screen_20260929.json)) constructs the
second form from exact two-point edge integration. It is positive
semidefinite and annihilates constant, x, y and xy pressure to approximately
1e-15 matrix-vector norm. For the proven two-hat direction, its quadratic
form is 1.56459, 1.56279, 1.56239 and 1.56229 m² at cut fractions .1,
.05, .025 and .0125, respectively. The *physical* discrete work is O(θ³)
and an admissible continuum work is O(θ²). Thus this particular fixed-weight
full-reference term stays O(1) while contact work vanishes. It would
penalize pressure extended through an uncontacted cell and change the active
gap/complementarity equation. It is **not adopted**. The script is retained
as a rejected method screen, not a solver test or acceptance result.

Two bounded independent mechanics reviews initially found a physical shell
displacement bubble to be the credible next candidate. On source cell
x∈[.5,1], y∈[0,1], use `B=16ξ(1−ξ)y(1−y)` in transverse position, with
zero added director rotation. The exact pressure work for the counterexample
is `c1 β/36 = −c1 θ²/18 + O(θ³)`. The bubble vanishes on that element's
boundary, lies away from the clamp, and has finite θ-independent *raw*
Mindlin shear energy. It detects the exhibited weak pressure direction at the
kinematic level. This is evidence for **one mode only**, not a uniform
inf-sup proof.

The production E4-PL compatible MITC shear operator samples only
`∂r B(0,±1)` and `∂s B(±1,0)`. These are exactly zero; flat-shell membrane,
bending and drill strain of this pure transverse bubble also vanish.
Consequently, appending it to the existing Q4 operator gives `K_bb=0` and
cannot be condensed. An independent reviewer confirmed this formulation
objection. The [algebraic screen](d1_q4_bubble_energy_screen.py) measures
13,675.2137 N/m raw shear stiffness but zero assumed-shear stiffness for
the specified cell and material. Its [initial output](d1_q4_bubble_energy_screen_20260929.json)
mislabels the force coefficient's units; the [corrected output](d1_q4_bubble_energy_screen_v2_20260929.json)
labels it m² per Pa. The initial artifact is retained as failed unit evidence.
The [production source-field check](d1_q4_bubble_energy_screen_v3_20260929.json)
also integrates raw bubble shear against E4-PL's actual stationary shear
stress sources and obtains 1.39e−17 coupling norm. Thus adding only a raw
compatible bubble to the unchanged E4-PL stationary fields is also
insufficient; its stress space must be enriched.

An exploratory **MITC4+/D scalar-reference** strain interpolation keeps its
nodal strain and adds the bubble's raw physical shear gradient. The
[fixed-pose block probe](d1_q4_bubble_block.py) used 3×3×2 quadrature
on the source cell and stitched the new bubble block to the assembled
8-Q4/2-S3 structural stiffness. Its 3.93e−16 nodal parity compares only
two integrations of that scalar reference, **not the production Q4**.
The reference `K_bb` and stitched `S_b` are both 13,675.213675 N/m. The
stitched bubble contact force divided by θ² is
−0.0130677, −0.0154809, −0.0170771 and −0.0180120 at θ=.1,.05,.025,.0125;
the exact limit is `−c1/18 ≈ −0.01906`. The four
[development raw records](d1_q4_bubble_block_theta005_v2_20260929.json)
have distinct θ files. Their bubble-to-existing-nodal squared dual-response
ratios are only 0.0037%, 0.0168%, 0.0710% and 0.2925% at those cuts,
respectively. The mode is asymptotically detected, but this preflight does
not show a material change to current finite-cut coupled results. The first
.05 output was written before a reporting
KeyError and is retained as failed process evidence. The positive raw-shear
stiffness is derived rather than an arbitrary spring, but the default Q4
uses a **different** 35-field stationary E4-PL formulation, PL/hourglass
terms and `5/6 Gt` shear. The scalar reference uses `Gt`. An independent
audit invalidated this stitched block as a coherent production preflight.
Its Schur values cannot direct production integration. Retain all outputs
as failed formulation-identity evidence.

The next [version of the same preflight](d1_q4_bubble_block.py) now extends
the **production E4-PL** 35-field stationary system by one matched shear
stress mode and one generalized-strain mode corresponding to the raw bubble
gradient. It retains the original nodal coupling and condenses the expanded
37-field system. On this flat cell, its nodal 24×24 core agrees exactly with
`QualifiedE4PLShellElement.compute_stiffness_components()["core"]`; the
new `K_bb=S_b=11,396.011396 N/m`, using the production `5/6 Gt` shear. The
condensed bubble force divided by θ² is −0.0130677, −0.0154809,
−0.0170771 and −0.0180120 at θ=.1,.05,.025,.0125. See the
[θ=.05 raw record](d1_q4_bubble_block_theta005_v3_20260929.json) and the
other `_v3` θ records beside it. The v2 records remain the failed reference
comparison. This is a fixed-pose *new mixed-element candidate*; its
physical contact geometry, derivative and state do not exist yet. A
matching stress/strain extension is essential: the original stress space
is orthogonal to the bubble. Independent audit of this corrected block is
complete for its flat fixed-pose algebra: the 37-field signs, coupling,
production nodal-core identity and `5/6 Gt` stiffness were checked. The
review does not assess a coupled or moving-contact implementation.

## Next integrated candidate

The corrected mixed block passes its flat-cell nodal identity and positive
energy preflight under independent design scrutiny. Next derive and version an
enriched E4-PL stationary/physical-skin profile;
retain the original Q4 identity and nodal equations. The contact residual
and tangent must include bubble coordinate, moving overlap, support and both
body work. Keep the bubble coordinate in the coupled solve initially. A later
condensation must use the complete structural-plus-contact matrix and
recover bubble state. The existing nodal-position-only patch manager cannot
implement this by adding a matrix row after geometry evaluation. Test
virtual work, tangent, constant/affine traction moments, rejected trials,
restart identity, changing fronts, pressure stability and unchanged D1
response/gap gates. The new structural interpolation itself needs thin-shell
and patch checks before acceptance. An equally defensible cut-aware
subscale repair may be compared if derived from a complete physical
equilibrium block; a pressure-only penalty is insufficient. Do not replay
expensive coupled refinements before a complete candidate exists.

An enriched surface with nonzero interior bubble displacement is no longer
the existing bilinear Q4 skin. It must have a separate formulation/capability
identity; the current D1 requirement for qualified bilinear Q4 is not
silently satisfied by it. Conversely, enriching only the internal E4-PL
stress/strain fields leaves the contact work map unchanged and cannot repair
the pressure counterexample. The D1 method choice is therefore still open.

A recent [primary mortar-stabilization study](https://arxiv.org/html/2603.18905v1)
adds traction jumps to its constraint equation and scales them by a local
Schur estimate. The authors explicitly note that this changes constraint
enforcement and can smooth tractions excessively if mis-scaled. Its
piecewise-constant 3D fault multipliers and fixed macroelement analysis do
not establish consistency or cut-uniform shell pressure stability for
ANYsolver's moving Q1 shell mortar; this is only a method lead.

The reviews are design scrutiny, not independent milestone acceptance.
The fixed-weight jump screen and unqualified bubble proposal do not close
any D1 gate. Complete-route speed and memory are unmeasured for either.
