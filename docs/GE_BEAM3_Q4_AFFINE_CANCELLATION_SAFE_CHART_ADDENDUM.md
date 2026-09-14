# Private Q4 increment-resolved chart evaluation: proposed source addendum

Status: DRAFT_PENDING_INDEPENDENT_DESIGN_REVIEW. No implementation or execution
authority yet. This proposes a numerically equivalent evaluation of the same
equal-weight proper Procrustes/Davenport chart, not different mechanics.

## Preserved source and incident

Retain the original numerical contract SHA-256
21cec54b2469e291c8f90a2c042e3cf693a14f7bc10efd5111ea842ca65a218c and accepted
stable-chart addendum SHA-256
1eb29b8814e6555e7d16569e2c8d30c828a60458dea4a2801c10f4d58d2c2176.
Preserve their references, exact-affine evidence, physical potential, original
35 system, recovery64 system, source coefficients, thresholds and histories.

Executed freeze484286c2e41d4a347fd8fe6ef06e9fe4457102fb, tree
16bff223011d6e221eb7f4d51c07096eba02438f, passed its separate smoke. Its full
rehearsal completed nine node packets, launched12 of15 nodes, then blocked at
SQUARE::1 MIXED amplitude1e-6: physical spatial-force normalized disagreement
1.2442263651131688e-8 exceeded the unchanged1e-11 gate. All processes drained;
no full aggregate, completed rehearsal, formal cycle or typed scientific
contradiction exists. Preserve the actual completed packets, not an all-pass
substitute or a new classification of the failed attempt.

Independent record484286c-smoke-rehearsal-evidence-review.json SHA-256
3fab4089cd13f667f13ba6149a3b4c505e316a5ff7449f2e3d8a8dd262eb697f and raw-file
manifest484286c-smoke-rehearsal-files.json SHA-256
65fb8a88cfa3585b4e1c00bde3a76e74801716391afd01d9bf6cb26364f808a0 are preserved
under C:/Github/ANYsolver/.perf2-worktrees/.beam-core-review-20260913/ and in
the verified durable484286c smoke/rehearsal archives. Smoke scientific.json is
13420 bytes, SHA-256 f3b721854c7c22c2be837bd2915c11acedc7938b529d7e31fee6779f63273e94.
Smoke ID95eed2a8-d9a1-4630-905e-2264acc1ff1f; rehearsal ID
1cdb780f-90fa-487a-a7f1-adae7d55c4bb. No consumed execution is retried.

Bind predecessor chart source _ge_beam3_g3c_affine_q4_chart.py SHA-256
2a26742ec7680a5e75934fb32ee8601d3877cd0befb250489f991f1b9d198a9f and facade
_ge_beam3_g3c_affine_q4_recovery.py SHA-256
1426457398831c3cf575dcebedffef6ce4c4c81ce52ccdbf0a974439d549b7ba.
Original Davenport mathematics is _ge_beam3_variational_shell.py SHA-256
b0db7a83633f4a835c06e940a6f0de36ab958f7e816c37a23c6ebc16259a2a60;
unchanged Jet2 source is _ge_beam3_mixed_ad.py SHA-256
b299ff765cd2eaae8b33a2ba1d05069f6fe8c39209e1eac75df356a2afb1fe36.
The accepted stable Exp/Log kernel and its proof/error bounds remain bound by
the preceding addendum; no new approximation coefficients are introduced.

## Cancellation paths and interpretation of inputs

The current path rounds X+u before fitting, centers that reference-scale sum,
forms covariance containing an order-one symmetric part, and finally subtracts
R^T xc-Xc to obtain order1e-8 deformation. Independent implementations can
therefore amplify order-epsilon absolute fit/subtraction errors relative to
the tiny physical force. Quaternion-to-matrix diagonal evaluation can add a
further order-epsilon identity error. This is a source-level explanation, not
yet an isolation experiment or a claim that all failures are resolved.

Authoritative inputs remain the exact supplied binary64 X,u,Qa,eta values.
The mathematical current position is their sum X+u. Higher-precision or
compensated evaluation retains that sum rather than changing any input bytes,
snapping a geometry, or importing a different pose. Rounded current-position
arrays may remain diagnostic outputs; they must not become a lossy intermediate
that discards the authoritative incremental input before the fit. Registry
recipes and all130 pinned input-state hashes remain unchanged.

## Common exact rearrangement

With centered reference Xc and centered translation uc, construct

    A = A0 + DeltaA,
    A0 = Xc^T Xc,
    DeltaA = uc^T Xc.

This is identically (Xc+uc)^T Xc. Form A0 by symmetric dot products and reflect
its entries, so no spurious skew baseline contaminates a tiny rotational signal.
Use exact Decimal conversion from each binary64 input, never decimal strings
rounded to a user-facing number. Center X and u separately at that precision.
Reference normalization is the unchanged positive constant
beta=sum_i Xc_i dot Xc_i; A/beta is the covariance used by the original fit.

After obtaining R and DeltaR=R-I, use the exact identity

    d_translation = R^T uc + DeltaR^T Xc.

Never compute DeltaR by subtracting I from a binary64 matrix already rounded
near identity. For unit quaternion q=(w,v), evaluate it directly as
DeltaR=2w hat(v)+2hat(v)^2. Retain its complete first/second derivatives;
this rearrangement is not a new interpolation or a truncation in v.

Translations and rotations still enter all24 chart coordinates. Differentiate
centering, covariance, fit and relative nodal Exp/Log analytically. It is not
sufficient to repair d values while leaving D or Hess(d) from a different map.

## Producer: same Davenport eigenstationarity, bounded accurate values

Use the exact original linear Davenport map K(A/beta). The normalized dominant
quaternion solves Kq=lambda q, q^Tq=1. Initialize using the binary64 symmetric
eigensolver and retain the original simple-top gap requirement
gap>1e-11*max(tiny,max(abs(eigenvalues))). No new rank/PSD admission, artificial
gap, eigenvalue clipping or regularizer is allowed.

Refine this same eigenpair with standard-library Decimal precision80, using
Newton on [Kq-lambda q;(q^Tq-1)/2]. Its5x5 Jacobian is

    [[K-lambda I, -q],[q^T,0]].

Use deterministic pivoted elimination and at most16 iterations per fit. Stop
only when both the eigen residual normalized by the Frobenius norm of the
normalized Davenport matrix and absolute normalization residual are <=1e-60;
otherwise return a typed evaluation
failure. These are internal accuracy checks, not replacements for or relaxations
of the frozen binary64 physical gates. Certify the dominant branch as follows,
in addition to retaining the unchanged binary64 seed simple-top guard:

- Gram-Schmidt orthogonalize all four seed eigenvectors in increasing eigenvalue
  order at Decimal80 precision. Normalize each column, requiring its pre-normal
  norm to lie in[1/2,2], and require max(abs(G^T G-I))<=1e-70. No defective basis
  is silently repaired or substituted; this is refinement of an already accepted
  eigensolver basis, not reference-geometry projection.
- Compute T=G^T K G and its four Gershgorin intervals: diagonal Tii plus/minus
  the sum of absolute off-diagonal entries. Inflate each endpoint outward by
  b=1e-60*norm_F(K). This budget exceeds the fixed small-matrix Decimal80
  operation/orthogonality error; no norm floor is added. Require the interval
  for the original top seed column to be strictly disjoint above all others.
  The disjoint interval contains exactly one dominant eigenvalue of the same
  symmetric operator. If intervals overlap, fail closed rather than swapping
  roots or changing the original geometric admission threshold.
- For the refined pair let rho=norm_2(Kq-lambda*q)/norm_2(q)+b. Require
  [lambda-rho,lambda+rho] to intersect the dominant interval and lie strictly
  above every other interval. Normalization must independently pass. Thus the
  residual-enclosed eigenvalue is the unique dominant one; mere proximity to an
  unbounded binary64 seed is not enough.

No alternate
eigenbranch, caller-defined precision or automatic resource retry is admitted.

Compute K_i analytically from centered reference coordinates; K_ij=0. The
derivatives of the normalized eigenpair satisfy

    lambda_i=q^T K_i q,
    (lambda I-K) q_i=(K_i-lambda_i I)q, q^Tq_i=0,
    lambda_ij=2 q_j^T K_i q,
    (lambda I-K)q_ij=(K_i-lambda_i I)q_j+(K_j-lambda_j I)q_i-lambda_ij q,
    q^Tq_ij=-q_i^Tq_j.

Solve the corresponding bordered systems, evaluating lambda I-K accurately
before conversion so its small entries are not lost. This is the same implicit
eigenvector differentiation as the original reduced-resolvent formulas, not a
numerical fit derivative. Include zero rotational-coordinate K_i and all mixed
24x24 Hessian entries. The shared Jet2 class remains unchanged. Refined q and
its derivatives create the rotation/DeltaR Jets through the exact quaternion
identities. Independently verify derivative normalization, eigenstationarity,
mixed-second symmetry and rotation orthogonality before acceptance.

Apply this single algorithm across the registered contexts rather than selecting
a special physical-amplitude branch that could introduce derivative discontinuity.
The proposed80-digit/16-iteration choices and dominant-root enclosure require explicit
independent review before coding; failure never falls back to the inaccurate
predecessor or reduces precision/case coverage to finish a wave.

## Relative nodal rotations and spatial connection

Retain the accepted stable Exp/Log coefficient evaluator and strict0.9pi guards.
Near-identity products can be formed through exact increment identities:
E=Exp(eta)-I is built as A(theta^2)hat(eta)+B(theta^2)hat(eta)^2, without
subtracting rounded identities. With Da=Qa-I from the actual supplied matrix,

    Dtrial = Da+E+E Da,
    Drelative = DeltaR^T+Dtrial+DeltaR^T Dtrial.

The relative matrix is I+Drelative, so its antisymmetric part comes directly
from Drelative. Supply the Log series argument delta=-trace(Drelative)/2
directly, not1-(1+trace(Drelative)/2). The non-series cosine is1-delta.
Use the same accepted coefficients and branch threshold, differentiating delta
through both orders; never recover its small value by subtraction from a rounded
cosine. Differentiate the
same expressions through both orders. This does not orthogonalize, repair or
invent unrecorded accuracy for Qa; caller matrix bytes and admission remain
authoritative. Tests must verify ordinary/common/passive/rebased contexts as
well as tiny ones. No claim of all arbitrarily tiny common-motion differences
is inferred from this finite inventory.

The spatial connection remains P=diag(I,J_left(eta)), r=P^-T g and
Jsp=P^-T(H-Cconnection). Its stable analytic Exp evaluator and both derivatives
remain as accepted. Physical local Q4 source response, M/n/C and64-variable
Schur, station-coordinate association and separate numerical channels are
unchanged.

## Independently authored checker method

The checker author independently proposes Decimal80-digit proper-polar
stationarity, not Davenport/eigenvector reconstruction. It starts from SVD
columns normalized in Decimal and refines R by right-Cayley Newton. For
M=R^T A, b=axl(M-M^T), solve

    (tr(M)I-M) omega=b,
    R_next=R(I+hat(omega)/2)(I-hat(omega)/2)^-1.

The nonsymmetric M is required away from the root. At stationarity it becomes
the symmetric polar stretch, giving the existing independent Sylvester
derivatives. Max32 iterations, covariance-normalized residual<=1e-60, otherwise
typed failure. The denominator is norm_F(A) from the same Decimal covariance,
strictly positive. Require max(abs(R^T R-I))<=1e-70 and abs(det(R)-1)<=1e-70.
Certify the maximizing branch independently: for S=R^T A require the symmetric
part of tr(S)I-S to be positive definite by deterministic high-precision
Cholesky with all three pivots strictly positive. The vanishing skew residual
and this strict local maximum of the linear SO(3) objective select the proper
maximizing branch (not a stationary saddle/minimum). Retain the original SVD
normalized gap check
2*(sigma2+signed_sigma3)/beta >
1e-11*max(tiny,sum(sigma)/beta), with signed_sigma3 determined by the proper
determinant correction. Check the refined rotation's objective against the SVD
proper maximum sigma1+sigma2+signed_sigma3 at relative1e-11 using norm_F(A),
not max(1,norm). Also recheck the equivalent normalized gap from the eigenvalues
of the refined symmetric stretch at the same original threshold. These are
independent branch/admission checks, not a new physical tolerance or a repair of
the source operator. Failure is typed and cannot authorize recovery.
Convert R and R-I
separately and retain the independently authored analytic D/D2 formulas and
ScalarJet chart composition. No producer import, source copying or shared fit
output is permitted. This method outline was supplied by the checker author;
the producer author has not read its implementation.

All Decimal arithmetic uses ROUND_HALF_EVEN and precision80 in a local context;
no process-global precision mutation. Frobenius/vector norms are the square
root of the sum of exact-input Decimal squares. Scalar residuals use absolute
value. Elimination pivots on largest absolute available entry, breaking ties
by lowest current row index; a zero pivot is a typed failure, never regularized.
Gram-Schmidt uses fixed input column order and one reorthogonalization pass.
Each iteration tests residuals before update; maximum counts include the final
residual test. No convergence claim extends beyond the registered, passing
finite cases; nonconvergence is an explicit process/evidence block. The fixed
roundoff budget is numerical conservatism for small-matrix evaluation, not an
outward interval proof of geometry/coercivity or an exact-field claim.

Preserve the original independent chart
docs/reference_cases/ge_beam3_q4_affine_numerical_chart.py (LF8271 bytes,
SHA-256 b7cc92f70d35e3b8f2ab10202cb2f3ad1116e92775425888e482293b323c23ac).
Implement the checker arithmetic in a separate
docs/reference_cases/ge_beam3_q4_affine_increment_chart.py. The source-equation
checker may change only its chart import/call binding from its predecessor
docs/reference_cases/ge_beam3_q4_affine_numerical_checker.py (LF16293 bytes,
SHA-256 79addca6199a57443c151ce7cc0dcb44da1c5cf2702bd85393ae0e9dc618e3c6).
The producer counterpart is a new private
src/anysolver/_ge_beam3_g3c_affine_q4_increment_chart.py. Preserve the predecessor
private chart; only facade routing/identity moves to the separately bound path.
All precision refinement and analytic derivatives must consume the same actual
input values. In particular no refined scalar value may be attached to the
derivatives of a different rounded fit. Existing tiny cases also receive full
d/D/D2 comparisons, not only physical-work checks.

## Identity, regression and release boundary

Proposed new private identity:
GE_BEAM3_Q4_AFFINE_INCREMENT_RESOLVED_CHART_NUMERICS_V1. It replaces the required
chart_numerics_id value in the complete canonical facade descriptor. Reject
old/missing/resealed predecessor IDs and cached operators associated with the
old complete definition before family work. Keep station_association_id and
the exact natural-coordinate bijection unchanged. No graph restart is added.

Implement only after independent design acceptance: a private successor chart
and facade routing/identity, independent checker chart arithmetic, their tests
and source-authority bindings. Preserve all original public/chart/kernel files,
registry bytes, contract/evidence history and existing scientific thresholds.

Retain the same15 full nodes, two-node smoke and130 observed input states.
Within that inventory add actual provenance/identity checks, all24 derivative
identities, stable-versus-naive cancellation witnesses using already registered
tiny states, internal nonconvergence rejection, and real mutation rejection
for missing DeltaA, reintroduced X+u subtraction, omitted DeltaR derivatives
and wrong eigen/polar branch. Never replace required physical checks by a
terminal flag or input-count assertion. Freeze the exact new source graph and
prove regenerated source-bound manifests retain all input-state hashes.

Independent implementation review precedes fresh smoke and complete rehearsal;
only full rehearsal success permits two formal cycles. Keep all process/tree,
memory, inactivity, concurrency and1800-second wave limits unchanged. No retry,
partial canonical success, tolerance floor or omitted case. Terminal precedence
and scoped affine-local acceptance remain unchanged. General geometry/history
parity, full G3c, G4/G5, public integration, defaults and releases remain open.
