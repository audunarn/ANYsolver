# Parent analytical review: admitted local laws

State: local potentials verified in source; awaiting worker checkpoint before
adopting the complete numerical contract. No numerical commands performed.

Actual solver dispatch: nonlinear_static.py:1507-1525 invokes the generic
corotational wrapper. Its input d(u) is a reference-coordinate nodal vector;
the native element applies its fixed T0/T frame internally. Do not apply those
fixed transforms twice when deriving B.T f_local.

For classical elastic Beam2 with the native von-Karman local route (NOT the
direct element corotational option, fiber or generalized section),
elements.py:4620-4664 gives

    W_local(v) = .5*v_loc.T K_noax v_loc + .5*EA*L*eps(v_loc)^2,
    eps = du/L + (dv^2+dw^2)/(2*L^2), v_loc=T0*v.

The returned T0.T f_loc is its gradient and the returned local tangent includes
the strain-gradient outer product and axial-force geometric second derivative.

For isotropic elastic Q4, no section/history/initial fields,
elements.py:2872-3229 gives membrane von-Karman strain, linear curvature,
through-thickness elastic resultants/moduli, and independent shear/drilling
quadrature. The local potential is the integral of .5*strain.T C strain,
including thickness/layer weights, plus shear and drilling quadratic terms.
Its force is the derivative through the nonlinear membrane strain, and its
tangent includes the material and geometric terms. Any active stabilization
must be included; do not silently disable a term to obtain a potential.
This is a source conclusion, not evidence that an implemented independent
energy oracle is already correct.

For these admitted conservative local laws, W(u)=W_local(d(u)) has gradient
B.T f_local and Hessian B.T K_local B+sum_a f_local[a] Hessian(d[a]). The full
map includes extracted-frame motion (both translations and beam twist). The
right/left SO(3) coordinate Jacobians alone do not account for that motion.

Derivatives of this composed potential establish work conjugacy to additive
coordinates. Objectivity is a separate requirement: if the existing frame
makes W_local(d(u)) vary under a superposed rigid rotation at nonzero local
deformation, a force pullback alone cannot fix it. Such a defect requiring a
different frame is the user's explicit STOP. It warrants an early fixed
energy-objectivity check before extensive force/tangent integration work.

Spatial nodal moments corresponding to generalized covectors p_theta obey
M_spatial = (R_node*J_right(theta))^(-T) p_theta. Translation force blocks are
unchanged by this coordinate/spin conversion. No global claim about the old
rotated-residual profile's energy gradient or Hessian is adopted here.
