# F03 broken physical trace graph screen v1

21 September 2026. **Exploratory; no inf-sup or F03 qualification.**
Independently measure whether the prior operator-adapted primal norm
controls a physical trace with native cell-yaw jumps. Use the ten explicit
meshes from the signed-norm run: Q4/S3 × joint `(Nb,Ns)=(4,4),(8,8),(16,16)`
and fixed-beam reaches `(8,1),(8,64)`. Freeze source, imported integration
worktree, dependencies, one BLAS thread, ignored Numba cache, 1,200-row
dense cap and exclusive result root before execution.

Use the supported scaled three-channel gap `g(s)`, with yaw multiplied by
`ell=.46 m` so all entries are metres. On the union of native half-cell and
shell trace breakpoints, define the dimensionally consistent *broken H1*
graph seminorm

`G(q)=Σ_I (1/L0) ∫_I |g|² ds + L0 ∫_I |g'|² ds
      + Σ_native interior j (L0/h_j)|g(s_j+)−g(s_j−)|²`.

Here `L0=1 m`. The native translation trace is continuous; its retained
cell yaw is piecewise constant and its one-sided jump is counted. Evaluate
exact interval slopes from two interior stations on each overlay interval,
check affine midpoint identity, use four-point integration for the L2 term,
and extrapolate one-sided yaw rows to native knots. Do not assume a
continuous H1 trace across yaw jumps or omit the jump term.

Form the operator-adapted SPD norm `H=Tᵀ diag(Ke,|Krr|)T` from work-scaled
exact retained elimination. The largest generalized eigenvalue of
`G/u0²` against `H` gives a finite-mesh trace-continuity upper bound;
report its trend over joint and one-sided refinement. The graph is
semidefinite because many primal modes have no trace; do not compare its
zero modes as a full-norm equivalence or call the smallest resolved mode a
uniform lower bound. A physical multiplier dual norm and a full inf-sup
check in it remain separate work. This diagnostic cannot select a mortar
space or close G0B even if its upper bound stays finite on these meshes.
The relative `1e-10` graph-rank cutoff applies to generalized eigenvalues,
not singular values. A raw jump-row Frobenius diagnostic has mixed coordinate
units and must not be interpreted as a physical jump amplitude.
