# Follower-load validation overhead gate

## Candidate

- Baseline: `26d35bcad1b5ac6ae693c09d283cc3a918aa650c`
- Corrected candidate: `b67517d16a589ebb397d1ef55441467ee0e62275`
- Candidate wheel SHA-256: `4512f1172f446922272fdb6e34f77175755351f7c91fc9ca2bddacc30623792c`
- Raw evidence SHA-256: `2c43d43887d520fb6c1581dafb2727f8f6b64a5d6566dc039bff70b161c05ddf`
- Compressed evidence SHA-256: `14ade518b188b81d02bc8b0681e6c4e918a51b8a1235c181f5e4fdefc43859a7`

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
- Evidence and profile harness: 18 passed.
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
| Easy elastic shell | 0.428253 | 0.414753 | 3.15% | PASS |
| Large-deflection shell | 5.489191 | 5.499492 | -0.19% | PASS |
| Plastic S3 reversal | 10.509118 | 10.679862 | -1.62% | PASS |
| Prescribed motion/MPC | 0.031016 | 0.033122 | -6.79% | PASS |
| Nonsymmetric follower shell | 8.187159 | 1.440301 | 82.41% | PASS |

Evidence completeness and physical equivalence pass. The follower target
passes its 10% threshold, but the prescribed-motion/MPC holdout exceeds the 5%
non-target regression limit. The representative nonlinear median is -0.91%,
below the required 10% improvement. The registered promotion decision is
**NO-GO**; the implementation disposition is **RETAIN_EXPERIMENTAL**.

The first coordinator setup attempt ended before its first measured sample
because `psutil` was absent. The dependency was installed and the formal
campaign used fresh install and log directories. The pre-review candidate
`261599a5` also produced a complete NO-GO campaign; its evidence is retained
under filenames containing that revision and is not reused for the corrected
candidate.
