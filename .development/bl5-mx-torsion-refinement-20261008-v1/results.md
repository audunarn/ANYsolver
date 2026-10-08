# Resolved beam-only torsion refinement — development result

The same 1 m, `0.04 × 0.06 m` C3D20 bar used identical area-L2 section-pose
root restraint and work-conjugate 10 N m torque at three systematic mesh levels.
The 2×2×1 body matrix matched the independently assembled saved body to
`7.3e-16` relative entry difference; both section ports matched within
`5.4e-15`. The coarse work reproduced the earlier section-port solve.

| C3D20 elements | Nodes | Applied work | Difference from prismatic Saint-Venant |
|---|---:|---:|---:|
| 2×2×1 | 51 | `0.001474598 J` | `-10.47%` |
| 4×4×2 | 245 | `0.001627825 J` | `-1.17%` |
| 8×8×4 | 1449 | `0.001649352 J` | `+0.14%` |

The native B3 beam-only work was `0.001647014 J`, equal to the stated
Saint-Venant section prediction to roundoff. This nested series strongly
identifies the coarse solid beam as a poor torque comparator. It does not
establish the asymptotic 3D port limit, a coupled-shell accuracy claim, or BL5
qualification. Each solution passed finite state, equilibrium, physical wrench,
root-gap and work checks.

[Receipt](receipt.json) and [raw level results](levels/) bind the source and
parent input, observed CPU0/one thread/JIT-off, process wall `2.91 s`, and
sampled peak process-tree RSS `218.9 MB`. No new CalculiX run or F03 assessment.
