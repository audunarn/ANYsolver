# Independent pairing review — source/equations only

Status: pending Mistral gate reconciliation; not implementation authority.
No numerical evaluations performed. HEAD recorded in baseline.json.

## Production evidence

nonlinear_static.py:1507 calls corotational.corotational_element_response,
not BeamElement._compute_corotational_nonlinear_response directly. The wrapper
computes local deformation via Log(R_rig.T Exp(theta)) and returns E f_ref.
corotational.py:383-405 / corotational_performance.rotate_corotational_force_blocks
rotate translation forces AND moment blocks by the same extracted rigid frame.
corotational.py:583-644 differentiates that spatial residual with respect to
additive rotation-vector coordinates, including the right-Jacobian and frame
sensitivity. Derivative consistency alone is not coordinate work conjugacy.
The current solver uses a fixed affine displacement transformation and T.T
residual projection. Neither is a ready nonlinear attachment implementation.

## Candidate narrow conversion to examine before declaring STOP

For R=Exp(theta), spatial spin delta omega = L(theta) delta theta, with
L(theta)=R Jr(theta). Jr already exists in corotational.py:491.
Let A(u) be block diagonal: identity on translations, L on rotation blocks.
If existing rotated moments are spatial resultants, the additive-coordinate
covector is p=A.T s for full spatial force/moment residual s. Its Jacobian is
Kp=A.T Ks + d(A.T)/du applied to s, where Ks is the existing exact derivative
of s. Then r=J.T p, K=J.T Kp J + sum_a p[a] Hessian(g[a]).

This conversion leaves unconstrained physical equilibrium unchanged where A
is invertible. It changes neither local element strain laws nor element output
force conventions. It would be restricted to the new opt-in profile only.
It is not permission to declare an energy Hessian, symmetrize tangents, change
the existing element formulation, or broaden admissible mechanics.

The attachment's physical virtual-work map gives slave translation variation
delta x_b=delta x_s+delta omega_s cross (R r0), and equal spatial spin.
Thus shell receives F_b and M_b+(R r0) cross F_b as physical resultants.
Both physical-resultant and additive-coordinate covector checks are required;
testing J.T algebra against itself cannot establish this pairing.

## Discriminating exact counterexample to naive J.T of spatial residual

Take theta=alpha ez, r0=a ex and slave F=f ez, no slave couple.
Physical moment is af(sin(alpha),-cos(alpha),0).
Derivative of slave position with respect to additive theta produces
af((1-cos(alpha))/alpha,-sin(alpha)/alpha,0), a coordinate covector.
They differ for nonzero alpha. This difference is a coordinate distinction,
not itself an element defect. Mixing that covector with unconverted spatial
shell/beam moments cannot prove common-origin physical moment balance.

## Remaining adoption question

Does the actual Q4/Beam2 production route establish the spatial-resultant
interpretation strongly enough for this narrow conversion, and can an isolated
map/force adapter integrate without a new general constraint solver? If not,
apply the user's compatibility STOP; do not select an interpretation solely
because it allows implementation. Mistral findings must be checked against
the actual wrapper dispatch and cannot be based only on the direct beam helper.
