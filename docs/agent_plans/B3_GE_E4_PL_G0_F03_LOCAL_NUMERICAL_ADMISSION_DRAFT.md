# F03 local reference: numerical-admission design for independent review

This is a design proposal, not a registration, case inventory, resource
allocation, or execution instruction. It preserves the classical represented
finite-pad law and all earlier consumed outcomes. Neither sparse certificate
method below is selected yet. Compare them on bounded synthetic matrices,
then freeze one method and its resources before any scientific case. A failed
bound does not authorize a second method, refinement, rescaling, or retry.

The controlling mechanical foundation is
`B3_GE_E4_PL_G0_F03_LOCAL_OPERATOR_CONTRACT.md`; its accepted design is
`B3_GE_E4_PL_G0_F03_LOCAL_REFERENCE_DESIGN_DRAFT.md`. The old numerical limits
come from `B3_GE_E4_PL_G0_F03_PRIMAL_RITZ_PROTOCOL.md` and
`scripts/_b3_e4_f03_primal_checks.py`. No old numerical module is invoked by
this proposal. No actual state, assembly or solve was evaluated to write it.

## Fixed coordinates, scaling and unmodified matrices

Let K=Ks+Kb on the supported shell coordinates and C=A(0), with exactly
three physical root rows. Keep L0=1 m, F0=1 MN, M0=F0 L0, ell=.46 m,
U0=F0/(210e9*.07), and E0=F0 U0 in their held represented convention.

```
Dii=sqrt(E0/Kii) > 0
R=diag(1/U0,1/U0,ell/U0)
Kbar=D.T K D/E0, Cbar=R C D, fbar=D.T f/E0
H=[[Kbar,Cbar.T],[Cbar,0]], b=[fbar,0]
z=[D^-1 q,eta_hat], eta_phys=E0 R.T eta_hat
```

This remains the original energy-diagonal solver coordinate change. It does
not change the physical comparison norm. Bind D to the positive square root
at relative 1e-12; retain primary D and R for every integration crosscheck.
Require finite positive diagonal entries and finite scaled data. No diagonal
shift, penalty, dropped root, pseudoinverse or post-failure matrix repair is
allowed. Full stored H, including any admitted skew, is the matrix used in
the condition and backward-error checks.

The intended energy assembly should create both symmetric entries from one
declared scalar contribution and preserve identical scaling/order on each
pair. This is an assembly definition, not averaging a failed matrix. Check
both stored triangles and retain the 1e-12 relative skew limit for each
nonzero Ks, Kb and K block. A zero block needs its absolute scaled check.
Keep a successful positive-definiteness check of the unmodified Kbar.
Use a reviewed sparse Cholesky/LDL positive-inertia path after full symmetry
checks; a successful indefinite LU alone does not establish this property.
Backend availability and factorization semantics must be verified before
registration. If only approximate symmetry is provided, define and review
the positivity certificate explicitly instead of silently ignoring a
triangle. The full-H condition certificate never uses a repaired H.

## A real upper bound on the 2-norm condition number

An iterative 1-norm estimate, reciprocal-condition estimate, or a few
Lanczos singular values do not give the required upper bound. They may be
recorded as diagnostics but cannot decide this gate. For upper bounds
`h1>=||H||1`, `hi>=||H||inf`, `b1>=||H^-1||1`, `bi>=||H^-1||inf`, use

```
inverse_2_upper = sqrt(b1*bi)
condition_2_upper = sqrt(h1*hi*b1*bi).
```

These are genuine 2-norm upper bounds, not renamed 1-norm estimates.
Admit only `condition_2_upper <= 1e10`. Record the upper-bound name and
method, all ingredients, and the underlying matrix/factor identities.
An upper bound above 1e10 means this numerical admission is HOLD; it does
not prove that the actual condition exceeds 1e10. A pessimistic bound is
not a reason to relax the old threshold or switch methods during a run.

### Candidate A: complete inverse-column residual certificate

Using the one frozen sparse factorization, compute every approximate inverse
column y_j from the prescribed RHS e_j. These are N certificate RHS solves,
distinct from the one physical equilibrium RHS. Preserve their count. Let
Y=[y_j] and E=I-HY. Stream column sums and row absolute-sum accumulators to
obtain verified upper bounds y1, yi, e1, ei on their induced norms. If both
e1<1 and ei<1, the Neumann identity H^-1=Y(I-E)^-1 gives

```
b1 = y1/(1-e1), bi = yi/(1-ei).
```

There is no need to materialize E. Every H*y_j residual must include every
stored sparse entry, including zero-target rows. All arithmetic needed for
the bounds must have a proved outward enclosure. Ordinary rounded residuals
and an unexplained epsilon multiplier do not establish an upper bound.

This is a research certificate, not a native production inverse path. Its
work is O(N*(nnz(H)+nnz(L)+nnz(U))) and its complete saved inverse-column
evidence occupies 8*N^2 raw bytes. Streaming reduces live memory only.
If the independent adjudicator must verify from saved arrays without a
factor solve, save all Y columns in bounded, exclusively written blocks.
Preserve block order, exact shape/dtype, hashes, and the full column inventory.
Do not report compressed storage as a worst-case raw-storage bound.

### Candidate B: factor-comparison certificate

Work in the archived row/column permutation convention in which
`Htilde=L*U+Rfac`. Permutations preserve the induced 1/infinity norms.
Hidden diagonal equilibration must either be disabled or explicitly included
in every inverse norm and residual formula; do not certify the equilibrated
matrix under the name H.

For each triangular T, define comparison C(T) with diagonal |Tii| and
off-diagonal -|Tij| in the same triangular positions. Nonzero finite pivots
are required. Its inverse is nonnegative and bounds |T^-1| entrywise.
Compute outward positive recurrences, without constructing an inverse:

```
C(L) v = 1,       C(U) w = v       -> nu_inf = max(w)
C(U).T v = 1,    C(L).T w = v     -> nu_1   = max(w).
```

For example a forward row is
`v_i=(rhs_i+sum_(j<i)|Lij|*v_j)/|Lii|`, with an upper rounding direction.
The two recurrences bound the norms of the composed inverse; using products
of separate triangular norm bounds is valid but can be less sharp.

Enclose Rfac=Htilde-LU independently from the saved factors and matrix.
Traverse complete sparse row products, accumulating each output entry before
absolute values; include fill outside H's pattern. With verified residual
norm bounds r1, ri, require nu_1*r1<1 and nu_inf*ri<1, then use

```
b1=nu_1/(1-nu_1*r1), bi=nu_inf/(1-nu_inf*ri).
```

This avoids N inverse-column solves and N^2 inverse evidence. It can be much
more pessimistic because absolute triangular recurrences discard sign
cancellation. It still needs factor storage, complete product-residual work,
and a finite verified arithmetic path. A large or overflowing recurrence is
HOLD, not a successful infinite bound or permission to try candidate A.

## Verified arithmetic and a bounded dense oracle

Treat the saved finite binary64 entries as exact real input numbers to the
certificate. A straightforward verification prototype uses directed interval
products and sums: bracket each rounded product by the adjacent floating
numbers, add lower and upper endpoints with outward rounding, and derive
absolute sums from the resulting intervals. Handle subnormals explicitly;
reject overflow, unsupported flush-to-zero behavior or nonfinite bounds.
Apply the same discipline to positive recurrences, denominators, products
and square roots. A faster sparse residual/error-bound implementation needs
its own arithmetic proof and tests before replacing this reference method.

Use full dense SVD only on synthetic H with N<=256, with an explicit scratch
ceiling checked before dense conversion. Compare each candidate certificate
against full singular values and backward error; the upper bounds must not
undershoot. Include scaled SPD-plus-three-root KKT matrices, nonsymmetric
perturbations that exercise both stored triangles, nearly singular roots,
large cancellation in LU, adverse permutations/equilibration, singular
factor failures, and deliberately pessimistic but valid bounds. Do not
calibrate acceptance by replacing the old 1e10 or 1e-8 limits. Synthetic
method comparison precedes selection; no scientific case receives a dense
fallback after a failed sparse certificate.

The first executable exact-Fraction comparison deliberately enforces the
tighter synthetic bound `N<=64`. It validates owned CSR/CSC buffers before
any sparse conversion, then uses dense rational products for the small
proof. This is not either candidate's scalable sparse implementation. Its
outward square-root conversion may fail for an extreme squared value even
when the root itself is representable; an explicit arithmetic failure is
retained, never treated as a successful certificate.

## Backward error, integration amplification and unchanged checks

For the full residual r=H z-b, enclose its 2-norm above by rU. Bound the
2-norms of z and b below by zL and bL. A usable lower bound hL on ||H||2 is
the maximum of its column and row 2-norms, evaluated downward. Then

```
backward_error_upper = rU/(hL*zL+bL)
condition_2_upper * backward_error_upper <= 1e-8.
```

An upper bound on ||H||2 in this denominator would underestimate backward
error and is forbidden. Retain separately the ordinary measured residual
and normwise error under honest names. A zero/nonfinite lower denominator
fails; the expected loaded fixture has nonzero b. Verify the unchanged
stationarity infinity residual/max(1,||fbar||inf)<=1e-10 and
||R C q||inf<=1e-10 independently of this full-system check.

Set sigmaL=1/inverse_2_upper. With Hplus,bplus in the primary scaling,
obtain upper bounds dH>=||Hplus-H||F, db>=||bplus-b||2 and zU>=||z||2.
Use the conservative original perturbation gate

```
alphaU=dH/sigmaL < 1
deltaU=(dH*zU+db)/(sigmaL*zL)
deltaU/(1-alphaU) <= 1e-6.
```

Record the Hplus*z-bplus residual without a second equilibrium solve.
If alphaU>=1 the bound is undefined: retain a violation and null bound,
not a manufactured finite value. The interpretation remains coefficient/
dual sensitivity to integration, not physical output accuracy.

Retain all numerical limits: own-block skew 1e-12; scaled integration K/C/f
differences 1e-11; positive-D binding 1e-12; saved state/action binding
1e-11; normalized root and stacked-slope singular ratios at least 1e-10;
energy/work identity 1e-10; virtual work and density/band recovery 1e-10;
root/tip partitions 1e-11; independent edge-reaction routes, admissible-lift
invariance and global balance 1e-8. Preserve the existing physical scales,
signed root forces/moments, endpoint atoms, band wrenches and full-functional
criteria. Passing numerical admission is not passing physical convergence.

## Nesting, rank and integration requirements

Shared tensor Q2 is a subspace of shared tensor Q3 on the same rectangles,
although their interpolation nodes are not nested. For conforming h
refinement, every fine rectangle must lie in a coarse rectangle and its
degree must be at least that coarse degree. Refining a Q3 cell into Q2 cells
does not generally embed the cubic space. The present tensor-grid helper
has no hanging-node mechanism; do not silently add one.

Construct exact prolongation by evaluating the parent tensor Lagrange basis
at each fine node in the exact local chart. Resolve a node on a parent edge
through the shared trace identity; both adjacent choices must agree. Keep
component order and prescribed-zero edges. Before numerical admission check
the exact pose identity on the common station partition and Cfine P=Ccoarse.
Check P.T Kfine P=Kcoarse and P.T ffine=fcoarse using the declared integration
comparisons. These prove internal nesting/parity, not continuum accuracy.

Establish exact root rank 3 and augmented transverse-root-slope rank 4 on
the smallest proposed space and verify the scaled numerical ratios for
every admitted description. Root rank alone is insufficient. Test the
small 3-by-n and 4-by-n rows directly; do not form a large dense global
matrix merely for these rank checks.

On an event interval Qp pad translations have degree <=p+1 and yaw <=p+2.
Thus axial energy has degree <=2p, bending <=2p+2, and shear <=2p+4. A beam
Gauss rule with p+3 points integrates the complete polynomial energy exactly
in real arithmetic (five points for p2, six for p3). A fixed independent
p+4 rule is used by the bounded assembly proof (also polynomial-exact).
An independent exact coefficient-pair integral checks the same blocks.
Exact polynomial Gram integration
is another admissible primary route if selected and bounded beforehand.
Shell tensor energy has per-axis degree <=2p; p+1 tensor Gauss points suffice
for a separate check of the exact shell helper. Apply rules separately on
every exact positive station interval; use local tau and preserve its width.

Integrate the constant load contribution exactly where convenient, and
freeze cosine-load rules 48/64 on each interval with the held frequency and
local addition formula. Compare loads and load work with primary scaling
at their existing limits. A zero/subnormal required integration weight is
an explicit numerical admission failure, not a deleted interval. The
separately accepted piecewise full-H1 norm retains its own 48/64 check and
1000^2 floor. No automatic higher rule is introduced here.

## Resource inequalities to freeze with the selected method

Let N=n+3, ZH=nnz(H), ZL/ZU be factor nonzeros, T be simultaneous COO
contributions, and m_i the active primal trace support on interval i.
Topology preflight must report max(m_i), sum(m_i^2), shell/beam/root pattern
unions and their growth. A fixed physical footprint may make these grow
quadratically. Sparse containers do not imply bounded incidence or linear
storage. Numeric zeros must not be assumed when establishing these bounds.

Use a conservative float64/int64 CSC size
`CSC(Z,N)=16*Z+8*(N+1)` bytes and `COO(T)=24*T` bytes. Sum every simultaneously
live primary/cross/difference matrix, assembly buffer, conversion workspace,
factor, permutation and vector; do not count only the final H. Include
Python/container/rational storage and the existing graph-bitset bound.
Report exact-rational object counts and aggregate integer bits; include
temporary blocks before conversion. Factor fill and native workspace need
separate hard bounds and measured peak RSS. A dense L/U ceiling is a valid
worst case, not predicted actual fill.

Candidate A additionally needs 8*N*B bytes per live inverse-column block,
O(N) norm/residual accumulators, exactly N certificate RHS solves, an
explicit N*(ZH+ZL+ZU) work bound, and 8*N^2 raw evidence bytes. Include both
producer and independent verifier work/storage. Candidate B additionally
needs a bound on complete sparse-product paths
`Wprod=sum_k nnz(L[:,k])*nnz(U[k,:])`, one full residual-row workspace of
up to N entries, recurrence/residual accumulators and factor evidence.
Wprod and actual factor fill may themselves be large.

Freeze Nmax, contribution/nnz/fill/product-path caps, exact-object bytes,
archive bytes, RAM and time only after comparing the certificate designs
and candidate topology envelopes. This draft assigns no default that
silently excludes the preferred local family. Fail a preflight before the
corresponding allocation/work. The future registered process must also
supervise factorization RSS/time; a resource failure preserves its terminal
receipt and does not authorize a smaller substitute case. None of these
research certificate choices changes the larger native sparse requirements.

Before a scientific protocol can be accepted, the selected method, outward
arithmetic, sparse backend, one-use evidence/verifier contract, admissible
space family, resource fields and all existing physical gates still need
independent implementation review.
