# F03 sparse numerics and full classical recovery: bounded proof results

22 September 2026. **48 distinct current tests pass, with independent
code/mechanics review closed for this bounded batch. G0B remains open and
G1 remains barred. No new physical reference equilibrium was executed.**

Final source is `ade088e99e3108969baf70b27e7f7cc450351229` on
`codex/b3-ge-e4-pl-integration`. The initial implementation commit
`3c4fe3c7117688d0b1f032ef346ef4cb3ce07219` is retained, followed by the
review correction. All changes are private classical research tooling,
tests and derivation records. Native elements, public APIs, defaults and
version 0.4.7 are unchanged.

## Implemented and verified

- An owned sparse scaling/candidate-solve route preserves the held energy,
  displacement and moment scales and recovers the physical dual
  `eta=E0 R eta_hat`. One general LU supplies one candidate RHS and a
  single-use inverse-column stream. A certificate does not change the
  candidate's `NOT_QUALIFIED` status.
- The complete streamed inverse-column certificate uses explicit outward
  interval products/sums and true induced-norm bounds. Square-root bounds
  additionally pass exact scalar inequalities. It retains the original
  condition upper `1e10` and amplified-backward upper `1e-8` limits.
  The 257-unknown synthetic streaming test rejects a global dense allocation;
  it is not a physical-scale or runtime measurement.
- A separate sparse congruence verifier proves a sufficient positive
  quadratic form of the full stored primal matrix, including admitted skew.
  It checks supplied unit-lower/positive-diagonal factors against every
  residual entry, including fill outside the input pattern. It never
  averages the matrix or treats successful LU as a positivity test.
- Full recovered polynomial/cosine functionals now include the signed root
  and tip atoms, station/trace resultants, common-origin band moments and
  exact beam virtual-work identities. The held yaw factor and free root
  slope remain. Six support residual lift actions are available for p>=2;
  they become physical support reactions only after separate equilibrium
  admission. p1 lifts are explicitly unavailable in this helper.

Details and limitations are recorded in the new sparse-certificate,
sparse-positivity and local-recovery draft documents. These are accepted
building-block contracts, not a selected scientific protocol.

## Tests and review

| Final group | Distinct passes | Final preserved log |
|---|---:|---|
| Streamed interval certificate | 22 | `sparse-certificate-root-guarded-ee5057c217f94992854a384cd46233ad.log` |
| Scaled sparse candidate and ownership | 8 | Same final affected 30-test log |
| Sparse positivity and resource guards | 6 | `f03-sparse-positivity-resource-20260922.log` |
| Manufactured full recovery and work | 12 | `local-recovery-guarded-565e2176d75a4328868a25682034c5cb.log` |

Earlier test runs overlap and are not added to 48. Numerical tests use the
five declared thread caps at one, unique temporary logs/basetemps, and no
pytest cache. Synthetic linear solves are present; there are zero physical
reference equilibria and zero native element evaluations in this batch.

Independent mechanics review accepted the full recovery and original
interval reasoning. Independent integration review accepted scaling and
physical dual recovery. The latter reviewer found that a negative mocked
square-root response could satisfy a squared inequality; a red regression
reproduced it before explicit domain/response guards fixed it. Final review
closed the finding on the corrected source hashes. This was an injected
backend failure, not an observed library failure.

Parent review of the separately implemented positivity helper required
individual rational-operation accounting, earlier work caps and a Python
storage estimate. Those changes passed their focused tests and inspection.
An initial recovery test also used the wrong grid for a collapsed-interval
expectation; the corrected test uses the previously accepted represented
pad-edge grid. All failed, intermediate and final logs are preserved.

## Immutable evidence

`.qualification/b3-ge-e4-pl/f03-local-numerical-proof-v1` contains 23 bound
files plus its inventory: 11 source/doc/test copies, all 10 raw logs, a
manifest and a record of independent reviews. Complete byte/hash read-back
passed. Do not extend or overwrite this root.

```
inventory 43f9a1c950acc315c6fed28548f5f6e40a822b934d566ae5f4eb6b1185817100
manifest  1f31a325fca4f7b70212adaf6e11c0b73c120babc38c24f455e23c4dd2ec188b
review    a733d04f4fe8afb01dc204803fe4f3cf087736ab5679a68f454c3d0fde84c1dc
```

Every earlier consumed scientific record, failed outcome and physical HOLD
remains unchanged. Main was observed clean at `be41a77a`; local main and
cached origin/main matched. No fresh remote fetch, promotion or release ran.

## Remaining work and exact next action

Implement and verify a bounded sparse producer for the supplied positivity
factors, then connect the existing building blocks through numerical
acceptance, integration/rank/work checks and saved-state/adjudicator
bindings. No factor producer or scientific certificate method is yet selected.
Factor fill caps are post-factor observations; external time/RSS supervision
and the full `8*N*N` raw inverse-column evidence budget remain mandatory.
Decimal cosine displays are not certified error bounds, and p1 support
recovery needs an explicit disposition in the eventual reference protocol.

Then freeze a conforming nested physical case family, integration rules,
resource limits, saved inventory and adjudicator, and obtain independent
protocol review before a new one-use scientific registration. Do not repeat
old executions, extend global polynomial degree automatically, weaken
physical criteria or treat these synthetic results as reference convergence.
The native B3-GE/B2 full-vector, shear/drilling and other G0 foundations,
mandatory external comparisons and later programme gates remain open.
