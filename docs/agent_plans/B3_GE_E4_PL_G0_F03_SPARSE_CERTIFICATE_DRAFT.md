# F03 sparse numerical building blocks: bounded proof contract

This implements candidate A and a candidate-solve preparation route from
`B3_GE_E4_PL_G0_F03_LOCAL_NUMERICAL_ADMISSION_DRAFT.md`. It is not a
scientific registration, selected method, physical convergence decision,
native element path or permission to repeat a consumed run. The original
condition, backward-error, physical and work thresholds remain unchanged.

## Arithmetic and complete inverse-column verification

`scripts/_b3_e4_f03_sparse_certificate.py` treats every finite saved binary64
entry as an exact real input. For an elementary product or addition, take
the rounded result and its immediately adjacent representable numbers as
lower and upper endpoints. Addition of interval endpoints is rounded outward
again. Sparse matrix products explicitly traverse every stored entry and
every supplied column; they do not use an unexplained error factor for a
BLAS or sparse multiplication kernel. Empty rows are retained. The residual
`I-HY` includes rows whose target is zero.

The premise is IEEE binary64 elementary arithmetic with gradual underflow.
A runtime check detects observed FTZ/DAZ behaviour in the used elementary
operations. Every square-root endpoint additionally passes an exact scalar
rational squared-inequality check against its binary64 input endpoint, with
explicit finite nonnegative domain and response checks. A library result
that violates the enclosure fails; an inaccurate but conservative positive
result can remain a valid bound. No
matrix-level rational multiplication is introduced by that scalar check.
Platform qualification must bind the elementary arithmetic premise if this
method is selected. Nonfinite endpoints and overflowing intermediates fail explicitly.
For known nonnegative quantities only, intersect a downward enclosure with
the nonnegative half-line; no computed norm or matrix is repaired.

Absolute interval endpoints give upper absolute residuals. Sequential
outward sums give `y1, yi, e1, ei`. Require both residual norm bounds below
one. The same Neumann proof as the numerical draft gives

```
b1 = y1/(1-e1), bi = yi/(1-ei)
inverse_two_upper = sqrt(b1*bi)
condition_two_upper = sqrt(h1*hi)*inverse_two_upper.
```

Every denominator is bounded downward and numerator/product/square root
upward. Norm lower bounds use squared entries summed downward. The backward
denominator uses a lower bound on the maximum row/column Euclidean norm,
which is a lower bound on `||H||2`, together with lower norms of `z,b`.
No upper matrix norm is used in that denominator. Require condition upper
`<=1e10` and its product with backward-error upper `<=1e-8`.
Without `b,z`, a passing condition result is only `CONDITION_BOUND_ONLY`.

The verifier accepts contiguous indexed blocks that cover all N columns
exactly once. It copies each block, validates its shape and finite entries,
and never factorizes or computes columns itself. It records the complete
raw evidence requirement `8*N*N` bytes even though live block memory is
linear in `N*block_width`. The matrix validator copies and checks raw sparse
buffers, ranges and strict entry order before any native traversal; a
cached canonical flag is insufficient. Workspace limits are explicit
implementation estimates, not total-RSS bounds or guarantees about caller
storage. A complete scientific runner still needs exclusive saved-block
inventory/hashes, supervised resources and independent saved-only replay.

Synthetic tests compare the interval ingredients with the independent
exact-Fraction probe and small full SVD, and exercise 257 unknowns while
rejecting an N-by-N dense allocation. That diagonal streaming check is not
a physical or performance qualification.

## Scaling and a candidate solve

`scripts/_b3_e4_f03_scaled_sparse.py` owns input blocks, supports exactly
three root rows, and uses the held `E0,U0,ell=.46` with

```
D=sqrt(E0/diag(Ks+Kb)); R=diag(1/U0,1/U0,ell/U0)
Kbar=D K D/E0; Cbar=R C D; fbar=D f/E0
H=[[Kbar,Cbar.T],[Cbar,0]]
q=D z_primal; eta=E0 R z_multiplier.
```

Each matrix entry uses left-then-right multiplication followed by division.
Both triangles are retained; there is no averaging. Nonzero entries or
states that underflow to zero are rejected. Integration crosschecks can
reuse an owned primary system's D/R without recomputing alternate scales.
Preparation does not adjudicate skew, rank, integration or positivity.

The bounded candidate solver uses one SciPy SuperLU general factorization,
COLAMD, diagonal pivot threshold 1, disabled equilibration and no iterative
refinement. It performs one candidate RHS solve. The same factor supplies
the one-pass inverse-column stream; attempted and completed certificate RHS
counts are separate. An interrupted or failed stream cannot restart on the
same object. Backend, memory and programming exceptions propagate unchanged.
Public state/operator access returns independent copies.

Raw inverse-evidence budget and known input/workspace limits are checked
before factorization. Factor fill is checked after it exists. That check
cannot prevent a factorization's peak allocation; an external time/RSS
supervisor and frozen factor resource envelope are mandatory for scientific
use. Failed factor/candidate RHS attempts also need the enclosing runner's
journal, since no candidate object is returned after an exception.

The result remains `NOT_QUALIFIED` even if its condition certificate passes.
The separately reviewed positive-quadratic-form proof, integration/rank/work
checks, artifact identity binding and physical convergence remain required.
No positivity factor producer or scientific case family is selected here.

The implementation was checked against the local SciPy/NumPy installation.
API semantics are described in the official [SciPy splu reference](https://docs.scipy.org/doc/scipy/reference/generated/scipy.sparse.linalg.splu.html)
and [NumPy nextafter reference](https://numpy.org/doc/stable/reference/generated/numpy.nextafter.html).
Those pages do not establish an executed environment or scientific accuracy.
