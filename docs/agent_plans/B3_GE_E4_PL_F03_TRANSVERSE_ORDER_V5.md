# F03 double-segmented transverse-order extension V5

24 September 2026. This is Level-A development evidence, not a formal
F03 assessment or native B3-GE/E4-PL qualification. The source revision
widens only the exploratory three-interval y-basis degree from 16 to 24,
retaining the global-Legendre limit. The degree-24 Legendre Vandermonde
condition is about `9.36`; the 13 affected mechanics tests pass.

Two guarded, one-thread runs held x degree 24, 512 beam elements, 1024 P1
line intervals, physical geometry, loading and constitutive parameters
fixed. Their raw roots are
`B3_GE_E4_PL_F03_DOUBLE_SEGMENTED_XP24_YP{20,24}_B512_M1024_V5/`
under `docs/agent_plans/`. Both completed with no reported failure under
the 8 GiB sampled-child-RSS/300 s limits. Maximum sampled child RSS was
**5.699 GiB** and maximum elapsed time **108.20 s**. Sampled RSS is not
a hard memory peak or process-tree total. The manifests bind predecessor
commit `bb4303e9`, exact commands and source hashes; the changed y basis,
reference and runner SHA-256 values are respectively
`a748b88c3a271d91b2ea74174a3292c08730c876d469429e6f5bc217c32c6754`,
`65c06e513becc9f7dfb915047fb51c2cada41cd582c5d296572d2b6e2b764735`,
and `fa2545ec5a1098aeee9589043ac3d4872e5a5f0b67ca88d95c69d84d79985002`.

| y degree | Beam tip axial (m) | Shell energy (J) | Beam energy (J) | Root axial (N) |
|---:|---:|---:|---:|---:|
| 12 | `-3.337760691e-7` | `0.004940093` | `0.000466488` | `-8219.46` |
| 16 | `-3.334527470e-7` | `0.004942491` | `0.000471151` | `-8162.89` |
| 20 | `-3.332819613e-7` | `0.004943628` | `0.000473698` | `-8133.35` |
| 24 | `-3.331833561e-7` | `0.004944215` | `0.000475201` | `-8116.57` |

The successive beam-energy changes are `+1.000%`, `+0.540%`, and
`+0.317%`; root-force magnitude changes are `-0.688%`, `-0.362%`, and
`-0.206%`. Thus y-order effects shrink but remain material at the fine
line resolution. The previously tiny y12→16 change on a coarser line
space was not a general convergence result. The physical gap decreases
slightly to `3.00e-12 m` at degree 24, but a small gap cannot establish
beam/shell energy or reaction accuracy.

**Decision:** do not adopt a physical reference target or native line law.
Another global polynomial-order increase would press against the 8 GiB
exploratory limit. The next development comparison should use a bounded
transverse partition that resolves the attachment-line neighbourhood
without changing the plane-stress energy or sample/line work, with
independent matrix and work checks before loaded use. Signed stability,
physical torque/shear, matched Q4/CST convergence and mesh-ratio gates
remain open. F03/G0B remain open and G1 barred.
