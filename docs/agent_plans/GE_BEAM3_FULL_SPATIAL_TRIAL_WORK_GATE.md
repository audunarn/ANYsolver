# Full spatial continuum second variation and admissible trial work

Parent: 5fa46af9cc617bbf4726fda33acc03cd5151a4d8.
Research-only successor; existing production operators, mechanics, recovery,
states, defaults and source reference equations remain unchanged.

## Derivation and boundaries

Material strain and balance authority remains Bali et al., DOI10.1002/nme.6994,
equations 6,7,10,11,15-17; public article:
https://pmc.ncbi.nlm.nih.gov/articles/PMC9543773/.
The chart Hessian and canonical Jacobi form below are derived here, not claimed
as equations quoted from that paper or independently authored/reviewed.

Use spatial path r(t)=r+t*u and R(t)=Exp(t*hat(theta))*R. Prime denotes reference
arclength differentiation, v=r', n and m are spatial force and moment. For a
symmetric positive-definite elastic material section C (including coupling),
the first material strain variation is

    de = [R^T (u' - theta cross v); R^T theta'].

Second material variations are R^T(theta cross (theta cross v)-2 theta cross u')
and -R^T(theta cross theta'). Thus the internal second energy density is

    de^T C de + n dot (theta cross (theta cross v)-2 theta cross u')
                 - m dot (theta cross theta').

Spatial dead point-force potential is linear in r, so its Hessian is zero.
This does not cover follower loads, material nonlinearity or physical dynamics.
Use q=(u,theta), V=hat(v), N=hat(n), M=hat(m), Q=diag(R,R), D=Q C Q^T,
T=[[0,V],[0,0]], G=[[0,-N],[0,-M/2]], B=D*T+G, and
F=T^T D T+diag(0,(N V+V N)/2). Density equals

    q'^T D q' + 2 q'^T B q + q^T F q.

Canonical p=D*q'+B*q. Its translation part is delta(n), but its moment part
is delta(m)+M*theta/2, NOT raw delta(m). The Hamiltonian generator is

    [[-D^-1 B, D^-1], [F-B^T D^-1 B, B^T D^-1]].

Verify direct cross-product versus block work, coupled sections, arbitrary
proper rotations, reference-linear limit, Hamiltonian symmetry and canonical
moment distinction. Verify second potential derivatives separately using
matrix exponential/Frechet evaluation of the actual perturbed strain, central
differences h=.001,.0005 with Richardson extrapolation. Freeze normalized
algebraic/work tolerance 1e-11 and directional tolerance 1e-7. Do not use
numerical differentiation as the operator implementation.

## Saved-state trial-work diagnostic

Bind the entire accepted endpoint manifest SHA-256
6e4ee30363656257d27db2fc5ace7ff24b76472b17050e6481af6d72ffe82ff6 and the exact
signed comparison hashes in the worker. Neither the continuum nor native beam
is solved again. Read the saved complete 52-field polynomials at +/-0.0065.

Admissible trial fields: sin(k*pi*(X+1)/2) in each of six spatial components,
k=1..8,1..16,1..24. These globally continuous H1 fields vanish at both clamps.
They retain all spatial displacement/rotation components and do not impose the
quarterspan numerical continuation controller as a physical support. Fields
remain continuous through the crown point force and other segment boundaries.
Derivative jumps are permissible for energy trial fields; no artificial force
or moment continuity is imposed on a Ritz trial not satisfying equilibrium.

Integrate over four saved segments using 64 and 128 Gauss points per segment.
Use the L2 Gram matrix solely to normalize Ritz trial functions; it is NOT mass
and its Ritz values are NOT frequencies or buckling load factors. Save raw
Hessian, Gram matrix, coefficients and all work diagnostics externally.
Require raw Hessian symmetry <=1e-11; disclose roundoff-only symmetrization
before the symmetric eigensolver. Choose the lowest 24-mode Ritz trial with
deterministic sign (largest absolute coefficient positive). Reintegrate that
same trial with direct cross-product work at both orders; require <=1e-11
normalized block/direct agreement and <=1e-8 relative quadrature disagreement.
Separately compute integrated finite-rotation potential with the same h values;
require <=1e-7 normalized extrapolated second-variation agreement.

A resolved negative direction requires negative integrated work and extrapolated
second variation, with work magnitude >100 times their discrepancy. It supports
a numerical instability direction only, not interval certification or a complete
Morse index. Positive trial work cannot prove continuum stability. Prior negative
discrete work at +/-0.006 is a different state; do not claim a same-state native
stability comparison until a separate native endpoint capture has been performed.

## Execution and evidence

Run local tests before freezing. Then positive smoke, followed only on success
by negative and two replicas in fresh processes. Guard clean commit/Python hash/
registered package versions before scientific imports and after evaluation.
Runtime version checking is not a complete environment graph certificate.
Require byte-identical same-sign trial-work outputs. Exclusive output paths;
preserve failures externally; no retry of consumed processes/roots. Inner
evaluation bound60s, child600s/24GiB, one numerical thread, max3 concurrent,
wave1800s and existing120s CPU inactivity limit. No new resource ledger requests.

Full production, state-safety, independent author review, installed selection,
nonlinear material and objective beam-shell connection qualification remain open.
No activation, release, version, package or default changes.
NO_GO_PRODUCTION_RESTRICTION_UNCHANGED.
