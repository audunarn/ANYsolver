# G3c scalar-local recovery and energy addendum

Status: DRAFT_REQUIRING_INDEPENDENT_EQUATION_REVIEW.
Base local foundation: 744d66e7858f25ce2ce6b6a554cb67444f6ce97b,
tree 5cacf0940e4a5ef36b589931d8440b9a70461d5e.
This is not G3c acceptance or a public recovery change. The direct-anchor
potential, local operators, scientific tolerances and full graph obligations
remain unchanged. No mechanics run is authorized by this draft alone.

## Source-equation interpretation

The accepted parent requires physical stations from the unchanged local family
evaluation. Its scalar compute_nonlinear_response returns force/tangent only;
compute_stresses instead uses linear endpoint gradients, including for B3.
Do not label that older stress envelope as finite work-conjugate recovery.
Here stations are reconstructed from the same local potential and checked
against the actual unchanged force/tangent. Existing compute_stresses stays
unchanged and is not called. No fibre stresses or material history are claimed.

Source: hash-bound src/anysolver/elements.py, B2 _local_linear_stiffness
(lines3820-3876), scalar compute_nonlinear_response (4528-4615), basic force
interpolation (814-889), and B3 scalar compute_nonlinear_response (4889-5058).
Section order is [eps,gamma_xy,gamma_xz,kappa_x,kappa_y,kappa_z] and
[N,Vy,Vz,T,My,Mz]. S=diag(EA,G*A*ky,G*A*kz,G*J,E*Iy,E*Iz), G=E/(2*(1+nu)).
Only the already admitted history-free isotropic material and positive scalar
section are in scope. Unequal Iy/Iz and shear factors remain supported.

## B2

Use d in reference section axes and the actual K_noax (linear stiffness with
axial rows/columns zero). Put f0=K_noax*d, e=(u2-u1)/L +
((v2-v1)^2+(w2-w1)^2)/(2*L^2), and N=EA*e.
Pi=0.5*d^T*K_noax*d+0.5*EA*L*e^2.
Basic forces are [N,f0[9],f0[4],f0[10],f0[5],f0[11]].
At t=(xi+1)/2, interpolate:
Vy=-(q4+q5)/L, Vz=(q2+q3)/L, T=q1,
My=(t-1)*q2+t*q3, Mz=(t-1)*q4+t*q5.
Strains are S^-1 times these six resultants. Axial strain is exactly e.
The transverse N*v' and N*w' string-force contributions belong to the
nonlinear virtual-work map, not an extra physical shear strain/resultant.
Use stations xi=[-sqrt(3/5),0,sqrt(3/5)] and weights [5/9,8/9,5/9]*L/2.
Require the integrated station energy to equal Pi; do not adjust section
coefficients to force agreement if a historical scalar safeguard is active.

The actual scalar B2 operator computes phi=12*EI/max(G*A*k*L^2,1e-12).
This is a real domain obstruction for physical-S recovery: L=1,E=1,nu=0,
A=1e-14,k_y=k_z=1,Iy=Iz=1e-12,J=1e-12 are positive admitted foundation
inputs but activate the safeguard. Its effective shear rigidity differs from
the physical G*A*k. Record BLOCKED_G3C_B2_PHYSICAL_RECOVERY_SHEAR_CLAMP;
do not change the operator, use effective rigidity as physical section data,
or silently exclude this input while claiming all-positive-domain recovery.
The registered G3c fixtures do not activate this clamp. Passing those fixtures
does not resolve this domain-wide recovery/parity obstruction. An explicit
negative regression must preserve the distinction. No successful physical
recovery record may be returned for the clamp-active case.

Explicit obstruction: with GA_eff=max(GA,1e-12/L^2), the integrated physical
energy minus actual operator energy is L/2 times
[Vy^2*(1/GAy-1/GAy_eff)+Vz^2*(1/GAz-1/GAz_eff)]. It is strictly positive
for nonzero shear in a clamped direction. This is an algebraic source witness,
not a new qualification run and not a scientific threshold adjustment.

For virtual work use d(strain)/dd=S^-1*H(xi)*dq/dd. Here H is the above
force interpolation, q0=EA*e has its full nonlinear axial derivative, and
the remaining q derivatives are the extracted K_noax rows. Do not substitute
a compatible linear-shape B matrix for B2. Contracting these strain variations
with section resultants and reference weights must reproduce the actual local
force, including axial geometric string terms, on the retained fixtures.

## B3

Use N=[xi*(xi-1)/2,1-xi^2,xi*(xi+1)/2] and N'=2/L*
[xi-1/2,-2*xi,xi+1/2]. At each existing three-point Gauss station:
e=u'+0.5*(v'^2+w'^2), gamma_xy=v'-rz, gamma_xz=w'+ry,
kappa_x=rx', kappa_y=ry', kappa_z=rz'. Resultants=S*strain.
Pi=sum(weight*L/2 * 0.5*strain^T*S*strain).
Do not use endpoint-only B3 gradients or replace its existing quadrature.

## Frames, work and evidence

Return detached immutable station arrays, positive reference-length weights,
reference section frame A0 and current section frame Q_A*A0, policy and
definition identity. Section component ordering is explicit. Proper global
re-expression and common rigid motion are distinct tests. Under connectivity
reversal, reorder stations and apply strain/resultant sign map
diag(1,1,-1,1,1,-1); never change the physical anchor or material direction.
Here A0'=A0*diag(-1,-1,1) and x'=L-x: v changes sign, w does not,
ry changes sign and rz does not. Thus gamma_xy is unchanged, gamma_xz
changes sign, kappa_y is unchanged and kappa_z changes sign. This is the
physical local-z/web convention, not the native beam's different convention.
These are section resultants, not a shortcut for the pulled-back global nodal
wrench; the complete existing D and second derivatives still define that work.

Require independent station reconstruction, integrated potential equality,
energy derivative versus actual chart force, actual tangent directional checks
at every h=[1e-4,1e-5,1e-6], finite work, covariance and reversal, finite
nonnegative energy with normalized rigid-zero checks, immutable outputs and
definition mismatch rejection. Use inherited
1e-11 invariants and 1e-7 directional thresholds; no tuning after results.
Independent review must confirm B2 force/compliance recovery reconstructs its
actual scalar potential, not a replacement element operator. Full recovery
acceptance stays false until these obligations and review pass.

No graph, state commit/restart, formal cycles, G3/G4/G5 closure, alias/default,
package or release authority follows from this local addendum. The usual
600-second,24-GiB,one-thread child bounds and no automatic retries still apply.
