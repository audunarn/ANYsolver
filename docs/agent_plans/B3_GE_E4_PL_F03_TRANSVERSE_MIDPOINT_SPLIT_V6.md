# F03 transverse midpoint-split diagnostic V6

24 September 2026. Level-A development experiment only. This does not
consume the formal F03 execution authority or qualify native B3-GE/E4-PL.
The classical plane-stress energy, four-sample pose, classical beam, P1
weak line, loads and supports are unchanged. Each of the three y intervals
from the previous comparator is split at its geometric midpoint. The
attachment lines at `y=±0.23 m` remain element boundaries. This is a
systematic h refinement, not a penalty or a retuned connection law.

The optional six-interval basis passed the affected **18/18** focused
checks, including independent physical quadrature of its matrices and
two-dimensional shell energy, shared-node continuity, fixed material
sample pose, and line virtual work. Replaying the original three-interval
small case after the source change reproduced six saved physical values
exactly. Two new serial, one-thread guarded runs completed at x degree
24, beam512 and P1 line1024. Exact raw roots are
`B3_GE_E4_PL_F03_HREFINED_Y6_P{8,12}_XP24_B512_M1024_V6/` under
`docs/agent_plans/`; they retain commands, source hashes, stdout/stderr,
parsed results, status and the 8 GiB sampled-child-RSS/300 s limits.
Maximum sampled child RSS was **5.093 GiB** and maximum elapsed time
**116.94 s**. Sampled RSS is not a hard peak or process-tree total.

The manifests bind predecessor commit `f49a90bb` and exact source hashes.
Changed y-basis, reference and runner SHA-256 values are respectively
`3834badb378209f89ca149fe231538e730c55ee362ab023462c44d50c0e19d2e`,
`9f26966eae313fe455c418f71d0cfa242a6a72673352549c45bc3620e946d633`,
and `da66bc40d6dc692b518a6e353750b4b1357af734c76b111fc592c9fe0decba7a`.

Equal transverse coordinate counts permit a direct fixed-cost comparison:

| y partition × degree | y coordinates | Beam energy (J) | Root axial (N) | Sampled RSS (GiB) |
|---|---:|---:|---:|---:|
| 3 × 16 | 49 | `0.000471151` | `-8162.89` | 2.733 |
| 6 × 8 | 49 | `0.000465586` | `-8230.63` | 2.400 |
| 3 × 24 | 73 | `0.000475201` | `-8116.57` | 5.699 |
| 6 × 12 | 73 | `0.000472027` | `-8152.57` | 5.093 |

The six-interval degree8→12 change is **+1.383%** in beam energy and
**-0.948%** in root-force magnitude. The three-interval degree16→24
change at the same coordinate counts is **+0.860%** and **-0.568%**.
This midpoint split does not improve the observed order-to-order physical
stability at fixed coordinate count. Its slightly lower sampled memory
does not overcome that deficiency. Neither sequence is a converged
reference, so the differences between the two partitions are not error
estimates and do not identify which one is closer to the continuum.

**Decision:** do not select the six-interval midpoint split as an
efficiency remedy for the present F03 axial reference. Preserve it as a
verified alternative discretization and contrary evidence. The next
mechanics decision must address the actual regularity/localization and
the native signed multiplier/torque problem, rather than declare a
physical target from a small gap or a single mesh. F03/G0B remain open
and G1 barred.
