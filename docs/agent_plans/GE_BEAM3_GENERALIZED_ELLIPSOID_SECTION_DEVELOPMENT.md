# Native six-resultant ellipsoidal section — equation map and development

Base: 44abf155442ff62df737af1ddafd2d015f50ecd9. Existing physical fibre,
beam and shell operators and historical evidence remain unchanged. This is
an additive, private generalized constitutive building block, not beam
integration, production qualification or a fibre/3D J2 material adapter.

Public background distinguishes stress-resultant section plasticity from
physical fibre recovery. OpenSees' Bidirectional Section documents coupled
section forces and use at nonlinear-beam integration points:
https://opensees.berkeley.edu/wiki/index.php/Bidirectional_Section .
Its modeling-capabilities page describes mapping constitutive behavior to
section resultants:
https://opensees.berkeley.edu/OpenSees/user/modellingCapabilities.php .
Its J2 page separately specifies a deviatoric tensor-stress yield model:
https://opensees.github.io/OpenSeesDocumentation/user/manual/material/ndMaterials/J2Plasticity.html .
These are primary background sources, not a claim that the model below is
their exact implementation. No OpenSees source code is copied or imported.
The following six-dimensional metric extension and conjugate are derived
here and require independent review; formal source-version authority remains
part of eventual qualification.

## Declared native law

Use work-conjugate e=[eps_x,gamma_xy,gamma_xz,kappa_x,kappa_y,kappa_z] and
s=[N,Vy,Vz,T,My,Mz]. Supply complete symmetric-positive-definite elasticity C
and yield metric M, with their units and material-coordinate orientation.
Do not infer a yield capacity or fibre geometry. Y>0 and H>0 are explicit
isotropic hardening data. q(s)=sqrt(s^T M s); f=q-Y-Hp.

At fixed origin (z0,p0), z0 is a six-component plastic offset and p0>=0.
The local law accepts an explicitly supplied offset; reachability from a
virgin state is a history-chain requirement, not inferred from this point
law. Default origin is exactly zero. A caller cannot use point-law state
acceptance as global restart authority.

For d=z-z0, define rho=sqrt(d^T M^-1 d). The incremental potential is

W(e)=min_d [ .5*(e-z0-d)^T C*(e-z0-d)
             + Y*rho + .5*H*((p0+rho)^2-p0^2) ].

Stationarity gives d=lambda*n, n=M*s/q, p=p0+lambda, lambda>=0 and
q<=Y+Hp with complementarity. All six components can yield together, unlike
a prescribed single plastic direction. M specifies a resultant interaction
law, not an automatically derived cross-section capacity or tensor J2 law.

The full conjugate is

W*(s)=.5*s^T C^-1*s + z0.s + max(q-Y-Hp0,0)^2/(2H).

On a plastic branch let lambda=(q-Y-Hp0)/H. Then

e=C^-1*s+z0+lambda*n,
D2W*=C^-1+n*n^T/H+lambda*(M-n*n^T)/q.

The consistent tangent is inverse(D2W*); no elastic tangent substitution.
On the exact yield boundary select the elastic semismooth derivative and
label it explicitly. Perfect-plastic/softening generalized interaction is
not admitted by this finite full conjugate; the existing physical-fibre
plateau law is not changed or removed.

Stored energy is .5*s^T C^-1*s+.5*H*p^2 and dissipation is Y*lambda.
Incremental potential subtracts the old stored hardening energy. Require
Fenchel equality and work conjugacy. No physical fibre stresses are supplied.

For strain control solve scalar tau=lambda/q in [0,1/H]:
s=(C^-1+tau*M)^-1*(e-z0),
q*(1-H*tau)=Y+H*p0.
Use bounded 80-digit Decimal arithmetic, 256 bisections, 15-second internal
deadline and paired binary64 output. Internal root/strain checks use 1e-60
and 1e-50 respectively; they are numerical solver controls, not exact
certificates. Reject nonrepresentable outputs and nonpositive tensors;
do not clip eigenvalues or regularize hardening.

## Independent calculation and state

The oracle imports no ANYsolver code. It solves the seven primal KKT
equations in (s,lambda) using 96-digit Decimal Newton with a bordered
Jacobian, rather than the producer's scalar dual inversion. Its tangent is
obtained by differentiating that bordered system. Both solvers retain bounded
iterations/deadlines; no automatic retry.

Histories and responses are owned immutable values. Local station trials
do not advance history. Commit recomputes from the accepted origin;
discard, stale/foreign/repeated commits, invalid trials and mutated responses
are rejected. Replay uses the original accepted origin, not a new unloading
trial. The local transaction is not yet a global beam material-state adapter.

Tests: all six individual yielding components; full coupled nonproportional
loading/unloading/reversal; oracle stresses, tangents and histories; primal
and dual derivatives; Fenchel energy; material work-coordinate covariance;
SPD/symmetry; semismooth boundary; mutation/ownership and deterministic bytes.
Use existing 1e-11 invariant/oracle and 1e-7 directional gates.

Run smoke then full rehearsal, freeze, two fresh bounded cycles and compare
canonical files. One numerical thread, 24 GiB, 600 seconds and 120-second
CPU-inactivity bound per child; at most three workers and 1,800 seconds/wave.
Independent review remains PENDING. Retained-cell integration, measure-consistent
material adapters, global solver/path parity, mass/spectra, engineering
qualification, public packaging and beam-shell joints remain required.
