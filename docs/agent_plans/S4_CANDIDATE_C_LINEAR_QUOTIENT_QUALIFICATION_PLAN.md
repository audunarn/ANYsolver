# Candidate C global multiplier-quotient qualification

Status: exact linear necessary screen authorized; production remains restricted.

## Authority and boundary

This successor starts from commit
`2cb8c53cd1097380c872ba2802ec0eacc5198304`, tree
`f95d74e3ed1bb760f622e188f75f62a8b7ae43f6`.  The accepted Candidate-A
open packet, Candidate-B packet, rank-four constraint packet, published
MITC4+/D mechanics, and legacy `ShellElement` are immutable inputs.

Candidate C is coefficient-free.  It adds no penalty, stabilization,
`C^T C`, inferred modulus, selector, production dispatch, or public API.  It
retains the registered A2 element constraints with normalized multiplier
basis `[(1/2) 1, (3/2) rs]`.  Only exact dual redundancy is quotiented; the
raw primal constraint matrix, its row space, and its kernel must be unchanged.

Permitted tracked changes are this plan, new Candidate-C derivation/case/
oracle/contract/output/report/test evidence, an independent review, and LF
transport rules in `.gitattributes`.  No production source, package metadata,
workflow, sibling repository, preserved evidence directory, push,
publication, or cleanup is authorized.

## Frozen formulation

Use the unit square split into consistently counter-clockwise `n x n` Q4
cells, `h=1/n`, `a=h/2`, and the accepted six-DOF node order.  The retained
topology diameter is the global `ell=sqrt(2)`.  In mixed-unit coordinates,

```text
q_phys = S_q q_hat
C_hat  = C_phys S_q
W_hat  = S_q^T W_phys S_q.
```

The multiplier mass is the physical surface `L2` Gram matrix.  Both normalized
A2 modes have element mass `a^2` and are mutually orthogonal.  For assembled
`C_hat` and positive primal norm matrix `W_hat`, the quotient is

```text
A = M_lambda^(-1/2) C_hat,
Lambda_C = Lambda / ker(A^T),
||[mu]|| = min_{nu in ker(A^T)} ||mu + nu||_2.
```

The quotient inf-sup value is the smallest positive generalized singular
value of `A W_hat^(-1/2)`.  This is a dual gauge convention only: no raw row is
deleted, and `ker(C_hat)` and `range(C_hat^T)` must be preserved exactly.

The primal norm is

```text
sum_e integral_e [ ell^-2 |u_h|^2 + |grad_s u_h|^2 + |theta_h|^2 ] dA.
```

For the exact witnesses below only the consistent Q1 `theta_D` mass block is
active, so translation scaling and gradient terms cannot affect the result.

## Exact necessary screen

Reproduce the raw A2 bounded-patch annihilator as a hostile control.  Then
analyze both free and fully clamped structured families for all integer
`n >= 3` using exact rational tensor difference/sum maps.

For the free family use the integer witness

```text
x_i = (i+1)(n-i),  i=0,...,n-1;  alpha=0; beta=x tensor x.
```

For the clamped family use

```text
x_i = (i-(n-1)/2)^2 - (n^2-1)/12;
alpha=0; beta=x tensor x.
```

The clamped witness must be proved orthogonal in the physical multiplier
metric to the complete dual kernel, not merely to the raw A2 checkerboard.
The all-`n` polynomial identities and mass-matrix lower bounds are
authoritative.  Direct assemblies at `n=4,8,16,32` are corroborative only.
Numerical SVD, fitted rates, floating tolerances, interval arithmetic,
80/160/320-digit shards, finite rotations, nonlinear mechanics, and
performance work cannot determine this terminal.

## Terminal

If either exact family has a positive quotient inf-sup bound tending to zero,
record `NO_GO_CANDIDATE_C_QUOTIENT_INF_SUP`.  If the proof is incomplete,
record `UNCLASSIFIED_CANDIDATE_C_LINEAR_QUOTIENT`.  Only an exact common
positive mesh-independent lower bound plus every preservation identity could
record `PROVISIONAL_GO_CANDIDATE_C_LINEAR_QUOTIENT`.

Every result retains `NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`.  A provisional
GO would authorize only a separately preregistered finite-rotation and
nonlinear-functional-redundancy program.  It would not authorize production.

Two fresh standard-library oracle processes must emit byte-identical canonical
UTF-8/LF JSON.  Identity, contract, or repeat-byte failures are blocking
execution errors and never scientific results.
