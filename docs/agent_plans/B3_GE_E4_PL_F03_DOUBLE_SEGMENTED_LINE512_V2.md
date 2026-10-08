# F03 double-segmented axial line-resolution extension V2

24 September 2026. Level-A development diagnostic only; no formal F03
execution authority was consumed. The classical shell, beam, load, support,
four-sample pose and P1 exact weak-line equations are unchanged from
`B3_GE_E4_PL_F03_DOUBLE_SEGMENTED_AXIAL_V1.md`. This source revision widens
only the exploratory line-interval admission from 256 to 512. The former
256-interval result was replayed after that bound change with exact equality
of six selected physical fields. All 13 affected focused tests passed.

The resource-bounded case fixes x degree 24 (119 free coordinates), y degree
12 (37 coordinates), 512 beam elements and 512 P1 line intervals. Raw
manifest, command, source hashes, stdout/stderr, parsed result and status
are in
`B3_GE_E4_PL_F03_DOUBLE_SEGMENTED_XP24_YP12_B512_M512_V2/`.
The child exited successfully with one numerical thread, a sampled peak RSS
of 1,583,374,336 bytes and 41.34 s elapsed, within the 8 GiB/300 s limits.
Sampled RSS is not a hard memory peak or process-tree total. The manifest
binds predecessor commit `e9f7d9ce` and exact script hashes; the changed
reference/runner source hashes are respectively
`6e9cad78672c53ecaf73e857cd0ac1177c768eed6ff481c66c74ab7a79b6144a`
and `e8b3cf12d77a213fc3206736dbfb3bc0dd1318e40dd643bf99d4227df931c48b`.

At fixed shell and beam spaces:

| P1 intervals | Tip axial (m) | Beam energy (J) | Root axial (N) | Gap L2 (m) |
|---:|---:|---:|---:|---:|
| 128 | `-3.328657677e-7` | `0.000481813462` | `-8079.42` | `2.85877e-10` |
| 256 | `-3.335459569e-7` | `0.000472403463` | `-8176.54` | `7.08400e-11` |
| 512 | `-3.337246847e-7` | `0.000468153489` | `-8210.01` | `1.46347e-11` |

For 256→512, beam energy changes **-0.900%** and root-force magnitude
**+0.409%**; tip magnitude changes **+0.0536%**. Weak rows, work and
algebraic residuals remain small, but those checks do not establish
continuum convergence. The trend is improving, yet a line-space stability
criterion and a physically converged multi-observable target remain open.
Do not extrapolate the remaining error or use the smallest gap as a proxy
for accepted response. F03/G0B remain open and G1 remains barred.
