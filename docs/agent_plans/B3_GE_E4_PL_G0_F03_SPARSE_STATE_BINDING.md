# Candidate sparse physical scaling and saved-state binding

This bounded helper checks supplied arrays for the independent classical F03
research fixture. It does not assemble physical elements, establish their
correctness, solve an equilibrium, or accept a reference result.

For physical shell and beam stiffness `Ks,Kb`, root map `C` with exactly three
rows, load `f`, positive diagonal `D`, physical state `(q,eta)` and scaled
state `z`, set `K=Ks+Kb`. The held constants come from the independently
represented spatial contract: `E0=F0*U0` and
`R=diag(1/U0,1/U0,.46/U0)`. The supplied scaled KKT and RHS must contain

```
H = [[D K D/E0, (R C D)^T], [R C D, 0_(3x3)]],
b = [D f/E0, 0_3].
```

Both constraint triangles, every load entry, and every nonzero KKT entry are
compared. This *particular candidate* fixes the binary64 entry arithmetic:
`((Kij*Di)*Dj)/E0`, `((Caj*Ra)*Dj)`, and `(Di*fi)/E0`.
The independently produced `K` is the canonical sparse sum of the owned
physical input matrices. Nonzero entries require exact float parity; stored
versus implicit zero and the sign of zero do not change the mathematical
entry. This is a deliberately restrictive arithmetic identity, not a new
floating tolerance. An alternate scaling order must be independently
reviewed before it can enter a registered protocol. The input hashes retain
raw canonical storage, including any explicit zero.

The frozen scaled-state bounds remain: `D>0` and relative `D` agreement
within `1e-12`; `max|q-D z_primal|/U0 <= 1e-11`;
`max|eta-E0 R z_dual|/F0 <= 1e-11`; and
`max|H z - saved_H_z| <= 1e-11` in scaled action coordinates. The positive
`D` comparison is made without trusting a floating square root: for each
positive `Kii`, exact binary64-lifted rational arithmetic tests
`(1-eps)^2 <= Di^2 Kii/E0 <= (1+eps)^2`, `eps=1e-12`.
The other state and complete action differences are also exact rational
operations on the finite saved binary64 operands, followed by outward
reporting. A missing saved action is explicitly partial, never a completed
binding. A supplied action over the unchanged threshold is HOLD.

Input CSR/CSC structure, array dimensions, finite values, the combined
sparse pattern, and a conservative verifier workspace estimate are checked
against declared budgets before native sparse sum or block construction.
Every exact rational result is checked against per-value and cumulative bit
limits. The reported hashes bind the supplied physical and scaled arrays;
no cached inverse, factor, or scientific state is treated as authority.
Separate gates must still establish physical operator derivation, root and
slope rank, block energy checks, numerical factor/inverse certificates,
integration sensitivity, and supervised execution.
