# Independent matrix-pose shell successor assessment

Reviewer: `/root/g3b_independent_review`, separate reviewer.
Scope: read-only source and equation assessment, no mechanics execution or
candidate edits. This is not implementation or graph authority.

## Disposition

The proposed private extension is mathematically sound: preserve the existing
equal-weight positional Procrustes rotation and replace each nodal Exp(theta_i)
by Exp(eta_i)Qaccepted_i in the complete deformation map. I found no new fatal
objectivity or repeated-eigenvalue obstruction from that substitution. It needs
a distinct matrix-owned-chart policy, explicit domain/state bindings and the
tests below before implementation acceptance; existing owned-shell evidence is
not generic G3c graph authority.

Read sources include `_ge_beam3_variational_shell.py`, `_ge_beam3_mixed_ad.py`,
`_ge_beam3_pose_joint.py`, `_ge_beam3_shell_joint_trial.py`, relevant Q4 and S3
V2D geometry/state/response functions, the G3 completion contract, and
`docs/agent_plans/GE_BEAM3_VARIATIONAL_SHELL_MAP.md`. The shorter documentation
path in the old module docstring does not exist at this checkout; the actual
source authority is under docs/agent_plans.

## Kinematics, objectivity and chart derivatives

With R fitted from X and x, keep

    d_ti = R^T(x_i-xc) - (X_i-Xc)
    Q_i = Exp(eta_i) Qaccepted_i
    d_ri = Log(R^T Q_i).

Under superposed rigid motion x*=W x+s, Q_i*=W Q_i, the unique Procrustes
optimum transforms R*=W R. Both local deformations are invariant. Do not rotate
the reference geometry or material normal in this test. A passive proper
coordinate re-expression instead transforms references and conjugates Q/R.

The map differential and Hessian must include all positional R derivatives,
each accepted-base nodal Exp, and the relative Log, with exactly the same
captured input arrays used throughout. The existing complete work pullback
g=D^T f, H=D^T K D+sum f_j Hess(d_j) remains appropriate for the admitted
elastic local potential. Accepted Q is constant with respect to trial eta.

For left increments, delta Q_i Q_i^T = delta Exp(eta_i) Exp(eta_i)^T;
therefore the chart-to-spatial block is Jleft(eta_i), not a function of a
reconstructed total rotation vector. Use P^T r=g and P^T J=H-(dP)^T r.
Do not copy a raw old additive-coordinate tangent into the new chart, rotate
forces instead of pulling back, omit the connection correction, or symmetrize.

At virgin reference D removes only an infinitesimal common rigid motion. The
actual local rigid-null identities imply D^T K0 D=K0. Verify against actual
qualified Q4/S3 reference operators without substituting cached matrices away
from reference.

## Procrustes domain and repeated eigenvalues

The source differentiates only a simple largest Davenport eigenpair. Its reduced
inverse is a sum of lower-eigenspace projectors divided by their gaps from the
largest eigenvalue. Repeated lower eigenvalues do not invalidate this inverse:
rotating a basis within such an eigenspace leaves the weighted projector sum
unchanged. Quaternion sign changes also leave R and its derivatives unchanged.
Do not demand four distinct eigenvalues or invert a rank-deficient 3x3 planar
covariance as if it had full rank.

For a rigid motion of a noncollinear planar reference, the two nonzero covariance
singular values are sigma1,sigma2>0. The Davenport eigenvalues are the signed
combinations of these values, and the top gap is 2*min(sigma1,sigma2)>0.
Regular squares and equilateral triangles therefore have a simple top eigenvalue
despite repeated lower eigenvalues. This remains true through common pi and
1.4*pi rotations or an antiparallel current/reference facet normal.

The inherited top relative-gap threshold of 1e-11 still defines a genuine
geometric fit domain; it is not removed by matrix-owned nodal rotations and is
not a stiffness/mass-rank filter. Top multiplicity or a numerically unresolved
gap must fail closed with no arbitrary eigenvector/frame fallback. For planar
references, covariance rank at most one gives a nonunique top fit. S3 current
collinearity is one such case; Q4 degeneration/cancellation must also be tested.
Do not infer fit uniqueness merely from nodal relative-rotation bounds, and do
not silently narrow or enlarge this inherited domain.

The actual required shell relative Logs are Log(R^T Q_i). Pairwise nodal angles
alone are not a substitute for this condition. Freeze exactly which additional
graph/joint relative-rotation checks apply; retain the original shell 0.9*pi
Log domain and the accepted trial-increment cutback policy. Arbitrary common
orientation is supported, not unlimited accumulated relative twisting.

## Normal, triad and numbering authority

R is a fitted extraction frame, not the nodal material pose Q_i, and neither
is a port reference frame D0. The graph must preserve the explicitly frozen
physical D0 frames instead of deriving them again from a first connectivity edge.
An edge-derived port frame changes under numbering and can invalidate a joint
while leaving a local stiffness comparison superficially plausible.

Keep authoritative physical reference normal, material direction, and S3 director
polarity fixed under numbering changes. S3 `_geometry` internally canonicalizes
orientation against reference_normal and includes its own node permutation in
local_from_external. Use that actual family mapping. Q4 numbered frames and
engineering/resultant transformations likewise belong to its unchanged source.
Do not import native beam local-y sign conventions, average normals as material
authority, or reconstruct Q from a director alone (which loses drilling rotation).

Simultaneously permuting X, x and Q leaves equal-weight R invariant. Verify D3/D4
local operators/recovery with their actual frame conventions and frozen normals.
Physical director reversal is distinct from numbering reversal; it must not be
silently introduced by a reversed polygon cross product. Numerical drill work
and reactions must remain separate from physical section resultants.

## Accepted origin and publication

Retain fixed X/reference normals/material axes. Rebase changes only the chart
base Qaccepted:=Qtrial and eta:=0 after global acceptance; it must not reset the
reference geometry, invent a moving material reference, or advance on rejection.
The reconstructed local d at the same physical pose is unchanged by rebasing.

The actual local material origin must be owned and bound to geometry, section,
layers, physical normal and accepted local d—not to graph-global translations
or eta merely because they have the same vector length. Q4 init_nonlinear_state
and S3 init_model_bound_nonlinear_state are distinct source contracts. S3 validates
expected_committed_total_u against local d. Preserve such state linkage in replay.
Elastic material flags do not authorize arbitrary foreign/nonvirgin state dicts.
Reject plastic/generalized/initial-field origins outside this G3 elastic scope.

Prepare all family trial states at the same accepted origin/epoch. Candidate
local state and candidate nodal Q are only proposed outputs; the later owner
publishes them atomically after global convergence. A final-family exception,
cancellation or tamper must publish none. This local equation review does not
establish that future transaction or restart owner.

## Required concrete tests

1. Compare values with the bound old private map at exactly matching physical
   poses where total-angle inputs are independently known; compare transformed
   derivatives in a common chart, not raw old/new Jacobian arrays.
2. Independently reconstruct Exp(eta)Qaccepted and Kabsch/Procrustes values; check
   complete first/second deformation derivatives and actual force/tangent work at
   each inherited h=1e-4,1e-5,1e-6, including noncommuting accepted/trial rotations.
3. Use Q4 square/rectangle and S3 right/equilateral triangles to exercise repeated
   lower eigenvalues, quaternion sign changes, arbitrary common pi/1.4*pi motion,
   and positive top gap. Exercise singular/near-threshold top-gap rejection
   separately; require no mechanics evaluation after a failed frame/domain guard.
4. Check actual reference stiffness/rigid nulls, finite local operator/recovery,
   energy/work, spatial wrench balance and physical/numerical drill separation.
5. Exercise every frozen D3/D4 numbering, coordinate re-expression and common
   motion while keeping physical normals, polarity and port D0 authority correct.
6. Rebase at the same nontrivial physical pose and compare local d, force, material
   candidate and physical recovery. Compare chart-derived tangents only after
   their work-dual transport. Reject changed normal, section, origin or policy.
7. Mutate caller arrays after snapshot, reject nonproper/nonfinite Q and computed
   contractions, reject unsupported origins, and keep returned diagnostics/state
   detached. Bind all new/old source, review, fixture and environment identities.
8. Later, separately complete the genuine multi-family graph transactions,
   accepted-prefix restart and formal deterministic cycles. A shell local pass
   cannot replace these or qualify defaults, full parity, G4/G5 or release.

No scientific cases, local shell laws, quadrature, coefficients, tolerances or
existing qualified shell evidence need changing to implement this chart extension.

## Subsequent recovery-scope clarification (not implementation authority)

Fresh family-specific model/material/virgin-origin construction is consistent
with the closed homogeneous scalar elastic, zero-initial-field local stage.
Return the actual sealed family candidate in its element-local displacement
convention. This is not permission to accept foreign origin dictionaries or to
infer full state admissibility from an elastic material flag. Accepted physical
pose ownership, preparation and restart remain separate required graph work.

The inherited shell domain is the Procrustes fit-to-each-node relative Log bound,
not the direct-anchor beam's all-pair rotation bound. Unrestricted common motion
does not imply unrestricted director-only spin against an unmoved sheet.

An additional source recovery issue must be resolved before a complete shell
local gate is frozen: Q4's existing mixed-field physical recovery is linear in
local displacement, whereas its admitted nonlinear force includes a compatible
von-Karman membrane increment. Therefore the existing public recovery alone
cannot be claimed as the full finite work-conjugate recovery. A proposed
potential split into qualified linear energy plus inherited nonlinear-minus-
linear membrane energy requires separately derived work channels. Replacing
one recovered membrane resultant with a sum while using one effective strain
derivative is not established by the energy split. Preserve the public API and
source laws; either establish the honest multi-channel representation or retain
an explicit blocker. The chart derivation above does not resolve this question.

A useful unexecuted source-derived sentinel is a flat square with local
checkerboard transverse values [a,-a,a,-a] and zero rotations. Linear membrane
recovery is zero, but compatible von-Karman membrane strains are nonzero. This
is preferable to a pure affine sheet tilt that a positional extraction can
absorb. Validate the extraction and exact source response in the future frozen
local test; no numerical outcome is asserted here.
