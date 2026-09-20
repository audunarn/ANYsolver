# Representative nonlinear evidence

- Campaign started: `2026-09-20T11:50:03Z`
- Campaign completed: `2026-09-20T12:38:29Z`
- Baseline: `3499a04fa10c8d2bd5d6b8e401229ac787cb117e`
- Candidate: `0a56c2c118ffbdea65f749df1a533d99350f26fe`
- Manifest SHA-256: `09c0139065bc35d5f7cd49be6f0b861394f031c34de2b662f7ccdf0940a6b822`
- Runner SHA-256: `d076789215052b61ad1502d5eb87dd9be04f7be8de72e173ddcee0a2d1aece29`

## Installed-wheel performance

| Case | Baseline median (s) | Candidate median (s) | Reduction | Physics |
| --- | ---: | ---: | ---: | --- |
| easy_elastic_shell_control | 0.351579 | 0.342140 | 2.68% | PASS |
| large_deflection_shell_holdout | 5.344808 | 4.775538 | 10.65% | PASS |
| plastic_s3_reversal_holdout | 10.900443 | 8.695636 | 20.23% | PASS |
| prescribed_mpc_beam_holdout | 0.032404 | 0.027793 | 14.23% | PASS |
| nonsymmetric_follower_shell_holdout | 6.330069 | 6.390719 | -0.96% | FAIL |

## Candidate globalization comparison

| Case | Residual-decrease median (s) | Armijo median (s) | Failed-work change | Physics |
| --- | ---: | ---: | ---: | --- |
| large_deflection_shell_holdout | resource limit | resource limit | 0.00% | FAIL |
| plastic_s3_reversal_holdout | 10.346621 | 10.491107 | 0.00% | PASS |
| nonsymmetric_follower_shell_holdout | 11.946103 | 11.864198 | 0.00% | PASS |

## Decision

- Performance promotion: **NO-GO**
- Armijo promotion: **NO-GO**
- Completeness: **FAIL**

Historical evidence remains unchanged. This campaign does not replace the earlier registered 4.35% small-shell NO-GO.
