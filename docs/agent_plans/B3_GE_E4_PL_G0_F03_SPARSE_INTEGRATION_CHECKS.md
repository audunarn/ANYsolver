# F03 sparse integration perturbation checks: synthetic design

This helper verifies numerical sensitivity of two already primary-scaled
classical KKT descriptions. It neither assembles the physical law nor proves
that `D` and `R` were constructed correctly. A future numerical owner must
bind the primary and alternate physical operators, scaling identities and
these input SHA256 digests before using it in scientific evidence. It does
not select a certificate method or authorize a run.

The owned, canonical sparse matrices have shape `(n+3,n+3)` with exactly
three physical root rows and an exact zero lower-right multiplier block.
Both right-hand sides have exact zero root entries. The complete inverse
column evidence is independently reverified against **the supplied primary
H, b and z** through the shared candidate-A interval checker; an arbitrary
reported inverse norm cannot enter the perturbation calculation. The
alternate system receives no equilibrium solve. Input hashes bind canonical
CSR data, indices, pointers and shape, and exact float64 b, bplus and z.
The returned scope is explicitly
`NUMERICAL_PERTURBATION_ONLY_NOT_SCALING_ADMISSION`.

A rowwise two-pointer union processes every stored entry of H and Hplus,
including entries absent from either pattern and both independently stored
C triangles. Exact Fractions lift their binary64 bits and accumulate
`dH²=||Hplus−H||F²`. The same method gives `db²=||bplus−b||2²`.
For the available combined K block and both C orientations, compare exact
`||blockplus−block||F/||block||F` when the primary norm is nonzero and the
absolute norm otherwise against the unchanged `1e−11`. For f, compare
`||fplus−f||∞/max(1,||f||∞)` against `1e−11`, retaining the earlier load
convention. These are independent of the full H and b perturbation norms.
Because H contains only the combined K, a scientific owner must **also**
verify the original separate shell and beam energy integration differences;
this helper cannot silently replace those checks.

Exact squared differences are converted to binary64 upper bounds by
outward conversion followed by the shared scalar square-root verifier,
which checks its bound by exact rational squaring. The saved primary
`inverse_two_upper=B` gives a downward-enclosed `sigmaL≤1/B`. Shared
interval arithmetic yields `zL≤||z||2≤zU` and an upper enclosure of
`||Hplus z−bplus||2` from every high-order sparse row, including zero-target
rows. Rational arithmetic on the chosen outward floats bounds

```
alphaU >= dH/sigmaL
deltaU >= (dH*zU+db)/(sigmaL*zL)
relative_solution_bound_upper >= deltaU/(1-alphaU).
```

Require `alphaU<1` and the last bound `≤1e−6`. If alpha reaches one, the
last bound is null with a violation, never a finite substitute. A failed
primary certificate, relative block check, nonfinite calculation or resource
bound does not trigger a second method or adjusted threshold. This bound
describes integration coefficient and dual sensitivity, not physical output
accuracy.

Explicit sparse, union, rational bit and Python workspace budgets precede
the complete inverse-block stream. Counts and hashes are returned with the
result. The Python estimate is a conservative synthetic inventory charge,
not a portable allocator or measured peak-RSS guarantee. A future
scientific protocol needs its own process supervision and full raw binding.
