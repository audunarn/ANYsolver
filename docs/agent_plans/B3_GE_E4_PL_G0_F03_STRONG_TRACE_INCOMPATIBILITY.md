# F03 planar strong-trace incompatibility on finite Q4/S3 hosts

21 September 2026. **A local linearized derivation, not qualification of a
multiplier space.** It addresses a proposed diagnostic that would enforce
every polynomial coefficient of the beam/shell trace gap exactly on every
overlay interval. Such a system is not a valid replacement for the weak
line law in the current finite trial spaces.

At a fixed y sample, the planar Q4 physical displacement trace is affine
in x within a host; the S3 trace is affine within each triangle. The
linearized centered four-sample centroid and proper-fit yaw are weighted
sums of those traces. On any open material interval that remains within
all four host cells/triangles, both the shell transverse position `v_s(x)`
and fitted yaw `θ_s(x)` are affine. This is a statement about the admitted
finite trace map, not a claim that an actual shell's continuum rotation
must be affine.

For a conventional, homogeneous exact-static Timoshenko beam element of
length `h`, let endpoint transverse positions and rotations be
`(v0,θ0),(v1,θ1)`, bending rigidity `EI>0`, shear rigidity `GA_s>0` and
`D=h³/(12EI)+h/(GA_s)>0`. The internal constant shear is

`V = [v1-v0-h(θ0+θ1)/2]/D`.

With local coordinate `x∈[0,h]`, its homogeneous field is

`θ_b(x)=θ0+(θ1-θ0)x/h+V(hx-x²)/(2EI)`,

`v_b(x)=v0+θ0 x+(θ1-θ0)x²/(2h)`
`       +V[h x²/(4EI)-x³/(6EI)+x/(GA_s)]`.

Suppose *strong* equality `θ_b=θ_s` and `v_b=v_s` holds on any nonempty
open overlay interval. Polynomial identity and the affine shell yaw make
the beam yaw's quadratic coefficient `-V/(2EI)` vanish: `V=0`.
The beam transverse field's quadratic coefficient then becomes
`(θ1-θ0)/(2h)`; affine shell position requires `θ1=θ0`.
The shear equation with `V=0` gives `v1-v0=h θ0`. Thus the beam element's
bending curvature and transverse shear both vanish, leaving only a
transverse rigid-body field on that element. Matching all polynomial gap
coefficients at a fixed finite mesh would suppress the very bending and
shear response that the coupled structure must carry. With the currently
clamped beam root and connected homogeneous elements, continuity then
propagates zero transverse beam motion across the chain. This is a
local discrete-field incompatibility. A beam field including particular
solutions from distributed loads and interface tractions requires its own
analysis; the homogeneous polynomial proof must not be applied to that
different field without derivation.

This result does not forbid a continuum bonded connection or establish
that a weak exact-multiplier discretization must lock. It rules out a
finite-element *strong coefficient tie* as an independent physical oracle
for this planar four-sample trace. Finite-station ties avoid these exact
polynomial restrictions but permit off-station gaps; the v4 screen measured
such gaps. A finite spring samples the full line but changes its law; the
v1 penalty sweep remained stiffness dependent. The next admissible F03
candidate needs a genuinely distinct, stable weak test span and an
independent physical response comparison, not stronger pointwise rows.

The derivation is limited to the small-strain planar Q4/S3 in-plane trace
and conventional exact-static beam field. The actual native retained B3,
finite pose, eccentric torque, shell drilling/director and shear tests
remain separate mandatory foundations.
