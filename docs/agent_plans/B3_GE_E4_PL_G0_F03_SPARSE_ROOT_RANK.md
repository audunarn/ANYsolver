# Bounded root and free-slope rank proof

Development helper only; no physical reference execution or G0B acceptance.
The frozen classical reference has three root pose constraints. The fourth
row is a free transverse-slope observation used to reject a discretization
that silently loses that freedom. It is never added to equilibrium constraints.

The helper owns validated sparse root C (3 by N), derivative port A1_y(0)
(1 by N), and positive D. It constructs the actual binary64 rows R C D and
(L0/U0) A1_y(0) D in the fixed left-then-right arithmetic order, with
R = diag(1/U0, 1/U0, 0.46/U0). Nonfinite or underflowed nonzero entries fail.
Trace identity and mechanical scaling must be verified separately.

Exact rational Gram matrices of the stored scaled rows determine full row
rank. Sylvester's criterion on exact leading minors tests positive
definiteness. Diagonal Gram matrices give an exact squared singular ratio.
For other matrices, Rayleigh and absolute-row-sum bounds enclose the smallest
and largest eigenvalues. Exact positive-definiteness tests of shifted Gram
matrices bisect those bounds. No numerical eigensolve supplies acceptance.

For each of the three-row and four-row matrices, acceptance requires the
proved lower bound on lambda_min/lambda_max to be at least the square of
the held binary64 threshold 1e-10. An upper bound below that threshold is
HOLD. Exhausting the declared bisection budget also returns HOLD, with full
rank and an unresolved ratio distinguished from deficient rank. Exact
arithmetic and workspace budget violations are explicit errors.

Only the four-by-N port rows and at-most-four-by-four Gram matrices are
dense. No global square stiffness, constraint nullspace, inverse or dense
derivative tensor is created. The workspace estimate is conservative
accounting for this helper, not a measured process peak or a replacement
for the later supervised resource gate. Fraction sizes, cumulative checked
bits and bisection work have explicit limits. Returned scaled rows use
immutable owned bytes.

Synthetic tests cover independent SVD comparisons, dependent root and
slope rows, inclusive exact threshold and nearby failures, non-diagonal
ill-conditioned rows, inconclusive bounded searches, CSR/CSC parity,
coordinate rescaling, ownership, malformed input, underflow and budgets.
They do not establish shell trace adequacy, physical convergence, production
coupling qualification or practical model scale.
