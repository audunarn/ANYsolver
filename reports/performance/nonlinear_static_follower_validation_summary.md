# Follower-load validation overhead gate

## Candidate

- Baseline: `26d35bcad1b5ac6ae693c09d283cc3a918aa650c`
- Corrected candidate: `b67517d16a589ebb397d1ef55441467ee0e62275`
- Candidate wheel SHA-256: `4512f1172f446922272fdb6e34f77175755351f7c91fc9ca2bddacc30623792c`
- Manifest SHA-256: `ae2e0e3aef093203c32975819717f651569c3cacbba661be0a97f5ebf5bca071`
- Runner SHA-256: `5764f1104f23272ca3103df50f1655c0aa6ca6701f930ee324313bd10e752d13`
- Raw evidence SHA-256: `0eafe512774a9cde13c2aaa9e9e4d6a4412d9c47b6e91904088f5a83890a7e62`
- Compressed evidence SHA-256: `a1ee0734a594d2e92a51db876c5039ee6e4ba06ab9fdbd9bb83e2c24b549a27a`

The candidate retains full follower force and tangent evaluation at every
required state. It reuses only component lifecycle validation inside a bounded
solver-owned evaluation, with exact full validation before and after the
evaluation. Unsupported models and load cases use the existing public path.
The trailing validation is exception-safe, records invalidation, and preserves
the original evaluation failure in the public exception chain.

## Verification

- Follower-load module: 21 passed.
- Related lifecycle, diagnostics, and performance contracts: 29 passed.
- Nonlinear static, Armijo, and restart set: 35 passed.
- Amplified evidence, adjudication, and profile harness: 20 passed.
- MPC variance diagnostic harness: 2 passed.
- Installed candidate regressions: 6 passed; the identity check confirmed the
  package was imported from the isolated installed-wheel site.
- The broader repository suite still has the independently reproduced,
  baseline-present generalized-triangle `reference_normal` failure. It is not
  changed by this candidate.

Independent mechanics review found no mechanics, state, restart, reaction, or
tangent defect. Independent code review found one exceptional-path lifecycle
gap. The corrected candidate closes it, and re-review accepted the fix with no
remaining actionable findings.

## Registered result

| Case | Baseline median (s) | Candidate median (s) | Reduction | Physics |
| --- | ---: | ---: | ---: | --- |
| Easy elastic shell | 0.468786 | 0.462381 | 1.37% | PASS |
| Large-deflection shell | 6.124852 | 6.172555 | -0.78% | PASS |
| Plastic S3 reversal | 10.783028 | 10.769225 | 0.13% | PASS |
| Prescribed motion/MPC | 0.032232 | 0.031363 | 2.70% | PASS |
| Nonsymmetric follower shell | 8.828272 | 1.489240 | 83.13% | PASS |

Each MPC worker used the median of 25 independent complete routes after one
warm route. All 350 measured MPC routes had identical physical and work hashes.

Evidence completeness, physical equivalence, the 10% follower target, and the
5% non-target regression limit all pass. The representative nonlinear median
improvement is 1.41%, below the independently registered 10% requirement. The
promotion decision therefore remains **NO-GO**; the implementation disposition
is **RETAIN_EXPERIMENTAL**.

The first coordinator setup attempt ended before its first measured sample
because `psutil` was absent. The dependency was installed and the formal
campaign used fresh install and log directories. The pre-review candidate
`261599a5` also produced a complete NO-GO campaign; its evidence is retained
under filenames containing that revision and is not reused for the corrected
candidate. The corrected candidate's single-route campaign is retained under
filenames containing `b67517d1_single_route`; it is not reused by this
amplified campaign.
