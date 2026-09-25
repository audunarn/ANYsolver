# C1 internal development kernel: moving S3/S3 pointwise energy

`MovingS3PairPenalty` in `triangle_pair_energy.py` is an internal verification
specialization for two explicitly supplied physical S3 triangles. Each of
their six nodes may translate independently. The distinct development static
route in [GENERAL_CONTACT_C1_GENERAL_S3_STATIC.md](GENERAL_CONTACT_C1_GENERAL_S3_STATIC.md)
now composes this kernel with physical S3 skin work maps. Neither the kernel
nor that route is the selected primal-pressure mortar law.

For current source and target positions projected along the current source
normal, the kernel clips their common triangle overlap at the affine normal
gap (g=0). It integrates the squared closed gap exactly over the active
polygon. The scalar work is

\[
E_c=\tfrac12\epsilon_n\frac{A_{s,0}}{A_s}
    \int_{\Omega_s\cap\Omega_t}\langle-g\rangle_+^2\,da,
\]

where (A_{s,0}) is source reference area and (A_s) its current area. This
keeps the declared source reference-area measure under arbitrary affine S3
motion. The active area and independent minimum represented gap are reported
separately. There is no pressure-space interpolation or augmented multiplier
in this specialization.

The local 18-coordinate residual and smooth-branch tangent differentiate
that same energy by centered differences with an explicit dimensional step
and a finite evaluation budget. Current face inversion, conflicting
polarity, overlap/contact branch changes and coincident-edge derivative
kinks fail explicitly. These checks do not certify every possible projection
branch switch. The separate static development owner adds conservative swept
control and restart; Q4 bilinear geometry remains unimplemented in this route.

`tests/test_general_contact_triangle_pair_energy.py` covers an independent
constant-gap reference-area integral, exact partial-contact affine-gap
integration, nonuniform in-plane nodal motion against analytic polygon
clipping, common-translation invariance, force/moment balance, a smooth
directional tangent and explicit kink/resource rejection. Five focused tests
passed in `c1-general-s3-energy-final1.txt`. This is development evidence,
not C1 engineering acceptance or a public capability.

## S3 V2D physical-skin work map

`S3SkinWorkAdapter` reads the exact S3 V2D formulation, its physical director
and its signed material-surface offset. It maps the solver's translational
and small-rotation nodal coordinates to the selected top, middle or bottom
skin. The sparse linear work map pulls physical contact force and tangent
back to the authoritative structural DOFs, including offset force couples.
A pure drill rotation about the physical director leaves the skin and its
contact work unchanged.

The local pair test maps the moving-triangle energy through two actual S3
elements. It checks formulation-owned top/middle/bottom positions against a
separate geometry adapter, nonzero offset couples, drill invariance, global
virtual work and a smooth directional tangent at relative error at most
`1e-5`. Together with the energy tests, seven checks passed in
`c1-s3-skin-energy-final1.txt`. The adapter alone does not admit a contact
solve; the separate S3 static development profile now connects it to the
nonlinear owner, with its own validation and limitations.
