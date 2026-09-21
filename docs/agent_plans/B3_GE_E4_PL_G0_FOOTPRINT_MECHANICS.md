# G0 footprint mechanics candidates (experimental)

Status: bounded feasibility only. This is a derivation record for independent
mechanics review, not the selected production attachment formulation or a
qualification claim. The registered runs and limitations are in
`B3_GE_E4_PL_G0_REGISTRATION.md`.

## Coordinates, work and the drill negative control

Let shell footprint reference points be `X_i`, current positions `x_i`, and
beam reference/current poses `(b_0,B_0)` and `(b,B)`. Beam rotations update
spatially by left multiplication. Shell director coordinates `theta_i` are
independent of their positions in E4-PL; they are not defined by a surface
normal merely because both appear in a six-coordinate node.

At a planar Q4 or S3-V2D single node, the quadratic energy for a pure
normal-axis rotation is entirely in the element's numerical drilling channel.
In the registered flat fixtures its physical quadratic energy is zero. An
isolated full-pose tie can create an apparent beam-normal torque stiffness
from that completion, so a reaction alone cannot qualify physical transfer.
No drilling coefficient or element guard is changed to address this.

## Rigid footprint candidate

For each material point in a bounded footprint, define the fixed offset
`e_i=B_0^T(X_i-b_0)`. The rigid material correspondence is

```text
c_i = B^T (x_i-b) - e_i
Pi_rigid = sum_i lambda_i · c_i
```

The constraints act on shell positions and beam pose. They intentionally
restrict all sampled footprint points to the beam's rigid motion. The
shell director coordinates do not enter this law. `lambda_i` is a material
force covector; the physical spatial shell force is `B lambda_i`, and the
beam's equal and opposite wrench includes lever-arm moments. A noncollinear
set of footprint points is necessary for all three rotational directions.
For collinear points, rotation around their line cannot be transmitted by
position forces alone. Accidental duplicated points/equations must be
rejected by the nonlinear attachment audit.

## Distributing pose candidate

For a positive, frozen reference quadrature `w_i`, let

```text
X_c = sum(w_i X_i)/sum(w_i)
x_c = sum(w_i x_i)/sum(w_i)
C = sum(w_i (x_i-x_c)(X_i-X_c)^T)
Q = argmin_{R in SO(3)} sum(w_i ||x_i-x_c-R(X_i-X_c)||^2)
e_0 = Q_0^T (b_0-X_c)
A_0 = Q_0^T B_0
c_t = Q^T (b-x_c) - e_0
c_R = Log(A_0^T Q^T B)
Pi_dist = lambda_t · c_t + lambda_R · c_R
```

The polar/Procrustes fit must be unique in the admitted chart and its first
and second variations must be propagated into `Pi_dist`. This six-equation
functional transmits a resultant force and moment without imposing rigid
motion at every footprint node. The weight and quadrature choice must be
frozen at compilation. It is a *position-based* pose; the shell director
coordinates remain independent and can contribute to transverse shear.
This alone does not prove that the coupled shell response retains the correct
shear and bending modes or avoids locking. The bounded four-corner proof uses
equal weights and an independent SciPy Procrustes/rotation-log oracle.

At the flat reference configuration, unit `lambda_Rz` in the candidate
produces shell position forces whose net is zero and whose moment about
`X_c` is `-1`, opposed by beam moment `+1`. The shell drill-coordinate
gradient is exactly zero. This is the physical lever-arm path observed in
the registered proof; it is not a continuum weld-stress prediction.

## Coordinate tangent and remaining decisions

For either candidate, the local coordinate residual is the derivative of
its multiplier work and its tangent is the complete second derivative,
including the curvature of rotations, the pose fit, and the constraints at
nonzero multiplier. A transformed spatial-wrench row needs the associated
chart correction; a coordinate Hessian is not interchangeable with a
spatial-row Jacobian. No post-hoc symmetrization is permitted.

The current proofs establish stress-free reference values, first/second
directional work, common rigid-motion invariance, a unit torque lever arm,
and a simple degeneracy negative control. G0 still requires a coupled shell
energy/reaction comparison, transverse-shear preservation, thinning and at
least three refinement levels, mixed Q4/S3 interfaces, support overlap and
footprint intersection, and an independently reviewed reference/trace map.
The exact line multiplier space and interface-resolution policy remain
unselected. No product implementation may be admitted from these proofs
alone.
