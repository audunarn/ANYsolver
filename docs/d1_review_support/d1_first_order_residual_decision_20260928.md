# D1 first-order residual prototype — bounded promotion decision

**Question.** Can the existing unbatched first-order Q4/S3 derivative prototype
replace batched Jet2 for residual-only evaluations on the D1 route without
changing adaptive branches or contact work, and does it offer a local cost
reason to pursue complete-route promotion? Competing outcomes were a useful
faster residual route, a branch/force inconsistency, or no measured benefit.

An internal development-only switch selected
`q4_s3_overlap_first_derivatives` when the contact manager requested no
tangent, retaining Jet2 for the tangent and any tiny-wedge fallback. The
[experimental patch record](d1_first_order_residual_experiment_20260928.json)
records those temporary changes against committed source `9740c93d`; its Git
blob is `effcb6fab60bb8690b390dbdd448aeed2688ab89`. The switch was removed
after the comparison. It is not a public or default solver option.

Two source-only paired evaluations used the same manager and pose for
first-order residual and Jet2 residual/tangent work. The [uniform active
4×8 record](d1_first_order_4x8_pair_20260928.json) had 40 overlapping
Q4/S3 pairs, 45 active pressure modes, −10 µm minimum gap and 0.09 N
integrated contact force. The [saved 16×8 pose record](d1_first_order_16x8_saved_pose_20260928.json)
binds the prior coupled-field SHA-256
`8293e528837cc2a8a25444aa079944c9f8371f5a5b50280bb6dc91816d19b852`.
It had 148 geometric overlaps, 52 differentiated active pairs and 38
active pressure modes under the manager's separate penalty evaluation. Its
penalty force was nearly zero; it checks saved deformed geometry and local
derivatives, not the monolithic active force at that pose.

| Observation | Uniform 4×8 | Saved 16×8 |
|---|---:|---:|
| Differentiated pair comparisons | 40 | 52 |
| Branch-signature/triangle-count differences | 0/0 | 0/0 |
| Maximum support-gradient difference | 1.73×10⁻¹⁷ | 2.08×10⁻¹⁷ |
| Maximum weighted-gap-gradient difference | 1.73×10⁻¹⁸ | 1.30×10⁻¹⁸ |
| Maximum assembled residual-force difference, N | 1.73×10⁻¹⁸ | 4.93×10⁻³² |
| First-order pair work, s | 1.734 | 2.253 |
| Batched Jet2 pair work, s | 1.016 | 1.309 |

This single ordered pair of timings at each pose is **not** a balanced
complete-route performance estimate. It provides no measured speed benefit:
the first-order kernel took about 1.7 times the batched Jet2 pair time in
both observations. No complete nonlinear run or general adaptive-branch
consistency corpus was executed with the temporary route.

**Decision.** Keep batched Jet2 for production residual and tangent work.
Preserve the first-order scalar prototype in its existing derivative module,
without adding a solver setting or promoting it on these results. Further
first-order optimization would need a measured whole-route bottleneck and a
new bounded hypothesis; it is not on the immediate D1 critical path. The
next work should close mechanics/acceptance gaps rather than tune this
kernel.
