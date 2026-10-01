# Prescribed-motion/MPC timing investigation

## Scope and identity

This is a diagnostic follow-up to the corrected follower-validation campaign.
It does not replace or override the registered **NO-GO**.

- Baseline: `26d35bcad1b5ac6ae693c09d283cc3a918aa650c`
- Candidate: `b67517d16a589ebb397d1ef55441467ee0e62275`
- Formal evidence SHA-256: `2c43d43887d520fb6c1581dafb2727f8f6b64a5d6566dc039bff70b161c05ddf`
- Diagnostic raw evidence SHA-256: `d8653656c956580efb5405cc23babe285992124e2eb541420f3d65ed57570a05`
- Compressed diagnostic SHA-256: `28ba05369f0e733c3dd3ee0690e3b45572c7ffcc7e7f17220d13b9b8940b267c`
- Diagnostic runner SHA-256: `8c1205825f1de4b4455f09732a3395529ccc6a2ecd302cb845f2d3a3692e8743`

The diagnostic used the exact installed sites and worker route from the formal
campaign: one unmeasured warm complete route followed by one measured complete
route. Twenty baseline/candidate pairs ran serially with alternating order and
the registered one-thread environment.

## Result

| Measure | Baseline | Candidate | Apparent reduction |
| --- | ---: | ---: | ---: |
| Complete-route median | 0.032039 s | 0.034132 s | -6.53% |
| Solver median | 0.031226 s | 0.033612 s | -7.64% |
| Model-build median | 0.000470 s | 0.000555 s | n/a |
| Complete-route median absolute deviation | 0.002485 s | 0.003359 s | n/a |

The complete-route median difference is 0.002093 s. It is smaller than the
median absolute deviation of either revision. Individual paired reductions
range from -190.21% to +17.36%, with a paired median of -3.92%. All 40 samples
have the same physical hash and work signature.

A call-count profile found 120,236 baseline calls and 120,252 candidate calls.
The 16 added calls are one-time follower-policy setup operations; Newton,
assembly, solve, reaction-recovery, and physical work counts are unchanged.
The profiles were collected concurrently, so their wall times are excluded
from the timing conclusion; only deterministic call counts are used.

## Finding

The 31-34 ms case cannot reliably enforce a 5% regression limit with the
registered one-route timing method. The diagnostic reproduces the formal
direction, but the 2.09 ms difference is below observed run-to-run spread and
cannot be attributed to additional solver work. No product-code change is
supported by this evidence.

The next qualification should retain this case for physical coverage and use
a preregistered amplified timing observation for the regression limit, such as
multiple independent complete routes per measured worker. That protocol change
requires a new manifest/runner identity and a fresh formal execution authority.

The first diagnostic setup attempt ended before collecting a sample because it
used an invalid line-search label. Its log remains in
`.tmp_follower_validation_gate/logs/mpc-diagnostic`; the corrected run used the
fresh `mpc-diagnostic-run2` directory and completed 20/20 pairs.
