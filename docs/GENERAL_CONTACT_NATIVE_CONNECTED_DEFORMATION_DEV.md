# Connected native axial deformation reference — DEVELOPMENT

**Source candidate only; all numerical and installed checks UNEXECUTED.**
No new execution authority is inferred from earlier connected/controller work.
This does not establish D6/C7 acceptance, general bending, finite-angle dynamics,
spatial convergence, contact, loads or support-motion admission.

## Declared physical fixture and prospective gates

Two existing centered, elastic native elements share one node. Each reference
has zero half-cell lift, straight principal axis, five distinct sorted nodes
10/20/30/40/50. Adjacent half-cell length is0.5m. Reference axis is world y;
nodal reference frames are the exact signed axis permutation
R=((0,-1,0),(1,0,0),(0,0,1)). Root position is O=(.25,-.5,.125)m.
Existing homogeneous full first-node clamp is the only imposed restraint.
Section elastic diagonal is (100000,30000,30000,30,20,10), with the existing
section units; generalized yield metric I, yield1e6 and hardening1. Inertia per
reference length is diag(2,2,2,.02,.01,.01), as an explicit declared primitive,
not inferred from a section class name. No external loads or contact.

Initial physical nodal axial displacement is2e-5*(0,1,2,3,4)/4m; initial rates
and cell SO3 increments are zero. Production retains all true physical cell
spin coordinates/inertia and algebraic traces. Zero subsequent spins are an
axial invariant to verify, not hidden constraints or mass condensation. The
nonzero initial elastic deformation accelerates freely: it is not claimed to
be static equilibrium. Public initialization must solve actual algebraic
compatibility and physical acceleration through its ordinary owner contract.

Frozen dt=2^-16s; default4 steps, focused2-step variant. Prepared exact restart variants use
fresh 2-step full and 1+1 split, or 4-step full and 2+2 split. Positive scales: displacement2e-5m, force1N,
moment1Nm, energy1e-5J, velocity=(2e-5)*sqrt(EA/rhoA)/(4ell)m/s and
acceleration=(2e-5)*EA/(rhoA*ell^2)m/s^2. Discrete response/accounting and
force/moment balances <=1e-6; independent virtual work/tangent <=1e-5;
analytical *semidiscrete* response <=0.1%; integrated energy change <=2%.
No gate, law or time-grid tuning after a failure is authorized by this document.

## Why the reference is four affine half-cells, not two Q2 bars

The initially suggested consistent quadratic-bar M/K premise was rejected
before execution. Actual compensated_strain forms the two retained half-cell
chords. For U=I and axial displacement, z_c=(q_R-q_L)*e. The generalized-cell
constraint integrates reference weight times frame-transpose/Jacobian. With
straight reference and constant principal frame, complementary elasticity is
Psi*_c=ell*N_c^2/(2EA), so z_c=dPsi*/dN implies
N_c=EA*(q_R-q_L)/ell. The compatible retained mixed potential is therefore
U_c=EA*(q_R-q_L)^2/(2ell). Retained resultants contain these two global force
vectors per element and zero end moments; those fields are checked explicitly.

For zero reference lift, actual centered station position is
x_c(t)=x_L+t*(x_R-x_L), t in[0,1]. Independent weak-form integrations give
K_c=(EA/ell)*[[1,-1],[-1,1]] and
M_c=(rhoA*ell/6)*[[2,1],[1,2]]. Assemble four cells into five global nodal
coordinates, each shared node counted once. The reference helper imports only
NumPy and derives these primitive matrices itself; no production structural,
inertia, quadrature, residual, tangent or mass recovery is its reference.

The actual scalar invariant has no transverse motion, frame motion, cell spin,
curvature or retained moments. Tests check those conditions and full rotational
work equations rather than inferring them from projected axial displacement.
The native producer remains the full coupled retained solver throughout.

## Independent endpoint, stage and support equations

With root q0=v0=a0=0, use the free4x4 M/K blocks:
(M_ff+h^2*K_ff/4)*a*=-K_ff*(q+.5*h*v),
q+=h*v+.5*h^2*a*, v+=h*a*.
Stage q*=(q_old+q_new)/2 and v*=(v_old+v_new)/2, stage acceleration a*;
endpoint acceleration solves M_ff*a_new=-K_ff*q_new. This is the discrete
midpoint stage, not a claim that it equals an exact continuous-time midpoint.
semidiscrete_exact(t) independently diagonalizes the mass-weighted symmetric
P1 matrix for the analytical finite-dimensional vibration reference. It is not
an exact continuum/spatial solution.

Root support force is the FULL residual
F_s=e*(M_0f*a*+K_0f*q*), including consistent-mass off-diagonal inertia.
First-cell tension alone is insufficient. Moment about global0 is O cross F_s;
force and moment impulses are h times these stage values. Axial displacement
contributes no additional arm. End reaction is separately evaluated with
endpoint acceleration; it is not an integrated stage impulse. Homogeneous
root displacement gives exactly zero support work. P=e*1^T*M*v and
H=O cross P; verify DeltaP=h*F_s and DeltaH=h*(O cross F_s) independently.
Nonzero support force/moment are explicit required assertions.

Compatible elastic U=.5*q^T*K*q, kinetic T=.5*v^T*M*v. Linear midpoint
conserves T+U exactly in arithmetic because the free weak balance is satisfied
and fixed-root work is zero. Actual numerical energy is checked, not used to
reject or alter a native step. The raw retained potential agrees with U only
on this compatible elastic axial invariant; this is no generic mixed-potential
or constitutive-energy reinterpretation.

## Prepared checks and usage

- tests/test_ge_beam3_native_connected_deformation.py checks endpoint and stage
  positions/rates/accelerations, actual retained forces/zero rotational fields,
  mechanical energy and momentum, full support force/moment/work/impulses,
  analytical semidiscrete response and complete fresh split journal equality.
- Its independent mass/work/tangent check compares primitive M and K with actual
  production recovery and global algebraic Schur pullback. Physical inertia is
  not condensed in the production trajectory. Its direction has physical length
  components; work is normalized in J, force-rate in N and moment-rate in Nm.
- `python -m examples.native_connected_deformation_dev --steps 4` calls existing public
  solve_transient with existing TransientConfig; it is a runnable candidate only.
- examples/native_connected_deformation_reference.py is the independent helper.

Numerical/import/build/installed work requires a separate bounded scope. Prior
9.1034228s connected/shared residue is not available to this new reference slice.

The prepared response control checks initial displacement/rate/acceleration and
full translational acceleration vectors at initial, stage and endpoint states;
axis projection alone is insufficient. With NATIVE_TRANSIENT_RESULT_RECORD set
by an authorized runner, tests save separately named actual public result JSON,
exact checkpoint bytes and SHA256 before assertions. Ordinary pytest requires
no recording environment. These prospective captures are not executed evidence.
