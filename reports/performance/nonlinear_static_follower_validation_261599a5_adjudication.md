# Follower-validation retention adjudication

Raw evidence SHA-256: `375f0c0b92a5f59f29e28f7d3dcb2066c2511a980749e44ba9fb2efecaaa6f0d`.

## Registered criteria

| Criterion | Required | Observed | Result |
| --- | ---: | ---: | --- |
| Target follower reduction | 10.00% | 82.32% | PASS |
| Non-target `easy_elastic_shell_control` | no worse than -5.00% | 3.08% | PASS |
| Non-target `large_deflection_shell_holdout` | no worse than -5.00% | -9.87% | FAIL |
| Non-target `plastic_s3_reversal_holdout` | no worse than -5.00% | 0.90% | PASS |
| Non-target `prescribed_mpc_beam_holdout` | no worse than -5.00% | 0.34% | PASS |

## Decision

- Evidence completeness: **PASS**
- Mechanics equivalence: **PASS**
- Registered representative performance: **NO-GO** (0.62%)
- Target follower performance: **PASS**
- Non-target regression limit: **FAIL**
- Promotion: **NO-GO**
- Retention: **RETAIN_EXPERIMENTAL**

The optimization remains mechanics-preserving and is retained for review, but it does not pass the registered promotion gate. The raw campaign and its NO-GO decision remain unchanged.
