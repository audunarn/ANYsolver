# Fixed-shell coupled Mx beam refinement — development result

The saved C3D20 shell, root support, geometry, 20 five-channel weak-P0 rows,
and 10 N m physical torque were fixed. Only the resolved beam C3D20 mesh
changed. The coarse independent coupled solve reproduced the executed
CalculiX applied work `0.000824615888 J` within `3e-11` relative.

| Resolved beam elements | Coupled resolved work | Native/resolved work ratio |
|---|---:|---:|
| 2×2×1 | `0.000824616 J` | `1.22489` |
| 4×4×2 | `0.000899274 J` | `1.12320` |
| 8×8×4 | `0.000910019 J` | `1.10994` |

The native work is the same saved `0.001010067323 J` at all three levels.
The old coarse solid beam contributes materially to the original response
contrast, but the remaining roughly 11% ratio difference is unresolved.
The sequence changes only the resolved beam, so it does not establish
converged solid-shell response or isolate a connection-law error. All levels
passed the weak constraint, physical interface wrench, equilibrium and work
checks. The next bounded comparison holds the fine beam fixed and varies only
the resolved shell discretization; any resulting trend must still be judged
against native Q4/S3 refinement and a physically matched external reference.

[Receipt](receipt.json) and [raw levels](levels/) bind the saved external
comparison and beam-only refinement. Observed process wall was `4.77 s`,
CPU0/one numerical thread/JIT off, peak sampled process-tree RSS `247.3 MB`.
No external solve, F03 assessment, or multiplier-policy selection ran.
