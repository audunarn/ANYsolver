# Saved-only sparse numerical equilibrium checks

This bounded candidate audits supplied classical primal arrays without
reassembling the physical model, solving equilibrium, or accepting a reference
case. It first calls the independent physical scaling and saved-state binder
with a mandatory `H_z` action. A failed binding makes the result HOLD.

Let `K=Ks+Kb`, `Kplus=Ksplus+Kbplus`, `D` be the supplied positive primal
scaling, `R=diag(1/U0,1/U0,.46/U0)`, and `E0=F0*U0` from the held spatial
contract. The six scaled blocks are the actual candidate binary64 results
of `((Aij*Di)*Dj)/E0` for `A=Ks,Kb,K` and their three independently
integrated counterparts. The products and division round in that fixed
order. Their stored entries are then treated as exact operands for norm
comparison; ideal exact scaling would measure a different skew. For each primary
block `A`, the increased-integration check is

```
||Aplus-A||F/||A||F <= 1e-11       when ||A||F > 0;
||Aplus-A||F        <= 1e-11       when A = 0.
```

The three separate gates prevent cancellation between shell and beam
differences. Every one of the six scaled blocks independently satisfies
`||A-A^T||F/||A||F <= 1e-12` for nonzero `A`, with an absolute skew norm
for zero `A`. Both stored triangles are used without averaging.

The same supplied arrays give three further frozen numerical checks:

```
maxabs((H z-b)_primal)/max(1,maxabs(b_primal)) <= 1e-10;
maxabs(R C q)                                  <= 1e-10;
abs((q^T Ks q+q^T Kb q)-q^T f)
    /max(E0,abs(q^T Ks q+q^T Kb q),abs(q^T f)) <= 1e-10.
```

The shell and beam physical energy actions are accumulated separately. The
quadratic form of the rounded sparse sum `Ks+Kb` is only a diagnostic;
adding physical entries first can lose a small block contribution.
The exact real values of each finite saved binary64 entry are accumulated
with bounded rational sparse row sums. Ratios are compared as exact squares
against the frozen limits; displayed magnitudes are outward upper bounds.
The distinct status flags remain authoritative at a threshold boundary.
All shared inputs are owned once before the binder call and those same copies
are used for the subsequent metrics. The complete input hashes include both
increased-integration physical blocks. The preflight inventory covers six
physical blocks, including both derived sums, and the report records their
actual stored-entry count. Explicit positive resource caps cover validated
sparse inputs, temporary transposes/sums, conservative Python workspace, and rational
numerator/denominator and cumulative bit counts. No global dense matrix,
factorization, fresh inverse, or saved decision dictionary is used.

These checks do not establish rank, positivity, conditioning, integration
error outside the saved block comparison, exact interface trace, loads and
reactions from a physical reference, or product/native qualification. Those
need separate independently reviewed evidence and supervised execution.
