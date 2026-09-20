# Follower-validation retention adjudication

Raw evidence SHA-256: `0eafe512774a9cde13c2aaa9e9e4d6a4412d9c47b6e91904088f5a83890a7e62`.

## Registered criteria

| Criterion | Required | Observed | Result |
| --- | ---: | ---: | --- |
| Target follower reduction | 10.00% | 83.13% | PASS |
| Non-target `easy_elastic_shell_control` | no worse than -5.00% | 1.37% | PASS |
| Non-target `large_deflection_shell_holdout` | no worse than -5.00% | -0.78% | PASS |
| Non-target `plastic_s3_reversal_holdout` | no worse than -5.00% | 0.13% | PASS |
| Non-target `prescribed_mpc_beam_holdout` | no worse than -5.00% | 2.70% | PASS |

## Decision

- Evidence completeness: **PASS**
- Mechanics equivalence: **PASS**
- Registered representative performance: **NO-GO** (1.41%)
- Target follower performance: **PASS**
- Non-target regression limit: **PASS**
- Promotion: **NO-GO**
- Retention: **RETAIN_EXPERIMENTAL**

The optimization remains mechanics-preserving and is retained for review, but it does not pass the registered promotion gate. The raw campaign and its NO-GO decision remain unchanged.
