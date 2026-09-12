# G3c matrix-owned shell local contract

Policy: `GE_BEAM3_G3C_MATRIX_POSE_SHELL_PULLBACK_V1`.
Base: `44dc811ccf620536216c8bc97c2930f2502454b4`, tree
`624ecc2bc931c5467f59a1cb74c5ff71f1b5efce`.

This is a source-equation freeze requiring independent review before private
implementation. It grants no mechanics result, public routing, graph closure,
full parity or release authority. The original G3c PHYSICAL_RECOVERY obligation
is NOT discharged by the work-channel interpretation below. The conventional
single-field finite Q4 recovery question remains explicit and unresolved; a
local pass cannot silently waive it in final G3 adjudication. Accepted B2/B3
evidence and the earlier inherited-frame blocker remain immutable.

## Admitted local scope and ownership

Only actual qualified planar Q4 and S3 V2D, homogeneous scalar virgin elasticity:
E=100, nu=0.25, thickness=0.1, three thickness layers, zero yield stress,
no hardening, generalized section, initial fields, offset, activity/deletion,
loads, contact, external cache or caller-owned material/state. Physical normal
and material direction are immutable definition inputs. The frozen graph shell
fixtures are retained. Four local shape fixtures supplement, not replace, them:
Q4 square [(0,0),(1,0),(1,1),(0,1)], rectangle with x doubled; S3 right triangle
[(0,0),(1,0),(0,1)], equilateral [(0,0),(1,0),(1/2,sqrt(3)/2)], all z=0.

A new private facade owns canonical sealed definition bytes and read-only
detached outputs, rejects write/delete/re-entry tampering, and captures owned
binary64 X,u,eta,Qaccepted once. Proper Q matrices and all intermediate/result
arrays and scalars must be finite before comparisons. Reject unsupported input
before family evaluation. Build a fresh actual mesh/material/element and its
family-specific virgin origin each trial: Q4 init_nonlinear_state(3), S3
init_model_bound_nonlinear_state(mesh,material,3). Seal the detached returned
family candidate in its local-d convention. No commit, caller origin, restart,
accepted history, or global graph ownership is implemented in this local gate.

## Complete matrix chart

Q_i=Exp(eta_i)Qaccepted_i. Rotational vectors are trial increments, not accumulated
state. Require each increment norm <0.9*pi. Reuse the unchanged analytic
rotation_jets(X,x), x=X+u_translation, for equal-weight positional proper
Procrustes R. Preserve its simple-top Davenport guard
gap>1e-11*max(tiny,max(abs(eigenvalues))); repeated LOWER eigenvalues are valid.
Do not add a shell all-pair nodal Log guard. The source-required Logs are
Log(R^T Q_i), each <0.9*pi; degenerate top fit fails before mechanics.

d_ti=R^T(x_i-mean(x))-(X_i-mean(X)); d_ri=Log(R^T Q_i).
Differentiate every term analytically using the unchanged Jet2 Exp/Log and
eigenpair derivatives, yielding d,D,Hess(d). For actual local f,K:

    g=D^T f
    H=D^T K D + sum_i f_i Hess(d_i)
    P=diag(I,Jleft(eta_i)); P^T r=g
    P^T J=H-(dP)^T r

r has spatial wrench rows; J has spatial rows and additive chart columns.
The chart Hessian H is symmetric for this conservative scope; J need not be.
Never symmetrize, drop force-weighted Hessians or chart connection, substitute
cached reference K at finite d, or rotate force instead of work pullback.

Common motion holds X fixed: x*=W*x+t,Q*=W*Q,R*=W*R, so d is invariant.
Coordinate re-expression transforms X and physical axes and conjugates Q/R.
Numbering permutes captured arrays while physical normal/direction and graph
port D0 remain fixed. D0, fit R and nodal Q are distinct authorities. A same-pose
rebase changes Qaccepted to Qtrial and eta to zero, never X or section origin;
local d, work channels and detached actual local candidate must agree.

## Q4 source-native signed work channels

The independently derived assessment is bound as a payload. Actual
compute_stiffness_components supplies Kphysical, Kpl, Khourglass and Kqualified.
Q4's nonlinear call adds Kqualified-Kinherited(0) to the inherited tangent,
and that correction times d to force. On this admitted elastic branch the
inherited bending, MITC4 shear and drill are linear and cancel exactly with
their zero tangent. Analytical h and h^3/12 moduli make the zero call's five
layers equivalent here; this is not a claim for another material branch.

Use actual _nonlinear_geometry arrays, local transform T0 and membrane weights
w=detJ*weight, not the Equation-7 frame or shear quadrature in their place.
For y=T0*d, e=Bm*y, p=Gw*y, n=[p_x^2/2,p_y^2/2,p_x*p_y], ev=e+n,
A=h*C_el, Beff=Bm+dn/dy, Nv=A*ev and Nl=A*e:

    U=0.5*d^T*Kqualified*d + sum w*(ev^T*A*ev-e^T*A*e)/2
    delta_f_y=sum w*(Beff^T*Nv-Bm^T*Nl)
    delta_K_y=sum w*(Beff^T*A*Beff-Bm^T*A*Bm
                  +Gw^T*[[Nv_x,Nv_xy],[Nv_xy,Nv_y]]*Gw)

Transform the increment with T0^T and T0. Retain FIVE named records: physical
mixed baseline, numerical PL, numerical hourglass, added compatible VK membrane,
removed compatible linear membrane. The last record has sign -1; all others +1.
Every record carries its signed potential, force and tangent and provenance.
PL/hourglass never enter physical fields or section outputs. Their energies
remain separate. The VK-minus-linear contribution is not asserted positive.
Verify the signed aggregate against the ACTUAL unchanged local response.

Physical mixed baseline fields use unchanged source recovery and its stationary
weak work, not a presumed pointwise equality of independent/compatible fields.
The two compatible membrane records retain their own e, N, B, source stations,
weights and frame. Engineering xy strain is twice tensor xy; Nxy is tensor xy.
The nonlinear center-frame and mixed Equation-7 frame are not assumed equal.
Transport each channel to reference-global tensors, then current tensors R*T*R^T;
bind physical station coordinates. Use actual D4/director transformations.

Do not expose Nmixed+Nv-Nl as one conventional finite physical resultant:
one Beff gives the unwanted Bnl^T*(Nmixed-Nl). This gate exposes no such sum,
does not modify compute_stresses, and claims no yielding/fatigue/design field.
It verifies source-native nodal/virtual work, separately typed station-value
diagnostics and numerical exclusion, not full finite conventional recovery.

## S3 source-native work

Use unchanged V2D scalar elastic response and its actual V2C-overlap/native
station operators. Its admitted local force is linear in local d; finite
geometric terms arise through the full common-pose pullback. Keep physical and
PL records separate, using actual physical resultants, weights, station order
and source director maps. No Q4 or beam strain/reversal convention is imported.
Bind reference normal and director polarity; numbering reversal is not physical
director reversal. Explicit normal reversal tests use the actual family policy.

## Frozen local checks and execution

The JSON inventory is ordered and mandatory. For all four shapes use nonzero
mixed deformation, noncommuting accepted/trial rotations and source sections.
Use independent Rodrigues/Kabsch value reconstruction, not the map under test.
Check first/second d derivatives and actual work/tangent independently at EACH
h={1e-4,1e-5,1e-6}; normalized invariant tolerance 1e-11 and directional 1e-7.
Reference operators and six rigid nulls use actual family operators, with their
known reference ranks (Q4 18, S3 12), not cached finite substitutes.

Include every D4/D3 permutation, common motions 0,[.4,-.3,.2],pi about x,
1.4*pi about y, passive Rz90 plus [2,-3,1], physical director reversal,
same-pose rebase, repeated lower eigenvalues, unique-top degeneracy and guard
before evaluation. Compare the old chart only at independently matching physical
poses, with derivatives transported into a common chart. Never equate raw old
and new tangent arrays. Numerical checks may falsify these equations; they do
not authorize adjusting actual family coefficients or tolerances.

Q4 sentinels: square checkerboard w=[a,-a,a,-a], a=.01, zero rotations
(linear membrane zero, VK channel nonzero); and a mixed-field mismatch exposing
the invalid single-Beff formula. Construct the latter from source baseline
operators, not coefficient tuning. Require finite energy/force/tangent checks
on each channel and sum, immutable returned arrays/candidate, caller mutation,
changed normal/section/origin rejection, and no publication on failure.

Each mechanics child: one numerical thread, 600 seconds, 24 GiB entire process
tree, 120 seconds without CPU/output progress; <=3 children, <=1800-second wave.
No automatic retry. Exclusive fresh external diagnostics, complete tree drain
on failure. Separate local test lane; do not rerun accepted historical lanes
as a substitute. Before mechanics: frozen implementation, complete source and
environment lease, guards and test inventory. The environment capsule hash is
2ce154b866565e1d03019651b1ae7fdd070e5554f38d72adf21d8080558b6756.

## Boundary and next stages

Local results are development only: process/evidence failure takes precedence
over operator/work contradiction, which takes precedence over scoped local
pass. None discharges G3c. All 25 original graph variants, actual native internal
stationary blocks, joint work/action-reaction, accepted-origin prepare-all,
atomic publication, cancellation/token/cache protection, prefix-authenticated
restart, independent implementation review and two complete formal cycles remain
required. Full PHYSICAL_RECOVERY and the B2 clamp-domain limitation remain on
the parity register. G4 history-bearing sections and G5 integration remain open.
No public mechanics, aliases/defaults, package, release or existing evidence edits.
