# Retained controlled-history and objectivity development closeout

Final fixture/test freeze: `c945a0d35d0c327a5bc40d0268bfa2a2ab9753a3`.
Tree: `a5b903f3657438cca7d3995170d7354ca62615fa`.
Controller remains `fd42d3e84d82a3a65418fad5d3b29a7189caf371`.
Branch: `codex/ge-beam3-curved-moment-reference-v1`.

The registered private gate passed its corrected rehearsal and two complete
deterministic repeats. It establishes the tested controlled generalized plastic
histories and objectivity/covariance checks, not general beam qualification.
There is zero `src/` delta from prior closeout
`05a6aae7a53e923611c1add31039336228a99d8e`. Existing beam/shell mechanics,
section laws, controllers, tolerances, recovery, state schemas, defaults,
dependencies and public routing are unchanged.

## Preserved protocol finding

Initial freeze `4a8748983d946fbd859cca815c35a709eb44556b` passed its two
unloaded rigid-motion checks but failed the scalar unloading assertion. The
original 0.0005 -> 0.0002 displacement step correctly crosses into reverse
plastic flow; its scalar plastic increment is 4.558376629742179e-05, not zero.
No actual plastic controller campaign had run at that freeze.

The successor adds an intermediate 0.00045 axial target and 0.079 curved target
to observe elastic unloading explicitly. All original targets remain in order.
No failed case, history segment, load, material or acceptance threshold was
removed. The initial failed smoke, its source and complete logs remain archived.

## Separate accepted inventories

| Lane | Tests | Science files | Material station checks |
| --- | ---: | ---: | --- |
| Unloaded rigid motion and scalar reference smoke | 3 | 2 | Not a material-history lane |
| Straight axial plastic history | 1 | 7 | 8 stations at each of 8 targets |
| One-macrocell coupled curved history | 1 | 7 | 8 stations at each of 8 targets |
| Two-macrocell coupled curved history | 1 | 7 | 16 stations at each of 8 targets |
| General rotated/translated controlled history | 1 | 5 | Full 8-target field/history comparison |
| Large dyadic translated/permuted history | 1 | 5 | Full 8-target field/history comparison |
| Plastic cancellation and rehashed corruption guards | 11 | 5 | Accepted plastic prefix |
| Existing translation-controller regression | 41 | 15 | Previous gate, unchanged bytes |

Each actual-history case includes plastic loading, elastic unloading, reverse
plastic flow, nondecreasing accumulated history, independent 96-decimal primal
section checks, force/moment/work balance, native recovery, full-prefix restart
and unchanged final-state replay. The axial case additionally follows an
independent scalar return map. Rejected and cancelled continuation cannot
publish a trial state or mutate the prior accepted plastic history.

The translation-controller suite's fifteen scientific files match its bound
`12202be` archive exactly. The separate earlier nineteen-file nodal-force
regression was not rerun in this gate.

## Numerical observations

| Specimen | Maximum station-oracle error | Loaded rigid-motion error | Directional tangent error |
| --- | ---: | ---: | ---: |
| Axial | 1.38778e-17 | 1.31025e-16 | 1.31001e-12 |
| Curved | 1.38948e-17 | 4.67928e-16 | 9.26718e-10 |
| Connected curved | 1.44082e-17 | 9.66827e-16 | 2.60588e-9 |

Station/rigid/covariance acceptance remains 1e-11 normalized error; the
independent directional-tangent threshold remains 1e-7. Loaded objectivity
superposes common current rotation/translation WITHOUT rotating the reference
geometry. Coordinate covariance separately rotates reference/current frames,
forces and control direction, with the correct retained-variable transport.
The general pose maximum error is 4.278331150921217e-12; the exact cyclic
permutation with translation (2^30,-2^29,2^28) gives 2.1487695367339634e-12.
Compensated coordinates are compared as dyadic sums. This does not claim to
recover input geometry already lost through external coordinate rounding.

## Determinism and bounds

Both repeat cycles cover the seven new lanes above; the old-controller lane is
the separate rehearsal regression. Every one of the 38 new scientific files
matches the corrected rehearsal and the other cycle exactly. Both canonical
aggregates are 5,139 bytes, SHA-256
`727BAD633C41DB7F76977F64FCEF9848F26A1C60AA855F6AE0999DD8EA541FD1`.

Cycle A spanned 110.085871 seconds; B spanned 115.110689 seconds. The complete
rehearsal (including its separate regression) spanned 257.445749 seconds.
Longest child was 111.7960252 seconds. These timings are diagnostics, not a
general performance claim. Peak concurrency was three, one numerical thread
per child, 24 GiB/tree, 600 seconds/child, 120-second CPU-inactivity and
1800-second wave limits. All process trees are empty; nothing was retried.

## Archive

`C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-controlled-history-c945a0d-20260908`

- Manifest: 40,424 bytes, SHA-256
  `6B670D97314950E1CB449EFAE40F2552081BE3A377F0D24A464FDF4DBF2EC8C4`.
- Audit: 24,702 bytes, SHA-256
  `EBC269FECA9E3EBE4D50C5D6AF1F5AC88106284DB5815B0A06C2F93DB561521E`.
- All 311 manifest entries verified during staging and external copy.

The failed first smoke, both source freezes, independent oracle, corrected
rehearsal, raw progress/logs/receipts and both complete repeats are preserved.
Original temporary data and the verified workspace transfer mirror remain.
Do not rerun archive creators against the exclusive completed destinations.

## Next gate and full goal

Implement retained objective arc-length continuation with distinct Program,
State and checkpoint authority. The older nested/Schur native arc is background
only. Its accepted-origin Exp-coordinate row cannot be copied directly into
the retained solver's CURRENT spatial left-increment coordinates. Freeze and
test the correct current-spatial frame-chord first variation, full bordered
predictor/corrector, remaining-correction gate, orientation and complete replay.
Then execute bounded real curved/post-limit cases against independent references.

Arc/postbuckling, full fibre-section/solver parity, practical scale, public
FEModel/state and installed opt-in integration, complete environment attestation,
independent review and objective eccentric/curved shell connections remain open.
Independent review is PENDING. No production, publication or activation claim.
Full goal remains active and incomplete. NO_GO_PRODUCTION_RESTRICTION_UNCHANGED.
