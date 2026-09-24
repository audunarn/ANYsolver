# F03 double-segmented separate-order diagnosis V4

24 September 2026. Level-A mechanics development diagnostic, not a
formal F03 assessment or native B3-GE/E4-PL qualification. The classical
plane-stress shell, separate beam, fixed four-sample pose, axial loading,
root support and exact P1 weak line remain unchanged. This revision widens
only the supported x spectral-element degree from 24 to 32, retaining the
global-sine x cap. The degree-32 Lobatto Vandermonde condition is about
`10.97`; the affected 13 focused mechanics checks pass.

Two serial, resource-bounded runs varied one approximation axis at a time,
holding 512 beam elements and 1024 P1 line intervals:

| x degree | y degree | Tip axial (m) | Shell energy (J) | Beam energy (J) | Root axial (N) |
|---:|---:|---:|---:|---:|---:|
| 24 | 12 | `-3.337760691e-7` | `0.004940093` | `0.000466488` | `-8219.46` |
| 32 | 12 | `-3.337347921e-7` | `0.004941361` | `0.000466412` | `-8209.98` |
| 24 | 16 | `-3.334527470e-7` | `0.004942491` | `0.000471151` | `-8162.89` |

The x24→32 change at y12 is `-0.0163%` in beam energy and `-0.115%`
in root-force magnitude. The y12→16 change at x24 is **+0.9996%** in
beam energy and **-0.688%** in root-force magnitude. The latter is
material despite a continuous-gap L2 of only `3.61e-12 m` in the y16
case. Earlier y-order stability at coarser P1 resolution therefore does
not carry over to this finer line space. It would be incorrect to treat
the earlier y-degree-12 result as a settled physical reference.

The two raw roots are
`B3_GE_E4_PL_F03_DOUBLE_SEGMENTED_XP32_YP12_B512_M1024_V4/` and
`B3_GE_E4_PL_F03_DOUBLE_SEGMENTED_XP24_YP16_B512_M1024_V4/` under
`docs/agent_plans/`. They contain commands, exact source hashes,
stdout/stderr, parsed responses, status, one-thread setting and 8 GiB/
300 s limits. Both completed without a reported failure. Maximum sampled
child RSS was 2.733 GiB and maximum wall time 78.25 s; sampled RSS is not
a hard peak or process-tree total. The manifests bind predecessor commit
`5e41f534` and script SHA-256 values for the changed x basis, reference
and runner of respectively
`619a4235688cb90c7dc2914a3deb36dbcc6c33fd9986b9005493c9c19df5d8d7`,
`bf836ae2086242a4f4effa2144551f4cc56c30859acfabdc2d26f4df72a440da`,
and `77fbc1eacde5e4f970b7884d29465ce759ae3b9b3a95c1efafb75fa1a1cbc6e9`.

**Decision:** retain the separate-order evidence and refine y before
proposing a physical target. Do not select a native pose, line space or
signed-stability conclusion from these classical cases. F03/G0B remain
open and G1 barred. Earlier failed and adverse evidence remains valid.
