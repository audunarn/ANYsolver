# GE-B3 private variational shell connection map V2

This is an explicitly identified successor connection map, not a change to the
qualified Q4/S3 local operators, existing corotational wrapper, public routing,
defaults or historical evidence. It remains unqualified and private. V1 global
static histories are preserved, but cannot qualify conservative V2 spectra or
be hot-restarted under V2; the assembly identity distinguishes the policies.

## Preserved blocking observation

At `6365ff3478dfd90dc7949c312fafc565ed46e984`, the actual curved free-beam /
supported-shell coupled owner reached its second accepted load point with
free residuals 3.613e-14 (Q4) and 5.724e-15 (S3 V2D). Its spatial-row Jacobian,
pulled back on the free rows by the additive shell Exp differential, had
normalized symmetry errors 4.8552925210788786e-5 and 5.9532713803890146e-5.
The required 1e-11 gate fails. The initial-point errors were below 1.3e-16.
Raw probe command/stdout/stderr/process receipt are preserved externally at
`ge-beam3-coupled-spectral-20260909-probe-b`. No spectral result was accepted.
The preceding probe-a invocation was a parent command syntax error; it created
no output root and launched no worker. Do not fabricate a probe-a result.

The V1 wrapper rotates local forces but does not apply the full derivative of
its extracted deformation map. A consistent derivative of that rotated force
can pass Newton/restart checks without being a potential Hessian. Averaging
the Jacobian with its transpose would hide this defect and is forbidden here.

## Explicit successor equations

Let X_i and x_i=X_i+u_i be reference/current positions and R_i=Exp(theta_i).
Find the proper least-squares rotation minimizing
sum_i ||(x_i-xbar)-R(X_i-Xbar)||^2, with equal nodal weights. Do not normalize
individual centered vectors. This fit is objective and numbering invariant.
The independent test uses SciPy's Kabsch `Rotation.align_vectors` implementation;
its documented loss is the same:
https://docs.scipy.org/doc/scipy/reference/generated/scipy.spatial.transform.Rotation.align_vectors.html
This is an independently implemented value/finite-difference oracle, not an
independent-author scientific review or a claim of published shell authority.

For C=sum_i (x_i-xbar)(X_i-Xbar)^T and z=(C32-C23,C13-C31,C21-C12), form
D=[[tr(C),z^T],[z,C+C^T-tr(C)I]]. Its largest normalized scalar-first quaternion
eigenvector q gives R=(q0^2-v.v)I+2vv^T+2q0 skew(v). The sign of q is immaterial.
Only the largest eigenvalue must be simple; repeated lower eigenvalues are
allowed. Reject a relative top eigenvalue gap at or below 1e-11. This geometric
domain restriction is not a stiffness-rank or mass-rank filter.

The following derivatives are obtained by differentiating Dq=lambda q and
q.q=1, not by numerical frame differentiation. With A_j=D_,j constant,
S=sum_{m<max} q_m q_m^T/(lambda-lambda_m):

- lambda_,j=q^T A_j q;
- q_,j=S A_j q;
- q_,jk=S[(A_j-lambda_,j I)q_,k+(A_k-lambda_,k I)q_,j]
  -q(q_,j.q_,k).

Differentiate the quadratic quaternion formula, then the complete map
d_i,t=R^T(x_i-xbar)-(X_i-Xbar), d_i,r=Log(R^T R_i), using analytic second-order
Exp/Log jets. Existing relative-log limit 0.9*pi remains. Total additive shell
angles may represent large common rigid motions, but singular Exp charts are
rejected; they cannot be silently rebased without the accepted-state owner.

The unchanged local elastic shell response provides f(d), K(d), and trial state.
Writing Dd for the map differential and H_i for each map Hessian gives
g=Dd^T f and H=Dd^T K Dd+sum_i f_i H_i. No symmetry averaging is performed.
For P=diag(I_translation,J_left(theta)) the actual mixed assembly requires
spatial rows and additive columns: r=P^{-T}g,
J=P^{-T}[H-(dP)^T r]. The rigid joint retains its existing r_joint,J_joint P.
At conservative free equilibrium, the complete pulled-back operator must pass
the original 1e-11 symmetry gate, not a relaxed threshold.

## Scope and verification boundary

The new map accepts only the owned elastic shells; no plastic shell or arbitrary
section extension is inferred. Native beam material histories remain owned by
the existing global transaction. Local shell strains, material matrices,
quadrature, drilling, recovery/state payloads and qualified coefficients are
unchanged. This *does* change the private finite-rotation shell-to-connection
work map, so it has a new explicit policy and requires fresh tests. It is not
retroactive authority for V1 coupled outputs.

Focused checks cover Kabsch values, analytic first/second map derivatives,
equal-weight node permutation invariance, D3/D4 real-operator covariance,
large rigid motion, local-potential path-integral work, spatial tangent
directional agreement, global wrench balance, unchanged reference stiffness,
singular/malformed rejection, loaded global symmetry, and exact fresh-owner
restart with V1/V2 cross-policy rejection. Matrix and process observations stay
external. Tests are not independent-author review or coupled modal/buckling
qualification. Existing completed beam campaigns must not be rerun for this
isolated connection correction.
