# Finite S3 reference-dead pressure: bounded development decision

2 October 2026; base solver e59c9221. Private experiment only. The public
finite-S3 reference-dead rejection, pressure schemas, checkpoints, physical
acceptance criteria and legacy element equations are unchanged.

## Question and result

The native MIN3 operator specifies the linear field
`w_h = sum(N_i w_i - l_i theta_xi + m_i theta_yi)` and its pressure covector.
It does not uniquely define a finite enhanced surface. Independent source review
confirmed this: objective cubic enhancements can share its reference derivative.
Neither reference parity nor correct differentiation establishes physical fidelity.

One proposed lift used the existing corotated nodal rotation logarithms. Its
derivatives, native reference force, rigid-motion work and chart invariance passed,
but a director-preserving spin changed work from 0.18604688205058909 to
0.1943685138383134 J. This full-log lift is **rejected for a director-only surface**.
The failed assertion remains in raw v2. The current test asserts the counterexample
to preserve the finding; that assertion does not accept the rejected formulation.

## Targeted revision and declared surface

Let Q be the existing proper positional Procrustes frame, n0 the reference normal,
R_i the physical nodal orientation and d_i = Q^T R_i n0. Let rho_i be the axial
logarithm of the shortest proper rotation taking n0 to d_i. This tilt depends on
the physical director, not drilling about it. Antipodal directors are outside the
candidate chart. More narrowly, the inherited SO(3) logarithm admits relative
tilt below 0.9 pi; boundary controls retain that limit. No regularizing stiffness
or altered material law is introduced.

In the reference element frame define

    h = sum(-l_i rho_xi + m_i rho_yi)
    x_h = sum(N_i x_i) + Q n0 h.

For uniform reference-area traction p n0, its external work reduces exactly to

    W = sum(f_trans0_i . u_i) + (n0 . Q n0) sum(m0_i . rho_i).

The scalar reduction uses native integrated MIN3 reference covectors. A separate
Hammer-station reconstruction evaluates l/m and the surface directly without
that load vector. Second-order AD differentiates the complete fitted frame and
director tilt. For the additive-to-spatial increment map P, wrench rows and
Jacobian obey `P^T f = grad(W)` and
`P^T J = Hess(W) - (dP^T) f`. No tangent symmetrization is used.

The first variation recovers MIN3's native load because the common fitted-spin
term cancels (sum l_i = sum m_i = 0), and tilt recovers the two linear bending
rotations. A uniform director tilt remains possible with a flat surface; the
candidate does not impose director/normal equality. This bounded shear screen
is not a complete finite director-shear or loaded-response validation.

## Evidence and limitations

Source tests cover both pressure signs, native reference force, independent
surface work, a three-step finite-difference plateau, conservative coordinate
Hessian, spatial-row Jacobian, rigid motion/resultants, frame/origin covariance,
chart rebasing, unchanged-director spin/work, uniform tilt and antipodal rejection.
v1: six original consistency checks passed. v2: four passed and three failed:
two failures were a sign error in the new independent quadrature oracle's b_i;
the third was the physical full-log drilling counterexample. v3: nine failed
because an AD helper required constant jets instead of numeric vector entries;
this implementation error was repaired. v4: all nine director-candidate checks
passed in 1.64 s pytest time (2.481 s supervised route; peak tree 169656320 bytes).
Failures and commands are retained. Timings are observations, not a speedup claim.

Final focused checks: v5 passed nine candidate cases plus two existing finite-S3
owner rejection cases (11 in 1.79 s). Review follow-up v6 passed the strengthened
drilling case and two tilt-boundary cases (3 in 1.56 s). This is eleven distinct
candidate cases and two owner guards, not fourteen distinct cases. Source-only;
no installed-artifact or loaded S3 claim. Runs requested one numerical thread and
JIT disabled, with 600 s/1 GiB limits; no effective BLAS-pool measurement was made
for this local slice. No resource limit was reached.

[Raw runs, failed source and final candidate/tests](s3-dead-work-raw-v1.zip),
SHA256 `1980b92a03c4b15664955c49210ca7981e8edce6a8bd182660d17c743cf3250f`.

Independent Read review found no consequential algebraic defect in V2 and
recommended retaining it as the preferred **private candidate**, pending physical
validation. Its finite surface differs from the internal full-log interpolation;
their compatibility must be assessed rather than inferred from reference parity.
Review requested the tilt-boundary and invariant spatial-force/drilling-work
checks, now included. No owner dispatch imports it. In particular this
does not fix or qualify the separate mixed follower-pressure failure.

Next bounded decision: compare reconstructed surface tangents/directors for
nonuniform finite shear and assess pressure work against a physically matched
reference before owner admission. Establish the intended finite surface contract
explicitly; do not present this choice as uniquely inherited from native MIN3.
Then integrate under a distinct work-law/checkpoint identity with source and
installed lifecycle checks. No automatic mesh-refinement campaign is warranted.
