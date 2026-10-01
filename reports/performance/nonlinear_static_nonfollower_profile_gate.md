# Non-follower shared-hotspot profile gate

The preregistered diagnostic gate completed all four installed-wheel profiles
for candidate `b67517d1`. The bound manifest, campaign runner, case builder,
profile runner, build provenance, installed module, revision, and wheel hashes
matched. Every case completed its physical target. Profile wall time is used
only for attribution and is not formal timing evidence.

| Case | Profiled wall (s) | Calls | Result |
| --- | ---: | ---: | --- |
| Easy elastic shell | 0.998954 | 2,227,951 | completed |
| Large-deflection shell | 10.991640 | 20,700,591 | completed |
| Plastic S3 reversal | 15.781043 | 30,228,543 | completed |
| Prescribed motion/MPC | 0.062205 | 120,252 | completed |

The qualified shell guarded-operation boundary satisfies the registered
shared-path rule. Q4 boundary validation accounts for 24.83% cumulative wall
time in the easy shell and 15.26% in the large-deflection shell. S3 model-bound
state validation accounts for 9.97% in the plastic reversal case. The beam-only
MPC case does not use this path.

The selected implementation will reuse the existing exact Q4 and S3
trusted-operation scopes around one nonlinear local-response assembly. Those
scopes already perform complete per-element validation at entry and exit,
check monotonic authority generations during evaluation, and invalidate
derived caches after a rejected boundary. The integration must preserve the
original evaluation exception when trailing validation also fails and expose a
forced-full-validation oracle path.

This is an eligible implementation candidate, not a performance pass. It must
first pass the registered three-pair screen. Formal promotion still requires
the unchanged seven-pair representative gate with a 10% median improvement,
no case worse than 5%, and complete physical equivalence.
