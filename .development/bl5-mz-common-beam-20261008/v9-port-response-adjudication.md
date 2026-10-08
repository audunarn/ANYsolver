# V9 incremental two-sided body-port diagnostic

The prepared check completed on attempt 3 in 2.2368589 s process wall,
sampled peak process-tree RSS 162,545,664 B. Effective parent affinity was
CPU0; the child requested one numerical thread and JIT disabled. The child
reported no qualification or connection-law decision. The [result](case-v9-port-response-attempt-3/result.json),
[receipt](receipt-v9-port-response-attempt-3.json), [source](../../scripts/r8_bl5_two_sided_port_response_dev.py),
and [contract](v9-port-response-contract.md) are the development evidence.

Attempts 1 and 2 failed before a useful result. Attempt 1 could not resolve
the repository `scripts` namespace under isolated Python. Attempt 2 rejected
the native retained mixed tangent because the diagnostic incorrectly assumed
a positive diagonal. Both stderr streams, receipts and registrations remain
preserved. Attempt 3 used an absolute-row congruence scale without changing
the indefinite tangent. The three children used 6.1689559 s cumulatively;
the final registration reports 83.8310441 s remaining including its 60 s
reserve. Its one final attempt has been consumed; no remainder is transferred.

| Incremental action at x=0.5 m | Resolved two-sided work | Native two-sided work | Native / resolved |
|---|---:|---:|---:|
| V7 balanced cut resultant, including Fy, Mx, Mz | 3.26739102787352e-5 J | 4.07707809202245e-5 J | 1.24781095 |
| Pure unit Mz | 1.48809523822698e-5 J | 9.92063492063492e-6 J | 0.66666667 |

For pure Mz, each resolved half rotates 7.44047619e-6 rad, matching
`L/(E Iz)` for L=0.5 m and Iz=3.2e-7 m4. Each loaded native retained
half-cell spin is 4.96031746e-6 rad. These are **different generalized
coordinates**: the native half-cell orientation is independent of the cut
nodal frame, while the resolved port is an L2-projected cut-face rotation.
The exact 2/3 ratio is a selected-port response difference, not proof of a
native body-stiffness error.

The 1.248 V7-resultant ratio is likewise a response to only its six-component
cut resultant. It omits V7's zero-resultant nodal warping action, does not
apply V5's P0/tip loads, and uses new remote section-pose restraints. It
cannot allocate V5's 7.24284444 loaded-body work ratio or choose a BL5
connection or multiplier space. Both bodies' small KKT residuals, zero remote
pose gaps and work/energy checks support the stated bounded calculation.

Read-only review found no concrete assembly, dual-map or slot defect. It
identified the physical port mismatch above and a provenance limitation:
the isolated Python process adds the worktree root for `scripts`, but imports
`anysolver` through the installed editable path to `C:/Github/ANYsolver/src`.
The four directly relevant operator/source files were found byte-identical
across that main path and this worktree, but transitive imports were not
exhaustively bound. V9 remains a provisional development diagnostic, not
installed-artifact or F03 evidence.

**Next decision:** compare the native cut nodal-frame rotation and retained
half-cell rotation under the *same* bounded incremental loading, with source
module origins bound to this worktree. If the physical nodal section port
agrees with the solid but the retained port differs, investigate the discrete
trace/work mapping rather than native body stiffness. If it also differs,
investigate body idealization. Separately quantify V7's zero-resultant cut
warping action before using any six-port result to interpret V5. Do not run
another classical axial refinement or formal F03 based on V9 alone.
