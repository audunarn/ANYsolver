# F03 analytical trace-norm validation v1

22 September 2026. **Nine of nine pure-norm comparisons passed.** This
validates the auxiliary scalar H1-dual evaluator for the registered
Nm=4,8,16 P1/hybrid/enriched rows. It does not establish physical convergence,
native coupling or a continuum inf-sup constant. Endpoint comparison v1
retains its original `UNRESOLVED_AUXILIARY_NORM` decision.

## Evidence and scope

Frozen source: `45d3f1aacb88a73259e226e4a66a9020af886a94`.
Evidence: `.qualification/b3-ge-e4-pl/f03-analytical-norm-v1/` in the isolated
integration worktree. The two norm constructions are an affine-cell Riesz
solution using positive Taylor terms, and an independent 70-digit Decimal
Green-kernel quadrature with frozen orders 12 and 16. No structural
equilibrium or 128-grid calculation occurred in this study.

| Artifact | SHA-256 |
|---|---|
| Registration | `4c4682a1648966d10d7b02317f918be849dd6a3d3375c8d767c3710ca0e68e30` |
| Adjudication | `b524f55f3cff2ba40973851ed125569198ded0b2e5daa3486099e435fab4df18` |
| Completed artifact inventory | `9fe9a15af614c24ff42317d210b6637d94adbe7515a926f752a7dfcb3eb1ab8b` |

The independently reviewed candidate passed 36 integrated focused checks
before evidence-runner corrections, followed by 11 affected checks after
receipt binding, saved-matrix adjudication, one-use execution and parent
thread guards. The final review permitted only this bounded norm study.

The child completed in 1.412 s, exit zero, using at most 63.199 MiB sampled
RSS, within 120 s and 512 MiB. Supervisor and child both used the five
registered thread caps of one; the child recorded actual numerical pools.
Each of three Nm groups saved eleven finite float64 Gram arrays and its
comparison data. Adjudication reopened those arrays and recomputed every
mandatory acceptance measure. Prefixes, identities and hashes are retained.

The independent post-execution audit **accepted this pure norm study**.
It verified all five source hashes, nine rows, 33 saved matrices, raw
events, receipts and artifact hashes, and independently reproduced the
mandatory measures from the saved matrices. No norm construction or
structural solve was repeated in that review.

## Observed accuracy

All candidate and reference matrices admit Cholesky factorization. The
maximum condition number is approximately 11,528 for enriched Nm=16.
No matrix symmetrization, clipping or regularization was used.

| Mandatory measure | Maximum over nine rows | Frozen limit |
|---|---:|---:|
| Relative Frobenius skew | 5.42e-16 | 1e-12 |
| Relative Frobenius difference | 5.18e-16 | 1e-12 |
| Relative operator error | 1.666e-13 | 1e-9 |
| Order-12/order-16 operator change after binary64 conversion | 0 | 1e-12 |
| Endpoint/partition identity discrepancy | 7.78e-16 | 1e-12 |

For oracle Gram B=L L.T, the operator error is
`norm(L^-1*(A-B)*L^-T,2)`, using triangular solves and the full unsymmetrized
error. It bounds relative quadratic-form error and is invariant under
invertible congruence. Zero rounded quadrature change does not claim zero
Decimal truncation error. The Taylor metadata bounds only the local series
tail in exact arithmetic; neither calculation is interval certified.

For context only, the enriched FE64 Gram's measured relative operator
error against the independent reference is 0.00048251, 0.00044191 and
0.00043891 at Nm=4,8,16. Its error is smaller than the previous registered
32-to-64 *change*. The previous rule tested that change and failed; these
new numbers do not retrospectively change the rule or its adjudication.

## Next decision

The validated analytical norm may be used only in a new, explicitly
registered analysis that binds the relevant operator/row/scaling identities.
Existing structural snapshots can support read-only derived analysis where
that new contract expressly permits it. Do not relabel the consumed v1 run
or perform an unregistered structural retry.

The next physical question remains joint shell/beam/interface refinement,
including signed total and partitioned reactions, endpoint atoms, energy
and physical-band transfer. The reduced movement in tip displacement is
encouraging diagnostic evidence, not a selected production formulation.
F03 and G0B remain open; G1 and release remain unavailable.
