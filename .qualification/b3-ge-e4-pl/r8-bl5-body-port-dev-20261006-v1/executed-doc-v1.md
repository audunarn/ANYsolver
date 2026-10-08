# BL5 saved-density body-port development discriminator

This distinct ordinary DEV probe uses the immutable installed native wheel
`b3d5f572797f3c2954d1bf9dc1c6b4293da14c5812e543dbde7f314a60207291` and
the saved weak C3D20 response. It does not replay either coupled native calibration
or CCX. Historical integration `fdd5c9dd` defines applicability; changing working
product source is not represented as the imported solver. Physics and scientific
acceptance remain reserved to the root owner.

The specimen, +1 N global tip Fz, shell clamps, section data and virgin physical
fibre material are unchanged. Four .25 m P0 supports integrate five channels.
Position rows have units m² and director rows m; their densities have units N/m
and N. Native gap polarity is opposite continuum polarity. At saved continuum
algebraic density lambda_r, physical body loads are
`ell_ref = f - C_ref.T lambda_r` and
`ell_native = f + C_native.T lambda_r`.
The action identity is checked on the previously proven globally representable
supported affine/material-director/rigid bar-section subset. It does not assert a
mapping of arbitrary broken native cell rotations into the continuum field.

Recover continuum shell/beam paired work and energy from saved full K/U, plus all
eight Gauss point face gaps. Zero P0 integrated gap does not imply zero point gap.
For native, solve one RHS per body with the complete unchanged mixed operators.
The shell retains original clamps. The free beam must first have zero work on all
six physical rigid fields, including retained cell spins; otherwise withhold the
solve. Use the explicit gauge `G q=0`, `G=R_rigid.T`, in an indefinite KKT system.
No load projection, artificial stiffness, physical beam support or condensation
is allowed. Reverse congruence scales into physical q/gauge covectors.

Compare body work `W=ell.T q`. Native beam section energy is recovered from the
actual virgin section at retained p after verifying reference-linear material
stationarity `J q_pose = grad Psi*(p)`. The mixed potential `p.k-Psi*(p)` and raw
negative resultant subblocks are not physical stored energy. The finite pose
law is not evaluated as though a reference-linear increment were a finite state.

Before execution, criteria are fixed: original scaled equilibrium and relative
work <=1e-8; physical wrench and gauge covector <=1e-8 at 1 N/1 Nm floors;
work denominator `max(abs(ell.T q),1e-12 J)`; material compatibility and pose gauge
<=1e-9 with reference length1 m. Actual material domain guards remain active.
Full unscaled residuals, physical q, gauge reactions, retained p/strain/resultant
fields and failed calculated diagnostics are preserved. Resource bounds are
600 s/2 GiB process tree, affinity1, effective pools1, JIT off, unforced backend.

Excess beam-port work directs beam/section/trace inspection; excess shell-port
work directs shell/body/trace inspection; comparable work suggests interface
redistribution requires examination. These are effective port compliances, not
isolated constitutive laws. No coupled native response, accuracy, convergence,
inf-sup, release or different-family scientific acceptance follows from this
discriminator. No automatic refinement or new interface basis selection follows.

Implementation prepared; numerical checks and outcomes pending shared-slot grant.
