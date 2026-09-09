# GE-B3 offset pose joint: explicit equation and port map

This is a private connection component, not an assembled beam-shell qualification
or an authorization to use arbitrary shell states. Existing beam/shell mechanics,
mass, recovery, state laws and public routing are unchanged.

## Background and the deliberately distinct choice

Steinbrecher, Hagmeyer, Meier and Popp, [A variationally consistent beam-to-beam
point coupling formulation for geometrically exact beam theories](https://doi.org/10.1007/s00707-026-04808-0),
published 13 August 2026, supplies background on relative-pose constraints,
multiplier work and coordinate transformations (sections 2, 3.1 and 4).
The [preprint](https://arxiv.org/abs/2604.02049) also describes objectivity tests.
The paper's symmetric positional construction is NOT claimed as the implemented
equation. The equations below are an explicitly master-referred rigid-constraint
choice with material-basis multipliers. No penalty regularization is provided;
off-constraint master/slave exchange symmetry is not claimed.

## Reference and current quantities

Port 0 is shell/master and port 1 beam/slave. Supplied reference poses are
\((x_s^0,Q_s^0)\), \((x_b^0,Q_b^0)\). Both frames are proper rotations;
initial relative orientation is unrestricted. Define the fixed material data

\[
e=(Q_s^0)^T(x_b^0-x_s^0),\qquad A=(Q_s^0)^TQ_b^0.
\]

At current poses, \(d=x_b-x_s\), the six constraints are

\[
c_t=Q_s^Td-e,\qquad c_r=\operatorname{Log}(A^TQ_s^TQ_b).
\]

The principal relative error must remain below \(0.9\pi\); this restricts the
relative correction, not common finite rigid motion or the initial orientation.
The reference configuration satisfies both constraints. On the constraint
manifold, \(x_b=x_s+Q_se\) and \(Q_b=Q_sA\). Eccentricity therefore rotates
with the master rather than remaining a fixed global offset.

The definition contains reference positions/frames, port ordering, update and
multiplier-basis policies. It is immutable and externally hash-bound when read
from canonical JSON. It contains no material history or implicit class routing.

## Work and first derivative

With material multipliers \(\lambda=(\lambda_t,\lambda_r)\),
\(L=\lambda_t^Tc_t+\lambda_r^Tc_r\). The translation multiplier is expressed
in the master frame and the rotation multiplier in the relative-error basis.
It must not be interpreted as a constant spatial dead moment.

The pose variation ordering is
\([\delta x_s,\delta\theta_s,\delta x_b,\delta\theta_b]\), with
\(\delta Q=\widehat{\delta\theta}Q\). If \(\phi=c_r\) and
\(B=J_l^{-1}(\phi)A^TQ_s^T\), the independently reconstructed Jacobian is

\[
C=\begin{bmatrix}
-Q_s^T&Q_s^T\widehat d&Q_s^T&0\\
0&-B&0&B
\end{bmatrix}.
\]

The complete multiplier residual is \(r=(C^T\lambda,c)\). The last six
equations are constraints, not physical recovery resultants. The joint creates
no artificial mass, spring, damping or material energy.

Under a common rigid motion \(x_i'=Sx_i+t, Q_i'=SQ_i\), both constraint
vectors and the material multiplier components remain unchanged. The spatial
forces and moments transform with S. Objectivity implies, even off constraint,

\[
F_s+F_b=0,\qquad d\times F_b+M_s+M_b=0.
\]

This is why the offset moment must be included. At the zero-multiplier reference
state C has rank six; the 18-variable multiplier Hessian has inertia (6+,6-,6zero).
Those six zeros are rigid-pose variations, not beam/shell elastic modes.

## Second variation and the actual Newton derivative

Analytic second-order SO(3) jets differentiate one scalar L in local Exp
coordinates. They produce the symmetric chart Hessian H. For the derivative
of the actual spatial residual, subtract \(\tfrac12\widehat{r_\theta}\)
from each spatial rotational diagonal block. Thus the spatial Jacobian J is
not generally symmetric away from equilibrium. Tests compare J against the
finite difference of the independent analytic spatial residual; symmetry of H
alone is not the acceptance criterion.

## Mixed additive/spatial ports

For a charted port, the supplied anchor and additive coordinates define
\(Q=\operatorname{Exp}(\theta)Q_a\). For a spatial port, the anchor is the
current authoritative rotation matrix and the coordinate vector must be zero.
The map P is identity except for charted rotational blocks \(J_l(\theta)\).
The transformed residual and its derivative are

\[
\bar r=P^Tr,\qquad
\bar J=P^TJP+\left[\partial_jP^T\right]r.
\]

The derivative term is included only for charted ports. Two additive ports
produce a symmetric potential Hessian; mixed/spatial ports generally do not.
The implementation obtains P and its derivatives analytically from Exp jets.
Total chart angles are not subjected to the relative-error 0.9pi bound. A
singular additive chart (for example 2pi) rejects with a state-owner rebasing
diagnostic; the same pose remains admissible through rotation matrices.
Neither this component nor a caller may invent a new accepted anchor silently.

## Scope and checks

Tests independently reconstruct C using SciPy rotations and closed-form
Log/Exp Jacobians, without importing the production jets into the oracle.
They check first variation/work at 1e-11, full spatial and mixed-port derivatives
at 1e-7, scalar second variation at 1e-7, common finite motion including pi,
offset wrench balance, the reference rank/inertia, large common translations
with low coordinate parts, repeated noncommuting updates, deterministic
serialization and malformed/foreign-policy/chart rejection.

This is independent implementation, not independent authorship. The component
does NOT yet bind real shell/beam accepted-state capsules, solve a coupled mesh,
condense constraints in a modal/buckling solve, commit history or authorize a
public connection. Those assembled owner/solver gates remain required. In
particular, an arbitrary rotation vector must not be presented as an accepted
Q4/S3 director. Every result retains production_qualified=false and
owner_binding_authorized=false.
