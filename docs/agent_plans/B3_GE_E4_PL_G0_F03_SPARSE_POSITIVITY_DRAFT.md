# F03 local primal: candidate sparse positivity certificate

This is a sufficient **positive-quadratic-form** certificate for the
**unmodified, supported, scaled** classical primal `Kbar`. It does not select
a scientific factor backend or authorize a case. A successful generic sparse
LU factorization and a solver label of “SPD” are not positivity certificates.
The separate relative-skew gate `||Kbar−Kbarᵀ||F/||Kbar||F≤1e−12` remains
mandatory. The certificate retains both stored triangles, allows nonzero
skew within that limit, and neither averages nor changes `Kbar`. It does not
claim symmetric-matrix eigenvalues or inertia for a nonsymmetric matrix.

Take an independently provided complete symmetric permutation `P`, unit
lower triangular sparse candidate `L`, and strictly positive diagonal `d`.
Treat every saved finite binary64 entry as an exact rational. Compute the
**full** sparse residual, including entries outside the input pattern and
including any admitted skew,

`R=P Kbar Pᵀ − L diag(d) Lᵀ`, `r1=||R||1`, `ri=||R||∞`.

For `C(L)` with unit diagonal and off-diagonal `−|Lij|`, positive triangular
recurrences `C(L)v=1` and `C(L)ᵀw=1` give
`linf=max(v)>=||L^-1||∞`, `l1=max(w)>=||L^-1||1`. These recurrences are
evaluated exactly in the synthetic prototype. Let `dmin=min(d)>0`. Then

`δ² = (l1 linf / dmin)² r1 ri`.

If `δ²<1`, `B=L diag(d) Lᵀ` is positive definite and
`||B^-1/2 R B^-1/2||2 ≤ (l1 linf/dmin) sqrt(r1 ri)<1`. For every real
nonzero `x`, including when `R` has skew, `|xᵀRx|<xᵀBx`; hence
`xᵀ(P Kbar Pᵀ)x>0`. This is only a sufficient quadratic-form test.
`δ²>=1`, nonpositive pivot, missing factor, skew above the retained gate,
or unresolved fill/resource preflight yields HOLD, not an indefinite-matrix
conclusion.
The certificate never changes the separate KKT condition-2 bound.

Preflight sizes before product work. A column `k` of `L` with `m_k` stored
entries contributes `m_k²` ordered products to `L diag(d) Lᵀ`; bound
`Σ_k m_k²`, factor/input nonzeros, result/residual pattern union, exact
rational count and total integer bits, row workspace, and time/RSS. Stream
one column at a time but retain the complete residual with its full pattern
for an independent raw replay. No dense global matrix or inverse is needed.
The synthetic implementation gates a deliberately conservative Python-side
workspace estimate **before** exact row/pattern allocation: 1024 bytes per
declared row, factor and pattern slot plus two bytes per permitted cumulative
integer bit. It checks every new rational term and running sum, including the
factor diagonal and triangular-comparison recurrence. This estimate bounds
the declared synthetic object inventory; it is not a measured peak-RSS or a
portable Python allocator proof. A scientific protocol must additionally
supervise measured RSS and freeze a reviewed worst-case runtime allocation.
An implementation consuming independently validated owned CSR data must bind
that validation and the original entry order; hidden equilibration and
unrecorded permutations are inadmissible. Sparse factorization may produce
a candidate, but the congruence identity is verified from archived factors
and `Kbar`, including all fill. Resource caps and factor producer semantics
still require review before any scientific execution.
