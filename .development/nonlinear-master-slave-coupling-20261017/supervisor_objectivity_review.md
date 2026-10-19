# Independent interpolation objectivity and DC-fold assessment

2026-10-18, read-only. Reviewed SLICE3_UNBLOCK_DELIVERY.md, the current rotating
map/transfer and constituent pullback symbols, corrected continuation wrench
oracle, ep_dc_block_probe.py and the supplied scientific adjudication. No
imports, FE solves, pytest, numerical probes, product/test edits or workers.
Mistral owns candidate design/implementation; Astra retains adoption/acceptance.

## Scientific conclusion

The current arithmetic rotation-vector interpolation is provably not rigid-spin
equivariant for differing master rotations. Its slave orientation and offset
both violate the adopted contract, and its work-conjugate force transfer can
therefore balance reduced equations while leaving a physical spatial wrench.
This is a concrete mechanism consistent with direct coupling passing and
interpolated coupling failing. It does **not**, without evaluating the derived
identity at the retained state, prove that the entire measured12.8765 imbalance
comes from that mechanism rather than constituent/recovery errors.

An objective mean must replace both the orientation and offset frame on the
active interpolated rotating route. An objective offset with the old averaged
slave rotation cannot satisfy the adopted contract. All derivative/restart/
postcheck/force-transfer seams below must change together. No particular SO(3)
mean algorithm is adopted by this review.

The dimensional augmented SVD does not prove a fold. A reliable inferred
control compliance of approximately -.01060 m per lambda is finite and nonzero;
it contradicts the specific claim that the DC Schur derivative is near zero.
The supplied tiny positive-control probe also tests unloading, whereas the
requested continuation direction is negative control displacement.

## Exact finite rigid-rotation counterexample

Two equal weights; master orientations R1=Rx(pi/2), R2=Rx(-pi/2).
Their arithmetic rotation-vector average is0, giving slave orientation I.
Superpose Q=Ry(pi/2) on both physical masters. The principal rotation vectors
of Q*R1 and Q*R2 are

    (2*pi/(3*sqrt(3))) * (+1,+1,-1)
    (2*pi/(3*sqrt(3))) * (-1,+1,+1).

Their arithmetic average is (0,2*pi/(3*sqrt(3)),0), giving Ry(1.209199576...),
where equivariance requires Q*I=Ry(pi/2). These are different physical
orientations, not merely different logarithm representations. For any offset
not parallel to y the corresponding lever arms also differ. All rotations are
inside the principal chart; no pi crossing is needed to produce the failure.

The current rigid-body-motion test, in which every master starts with the same
orientation, cannot expose this. Equal master orientations and single-master
direct coupling are special cases where arithmetic averaging is equivariant.

## Infinitesimal rigid-spin defect and wrench identity

Use J_i=J_l(theta_i), theta_bar=sum(w_i*theta_i), J_b=J_l(theta_bar),
R_b=Exp(theta_bar), A=d(R_b*r0)/dtheta_bar. Assume weights sum to1 and the
reference attachment satisfies X_b=sum(w_i*X_i)+r0, as in the EP builder.
Under a superposed infinitesimal spatial spin Omega:

    delta_x_i = Omega cross x_i
    delta_theta_i = J_i^(-1)*Omega.

Define

    D = sum(w_i*J_i^(-1)) - J_b^(-1).

The current map produces an additive slave-rotation error D*Omega and a slave
translation error A*D*Omega relative to a true physical rigid spin. This follows
from A*J_b^(-1)*Omega = Omega cross (R_b*r0).

An explicit infinitesimal example is theta1=(a,0,0), theta2=(-a,0,0), weights1/2,
theta_bar=0. Then

    D = diag(0, (a/2)*cot(a/2)-1, (a/2)*cot(a/2)-1).

For small a the last two terms are -a^2/12+O(a^4), so the defect persists at
arbitrarily small nonuniform rotations. At a=pi/2 the y/z factors are pi/4-1.
A spin about x happens to be represented correctly; a noncommuting spin does
not. Likewise a planar commuting deformation can balance its planar moment
while still lacking arbitrary three-dimensional spin equivariance.

For any frozen slave imbalance (f_b,m_b), where m_b is the additive rotation
covector, let v=m_b+A.T*f_b. The current transfer puts w_i*f_b and w_i*v on
each master and zeros the slave. Convert all rotational covectors to spatial
moments using J_l(theta)^(-T), and use deformed force arms. The exact change in
total physical spatial moment caused by that transfer is

    Delta_M = D.T * (m_b + A.T*f_b).

Derivation: translation arms lose (R_b*r0) cross f_b when the slave force is
moved to the weighted attachment point. For the common mean chart,
J_b^(-T)*A.T*f_b equals that missing lever moment. The difference between
weighted master and mean-chart moment duals is precisely D.T*v. The net force
is unchanged when the weights sum to1.

At equilibrium p=F_int-lambda*F_prop, with objective constituent internal
wrench near zero, the corrected physical root+applied moment should equal
sum(Delta_M) plus the free residual's wrench and constituent internal-wrench
error. This gives a source-derived prediction of the actual observed imbalance,
including its vector direction/sign, rather than a loose plausibility argument.

## Discriminating retained-state check — no additional equilibrium solve needed

Using copied history at the already retained interpolated -.10 state:

1. Assemble full F_int and compute its total spatial wrench from deformed nodal
   positions and J_l(theta)^(-T) rotation covectors, preferably also per physical
   shell/beam element. Work-conjugate objective constituents should each have
   negligible internal wrench. Corotational assembly is already on the reference
   full-coordinate route; no von-Karman batch reduction is selected here.
2. Form p=F_int-lambda*F_prop. Compute its physical moment before and after the
   existing slave transfer and compare their vector difference to sum(D.T*v)
   over every active interpolated entry. This identity tests the map/transfer
   mechanism directly even if the state is not exactly equilibrated.
3. Reconcile root+applied moment with that prediction, the measured free reduced
   residual contribution and the constituent internal wrench. If the map term
   explains the imbalance, the interpolation contract is the cause. If not,
   localize constituent pullback/recovery or missing-force/reaction accounting
   before changing more mechanics.
4. Check finite rigid covariance directly on a nonuniform master-orientation
   fixture and its reconstructed slave, including orientation and position.
   Do not attempt to represent an arbitrary global rigid spin through a fixed-
   support reduced q space: that variation moves the supports. Use local
   descriptor/master state or an unconstrained kinematic fixture instead.

These checks use the retained state, not a new sweep. Any owner execution still
counts against the unchanged allowance. This reviewer did not execute them.

## Obligations for an objective mean candidate

Let theta_m=Log(R_mean(R_i,w_i)) in an admitted smooth local chart,
theta_lin=sum(w_i*theta_i), and G_i=dtheta_m/dtheta_i. Require

    R_mean(Q*R_i,w_i) = Q*R_mean(R_i,w_i)
    sum(G_i*J_i^(-1)) = J_l(theta_m)^(-1).

The second identity is the differential rigid-spin test and implies physical
wrench preservation of the correct covector transfer. Require translation
partition of unity, direct/identical-rotation limit, and the existing first-order
weighted linear relation. State the chart/nonuniqueness failure boundary; do not
claim arbitrary pi crossings or silently select a discontinuous branch.

Connected changes are mandatory:

- **Forward map:** starting from the old linear expansion, translation correction
  is `(R_mean-I)*r0 - skew(theta_lin)*r0`, not merely
  `(R_mean-I-skew(theta_m))*r0`. Also add theta_m-theta_lin to slave orientation.
  Otherwise the old linear lever or old slave orientation remains in the state.
- **Inverse/postcheck:** subtract these same master-dependent corrections from
  the supplied physical slave translation AND rotation. Do not overwrite an
  incompatible supplied slave rotation with theta_lin: that would hide a
  constraint violation. The inverse must preserve deliberately injected slave
  perturbations for the residual postcheck to detect. Include ordinary restart,
  force/DC checkpoint reconstruction, fully constrained and preload paths.
- **Jacobian:** slave translation depends on A*G_i; slave orientation depends on
  G_i. The present frozen theta_proj=sum(w_i*T_theta_i) is insufficient. Retain
  individual master projections or equivalent complete derivatives, including
  upstream admissible linear constraints.
- **Reduced force/reactions:** transfer w_i*f_b to master translations and
  `G_i.T*(m_b+A.T*f_b)` to master rotation covectors, then zero slave terms.
  The current w_i common-covector shortcut is invalid. Verify this transfer
  against J.T and the physical spatial wrench identity independently.
- **Geometric tangent:** include second derivatives of the mean itself and the
  slave orientation, contracted with the complete slave rotation imbalance m_b,
  as well as offset translation derivatives contracted with f_b. The current
  force-only lever Hessian assumes theta_bar is linear and omits these terms.
  Use net internal-minus-external imbalance and retain external follower tangent.
  Symmetrization alone cannot repair omitted derivatives.
- **Derivative coverage:** finite-difference the whole forward map, the reduced
  net force and mean derivative. Include nonzero slave moment covectors so a
  missing orientation Hessian is discriminating. Check direct/coincident limits
  and nonuniform multiaxis rigid covariance, not only a planar arc.
- **Downstream admission:** the existing translation-dependency refusal remains
  necessary. A nonlinear interpolated slave rotation can no longer be consumed
  as a master by an uncomposed affine or rotating constraint. Add refusal for
  those rotational descendants before constitutive activation. Single-master
  direct rotation remains linear and need not lose its existing supported
  descendants. A currently identical multi-master state is not sufficient to
  admit a dependency that becomes nonlinear later. Upstream shell row ties remain
  admissible because they do not consume a nonlinear beam slave.

## Compatibility/applicability boundaries to resolve explicitly

The active rotating route is a new finite-rotation candidate. General multiaxis
finite states will intentionally differ from the defective arithmetic mean;
public small-rotation/linearized weights and direct coupling should not change.
Old finite candidate states may be incompatible with the adopted new manifold:
refuse them accurately rather than silently projecting or stripping valid state
bindings. Regenerate half/full cached evidence after the source identity changes.
Preserve restart material history and existing caller-input exact immutability.

The current interpolated weight validator admits finite mixed-sign weights
forming a partition of unity. A chosen SO(3) mean must handle its admitted
weights or explicitly propose a bounded active-route refusal for a nonunique/
singular mean. Do not silently clamp/replace weights. Standard EP/arc weights
are positive. Finite partition tolerance also means any claimed exact covariance
must use a consistently defined partition, not ignore a weight-sum defect.

An intrinsic/Karcher-type local mean or an anchored relative-log interpolation
can be left-equivariant, but these are candidate methods, not adopted algorithms
here. Some objective means, e.g. a projected arithmetic matrix mean, do not retain
exact linear interpolation of commuting angles for unequal weights. If such a
mean is selected, update the analytical derivation's claim that planar rotation
interpolation is exact; its unchanged continuum arc remains the oracle and
finite-mesh interpolation error remains subject to the same gates. Do not fit
loads/reference to the selected mean.

Zero-offset descriptors are currently inactive. The adopted brief explicitly
does not expand zero-offset legacy capability; do not claim general 3D
objectivity for that legacy interpolated orientation path. This does not
invalidate the specially constrained commuting planar e=0 arc verification.

## Fold/SVD adjudication

For residual g=F_int(q)-lambda*f and control c*q=u_control, the augmented
linearization is A=[[K,-f],[c,0]]. When K is invertible, its Schur derivative is

    S=c*K^(-1)*f = du_control/dlambda,
    det(A)=det(K)*S.

Thus a DC parameterization failure with nonsingular K requires S=0. A reliable
S approximately -.01060 m/lambda is neither zero nor evidence for that failure.
A load-controlled limit point is different: K can become singular while the
augmented DC system remains regular and d(lambda)/d(u_control) can vanish.
Do not conflate the two mechanisms or infer either from Newton nonconvergence.

The current SVD mixes displacement/rotation DOF units, force/moment residual
units, load-pattern magnitudes and a dimensionless control row. Rescaling units
or the load-pattern normalization changes its numerical condition number without
changing the physical branch. Moreover ep_dc_block_probe uses unscaled
np.linalg.lstsq with default rank truncation; check the original augmented
residual and achieved c*dq before treating rhs_control/dlambda as a reliable
compliance measurement.

Use explicit physical row/column scales for any rank/condition claim:
translation/rotation unknown scales and lambda scale on columns; force/moment
residual and control-displacement scales on rows. State them and check the
original-system residual, then interpret the physical Schur derivative/null
direction. The supplied positive tiny control increment gives negative dlambda,
consistent with unloading for negative S. It does not discriminate failure to
continue in the required negative displacement direction. Existing evidence
supports “unresolved Newton/globalization failure,” not fold/collapse. No new
probe is authorized by this review; use the existing bounded owner assignment.
