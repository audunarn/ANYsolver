# F03 mesh-local trace dual: ambient/image equivalence fails the screen

21 September 2026. **Ten/ten registered exploratory cases completed, with
an adverse equivalence trend. F03/G0B remain open.** Frozen source and
registration commit `86da5763fbeb849cb060f809c2f1010d6b0a408d`;
exclusive evidence root
`C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/f03-local-trace-norm-v1/`.
SHA-256: `manifest.json`
`b7a93390ecb2fb3e45a29f8f4ebc5a0f495d58297d09f42591a42252d5c8e71b`;
`records.jsonl`
`bf69b46e865162882c61ea17f398f30661c4d756baf9e17fc88da32d0c683790`.
The manifest's ten source hashes match frozen files, and its import points
to the isolated integration worktree. This is source-backed diagnostic
evidence, not an installed-artifact or production-mortar qualification.

The three physical trace channels scale yaw by `.46 m`. Each actual overlay
interval owns independent left/right trace values. A sparse local Riesz
matrix `R` integrates their L2 and slope norms and adds native-cell yaw
jumps. The two candidate test spaces integrate through local `F` rows;
one-sided physical trace evaluation supplies `E`. The independent old
assemblies agree with `C=FE` and `G=EᵀRE` at `1.03e-15` and `8.22e-15`
maximum scaled relative discrepancy. The maximum affine midpoint error
was `7.77e-15`, and every case counted `Nb−1` native yaw jumps. `R` had
at most 2,352 endpoint DOFs, 4,718 nonzeros, and 7,072 LU-factor
nonzeros. A sparse factorization computes the ambient test dual
`A=F R⁻¹ Fᵀ`; no dense model-wide inverse is used for that dual.

For verification only, a bounded dense oracle computes the physical-image
dual `B=C G⁺ Cᵀ`. The ambient space admits translation discontinuities and
non-native yaw jumps that the shell/native beam cannot realize. Thus
`0≼B≼A`; physical equivalence would need a uniform upper bound on `A/B`.
The table gives the largest generalized `A/B` eigenvalue and the smallest
full *signed* KKT singular value (ambient-dual normalized):

| Panel / test | Joint 4/4 | Joint 8/8 | Joint 16/16 | Crossed 8/1 | Crossed 8/64 |
|---|---:|---:|---:|---:|---:|
| Q4 K4, max `A/B` | 124.31 | 628.37 | 2,181.87 | 265.50 | 617.12 |
| Q4 local dual, max `A/B` | 130.31 | 640.29 | 2,186.44 | 247.07 | 637.63 |
| S3 K4, max `A/B` | 135.64 | 656.58 | 2,559.48 | 336.94 | 643.92 |
| S3 local dual, max `A/B` | 152.87 | 673.63 | 2,586.29 | 366.74 | 661.83 |
| Q4 K4, signed floor | .05216 | .01084 | .00316 | .02516 | .00977 |
| S3 K4, signed floor | .04380 | .00996 | .00258 | .01915 | .00973 |

All eight joint-doubling `A/B` growth factors exceed the registered 2×
adverse screen, ranging from 3.42× to 5.06×. The fixed eight-cell beam
reach changes much less between 8/8 and 8/64. This shows that the
ambient broken-trace dual is a poor, mesh-dependent proxy for the
physically reachable trace-image dual on this finite inventory. Its
declining signed floor must not be read as a proved physical instability.
The local-dual candidate does not cure the trend. The signed Schur blocks
had no negative eigenvalues in these cases, so this observation does not
uniquely diagnose negative-block cancellation either.

Every case completed with exit code zero, exact case identity and empty
stderr. All three graph cutoffs `1e-12`, `1e-10`, `1e-8` gave the same
image ranks and generalized ratios. Maximum dropped-kernel action was
`7.48e-14`, minimum ambient dual eigenvalue ratio `.00315`, and the
minimum eigenvalue of `A−B` divided by `λmax(A)` was `−1.82e-12`, within
the registered `1e-9` roundoff allowance. Maximum sampled child RSS was
300,478,464 bytes, maximum case wall time 39.55 s, and summed case time
86.70 s, within registered limits. Sampled RSS is not a certified peak.

Independent pre-execution mechanics review checked the derivation,
source and case inventory. It required aligned dual-rank thresholds,
three-cutoff sensitivity, and provenance checks before the exclusive
root was created; all were corrected before source freeze. Independent
post-run review verified source hashes, raw responses, statuses, numerical
criteria, resources, and the adverse trend without a raw-evidence finding.

**Decision:** retain the local Riesz assembly as a diagnostic of the
ambient broken space, but do not use its dual as the physical multiplier
norm or select either line test space from these floors. A next norm must
control the *reachable* trace image with a mesh-local stable lifting or
an independently justified equivalent construction. An independently
converged, mechanically matched loaded reference and six-channel
eccentric torque/shear tests remain separate mandatory F03 foundations.
No G1 production implementation or acceptance follows from this run.
