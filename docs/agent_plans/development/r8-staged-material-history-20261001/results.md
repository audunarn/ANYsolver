# Staged plastic material/history development — 1 October 2026

Three scoped installed behaviors pass: Q4 with yielding physical beam fibres,
S3 shell J2 with elastic mixed beam families, and simultaneous Q4 J2/generalized
beam yielding. Each completes loading, unloading, reversal, reload, plastic-state
chart reset, checkpoint restoration and continued stepping. These are small
point-connected panels, not aggregate G3/F06 acceptance or practical-scale evidence.

Product remains `9057067d`, unchanged wheel
`0c45666609355e654cb726a0e4e0780d386bccfaafef1209ffd994bdd3b9d09c`.
Latest test SHA is `00668c9409b1f41daffed865a590098b5f5f7cb55de4f60392ac2c075a1f6f3f`.
Every execution verifies all 388 product source/wheel/site modules and effective
one-thread NumPy/SciPy BLAS and Numba settings with JIT disabled; all 210 loaded
product imports resolve to that site. No new wheel is needed for test-only edits.

## Executed scope and reuse

| Case | Absolute endpoint Fz, N | Actual material activity | Passing evidence |
|---|---|---|---|
| Selected Q4 / physical fibres | 1000, 250, -500, 1000 | Beam fibres plastic; shell remains elastic | V5 first case; earlier complete V4 corroborates |
| S3 / mixed native families | 50, 12.5, -25, 50 | Shell J2 plastic; beams remain elastic | V5 second case; earlier V3/V4 corroborate |
| Selected Q4 / generalized beams | 1000, 800, -1000, 1100 | Both histories advance in the same accepted substep | V7 third case |

Each accepted control path is `.5, 1, 2, 3, 4`; each passing case retains 19
detached states/checkpoints across control, rebased, restored and stage-2/3
restart branches. Actual affine programme interpolation is checked independently,
including exact applied-load vectors, current-position force/moment balance,
equilibrium, compatibility, actual histories and material-aware recovery.
Future-programme mutation, failed increments and cancellation before atomic
publication preserve checkpoint bytes, accepted object and observer count.

This is **two retained V5 passes plus one V7 pass**, not an all-green V5 campaign.
V7 modifies only the added-case cancellation site and the recomputed Q4 stress
comparison. The first two cases retain their inputs, equations, controls and
cancellation site; their stronger earlier stress-byte check implies the current
bounded check. Independent review explicitly accepts this reuse eligibility.

The simultaneous case advances both histories at `.5→1`, `2→3` and `3→4`;
`1→2` is elastic unloading in both domains. Maximum shell/generalized-beam
increments at `.5→1` are `1.1108181743e-6` / `9.0203080994e-6`.
Signed plastic histories are retained. Empty fibre-energy recovery for generalized
sections is N/A, never a measured dissipation or total-energy result. Physical
fibre dissipation is the reported last-increment quantity; shell stress contracted
with plastic-strain increment is local backward-Euler plastic work, not global
dissipation. Large plastic/noncommuting F06 coverage remains open: the largest
simultaneous rotation is about `1.69e-4 rad`, commutator `1.03e-9 rad`.

V5's serial campaign took 125.307 s including its failed added case; V7's affected
case took 96.682 s. Sampled process-tree peaks were 179,130,368 / 173,703,168 B,
inside the 600 s / 8 GiB monitored bounds. These are execution observations,
not development-speed or performance qualification claims.

## Preserved failures and explicit test corrections

- V1 incorrectly expected `completed` at every callback. Status follows the
  current adaptive target sequence, independently of whole-programme completion.
- V2 selected historical-corotational Q4 and failed physical moment balance at
  500 N (`4.722357e-6` versus `1e-8`). Independent work review found no reaction
  frame/sign error. Later cases explicitly select the previously accepted full
  algorithmic Q4 map; historical behavior and defaults remain unchanged.
- V3 selected Q4 failed a new near-zero component-relative comparison. Independent
  saved-state analysis established that criterion was not the existing physical
  role metric. V4 prospectively uses unchanged `1e-9` dimensionless parity at fixed
  input force, 2 m length and force×length moment scales. Native retained18 stores
  six forces then twelve moments; point/support6 stores three of each.
- V5's added generalized case waited for a fibre-only safe point and did not cancel.
  V6 uses the existing controller-publication point after complete prospective
  checkpoint construction, before the mixed commit. No solver correction follows.
- V6 then failed an unsupported byte-identity expectation for restored Q4 stress:
  only recomputed layer stress differed, by `2.3283064365e-10 Pa`. V7 retains exact
  checkpoint/material origins, all other Q4 recovery fields and complete S3/fibre/
  energy records; only derived Q4 stress uses the existing E-scaled `1e-9` bound.

All failed executions, original fixtures and decisions remain retained. No
constitutive, load, convergence, checkpoint, public API or default was altered.

## Independent review and remaining work

[Complete three-case review](raw/preparation-review/r8-staged-material-history-v5-independent-review.md)
finds no consequential latest-source defect within this scope. The earlier
[two-case review](raw/preparation-review/r8-staged-material-history-independent-review.md)
also corrects the prior elastic F06 retained-slot interpretation: all 44 original
snapshot hashes and 26 comparison pairs were checked without another solve.
Correct force6/moment12 normalization still satisfies the original `1e-9` bound
(Q4 maximum `4.7098313e-14`, S3 `3.1079565e-13`). Original records remain unchanged.

[Manifest](manifest.json) binds 667 retained files, original paths and the raw
archive SHA `37149deb1a55e0801ba31afca51af36996786581fbe5301cdbf3506a67cca4e7`.
Long pytest path components are shortened only in archival locations; file bytes
and original-path mappings are preserved. Source, fixtures, commands, JUnit,
logs, identities, checkpoints, material records, arrays and reviews are included.

These three behaviors are implemented and installed-tested, independently reviewed
development scope. Simultaneous physical-fibre/J2 and mixed-S3 yielding, large
plastic transport, total energy, broader attachments/supports/topology, loads,
spectra, capacity, external comparisons, scale and release remain open. Formal
F03 is unconsumed; no aggregate gate, production, main merge or publication follows.
