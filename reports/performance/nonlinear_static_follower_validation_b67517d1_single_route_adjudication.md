# Follower-validation retention adjudication

Raw evidence SHA-256: `2c43d43887d520fb6c1581dafb2727f8f6b64a5d6566dc039bff70b161c05ddf`.

## Registered criteria

| Criterion | Required | Observed | Result |
| --- | ---: | ---: | --- |
| Target follower reduction | 10.00% | 82.41% | PASS |
| Non-target `easy_elastic_shell_control` | no worse than -5.00% | 3.15% | PASS |
| Non-target `large_deflection_shell_holdout` | no worse than -5.00% | -0.19% | PASS |
| Non-target `plastic_s3_reversal_holdout` | no worse than -5.00% | -1.62% | PASS |
| Non-target `prescribed_mpc_beam_holdout` | no worse than -5.00% | -6.79% | FAIL |

## Decision

- Evidence completeness: **PASS**
- Mechanics equivalence: **PASS**
- Registered representative performance: **NO-GO** (-0.91%)
- Target follower performance: **PASS**
- Non-target regression limit: **FAIL**
- Promotion: **NO-GO**
- Retention: **RETAIN_EXPERIMENTAL**

The optimization remains mechanics-preserving and is retained for review, but it does not pass the registered promotion gate. The raw campaign and its NO-GO decision remain unchanged.
