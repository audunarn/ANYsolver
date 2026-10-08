# B3 GE E4 PL F03 local classical work identities

This is a synthetic identity oracle on four conforming rectangles covering
`[-1/2,3/2] × [-1/2,1/2]`. Each component uses the same nodal values on
shared Qp edges, p=1,2,3. Thus displacement and virtual test fields are C0,
but their derivatives and stresses need not be continuous. The membrane stress
is `T = represented(thickness) × represented(plane C) × engineering strain`;
the two represented factors are lifted independently to exact Fractions.

Let the normal on an internal edge point from its minus cell to its plus cell,
and define `j=(T_plus−T_minus)n`. Summing the exact cellwise divergence
theorem gives

`a_s(u,z) = −∑cells ∫(div T)·z + ∫supported Tn·z + ∫free Tn·z −∑internal ∫j·z`.

For the physical finite-square interface measure μ, the same virtual work
is obtained either by integrating its spatial area force `f_μ` over the
panel or integrating `μ·A z` over moving square pads in station s and over
the two endpoint pad footprints. The independent routes clip in different
orders. With `r=div T+f_μ`, their equality yields

`<μ,A z>−a_s(u,z) = ∑cells ∫r·z +∑internal ∫j·z −∫free Tn·z −∫supported Tn·z`.

The final term vanishes for a supported test. For a general edge lift,
`R(z)=∫supported Tn·z+∫free Tn·z−∫r·z−∫j·z=a_s(u,z)−<μ,A z>`.
The left/right lift weights `(1.5−x)/2` and `(x+.5)/2` add to one; no beam
slope support is introduced. For an origin rotation `z=(-y,x)`, the pad
translation is `(0,s)` and the pad yaw is `J_geom/J`, retaining the held
binary64 J. Hence its interface work includes the line moment and **both**
endpoint atoms exactly once. Virtual rotation yields Nm about (0,0).

The current `Load` admits constant line-density triples and the two endpoint
atoms only. These identities are not yet a verification of a general
piecewise-polynomial or cosine recovered multiplier field.

The oracle performs rational polynomial integration over a fixed 2×2 panel
patch. It does not construct an equilibrium, a local stiffness matrix, a beam
response, a scientific reference, or a qualification decision. Rectangular
pad clipping and the four-cell boundaries are exact represented-rational
geometry; it does not cover curved or inclined cells.
