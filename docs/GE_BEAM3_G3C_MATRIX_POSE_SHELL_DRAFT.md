# G3c matrix-owned shell chart: draft next gate

Draft only. Preserve all accepted sources/evidence, all five graphs and25
variants, all frozen sections, reference normals, joint port frames, tolerances
and execution bounds. No public Q4/S3 change or complete graph authority.

Candidate policy: GE_BEAM3_G3C_MATRIX_POSE_SHELL_PULLBACK_V1.
Use unchanged _ge_beam3_variational_shell.rotation_jets(X,x) for equal-weight
proper positional Procrustes R. Trial physical nodal matrices are
Q_i=Exp(eta_i)*Qaccepted_i, never Exp(accumulated rotation vectors).
Build all first/second derivatives from one captured owned X,u,eta,Qaccepted:
d_ti=R^T(x_i-xc)-(X_i-Xc), d_ri=Log(R^T*Q_i).
Keep reference geometry, physical material axes and owner normal fixed.
Only a simple top Davenport eigenpair is required; repeated lower eigenvalues
are admissible. Retain the source top-gap guard and0.9pi relative Log domain,
and the accepted trial-increment cutback policy. Nodal pair angles do not
replace fit-to-nodal Log admission; do not add a different pairwise cutoff.

For actual local force f and tangent K, g=D^T*f and
H=D^T*K*D+sum(f_j*Hess(d_j)). P=diag(I,Jleft(eta)); solve P^T*r=g and
P^T*J=H-(dP)^T*r. Use analytic source derivatives, no numerical frame
differentiation, symmetrization, rotated-force shortcut or old raw chart tangent.
Rebase eta to0,Qaccepted toQtrial only after acceptance. At the same physical
pose local d and actual material-origin/candidate identities must not change.

Common physical motion holds X fixed, x*=W*x+t,Q*=W*Q and R*=W*R, giving
invariant d. Passive coordinate re-expression instead transforms X/material
normal and conjugates Q/R. Simultaneous connectivity permutations leave R
invariant and use actual Q4/S3 local transforms. Never derive graph port D0
from a newly numbered first edge. Physical director reversal is not numbering.

The first local implementation owns only a closed homogeneous elastic scalar
definition and constructs fresh real element/model/material and the correct
family-specific virgin origin. No caller model, cache or state is borrowed.
Q4 initialization and S3 model-bound initialization are distinct. Returned
actual trial state is detached diagnostic data, not an accepted graph commit.
Before global ownership, freeze accepted-origin authentication, per-family
preparation and replay; do not assume virgin-origin local checks prove them.

## Physical recovery/potential question that must be resolved before freezing

Q4's actual nonlinear force is the inherited nonlinear force plus the constant
qualified-minus-inherited-reference correction. Its existing planar mixed-field
compute_stresses is linear in d. Do not pass that baseline off as a complete
finite work-conjugate physical recovery or change the existing public recovery.
For the admitted elastic no-initial-field route, the source suggests
U_Q(d)=0.5*d^T*K_Q*d + sum_g w_g*(0.5*eps_vk^T*A*eps_vk
-0.5*eps_lin^T*A*eps_lin), because unchanged linear bending/shear/drill terms
cancel. Confirm this against the actual source and independent derivatives.
Baseline mixed physical/numerical energy and nonlinear membrane increment
must remain separate channels. A naive sum of membrane resultants contracted
with one B_eff is not established by this energy identity. Freeze an honest
multi-channel physical/work interpretation or preserve an explicit blocker.
No new physical constitutive matrix or empirical correction is authorized.

For S3 verify its actual homogeneous elastic native route and actual physical
resultants, numerical PL exclusion and canonical station ordering. Do not
import Q4 recovery or native beam shear/reversal conventions into S3.

## Required checks

Independent Kabsch and Rodrigues value reconstruction; exact-reference actual
operator/null modes; all first/second maps and actual residual/tangent at every
h=1e-4,1e-5,1e-6. Use square/rectangle and right/equilateral triangle, noncommuting
accepted/trial rotations, all source D4/D3 numberings, passive proper transform,
common arbitrary/pi/1.4pi motions, and repeated lower eigenvalues. Explicitly
test top-fit degeneracy and no family evaluation after failed guards.
Compare old/new physical-pose values where independently known total-angle
coordinates exist, transporting derivatives rather than comparing raw charts.
Check caller mutation, nonfinite contractions, normal/section/origin mismatch,
immutable outputs, physical/numerical separation and unchanged-pose rebase.

Follow with complete mixed graph ownership, actual source stationary native
blocks, joint multiplier work, all25 variants, transactions/restart and two
formal cycles only after candidate/runner freeze. No local-only substitute.
