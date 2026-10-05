# F03 checkerboard shell-y refinement diagnostic result

22 September 2026. The four new cases in `B3_GE_E4_PL_G0_F03_CST_CB_Y_REFINEMENT_REGISTRATION.md` completed under exact clean execution HEAD `ab819e7bbef9651cdb4eb5c1758452299ab3e215`; executable source bytes remain identical to frozen `f7d890e7c355c9016dde7c0db10ee71c3200dec2`. The earlier same-source Ny64 Q4/CST-CB roots were reused only as terminal diagnostic points. This is **not a registered 96-case physical-reference comparison or G0B acceptance**.

| Ny / route | Root suffix | Manifest SHA-256 | Elapsed | Peak RSS |
|---|---|---|---:|---:|
| 16 Q4 | `f03-classical-cst-cb-y16-q4-v1` | `45a325bb588082a314e8d8d21c04a1deb16be080dca5158c5c0be34f48edca3a` | 7.143 s | 154,517,504 B |
| 16 CST-CB | `f03-classical-cst-cb-y16-v1` | `ad5b5ce65a7d00e6a7d2512c1acc61167c7adf87de2cdde80c0d6105a0c225ff` | 7.442 s | 149,614,592 B |
| 32 Q4 | `f03-classical-cst-cb-y32-q4-v1` | `0402d1452613801896e45b201a4aeddff00666a3ed22d3d4f9b78c127ac18e43` | 8.240 s | 227,713,024 B |
| 32 CST-CB | `f03-classical-cst-cb-y32-v1` | `f9522121ba077c4fe36b6cbd5bfbd5b9ef6544fe0ac942f4df9f49fcbe2e16a6` | 7.940 s | 200,212,480 B |

All roots are under `C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/`; the reused Ny64 manifest hashes are in `B3_GE_E4_PL_G0_F03_CST_CHECKERBOARD_UPPER_RESULTS.md`. Independent read-only audit confirmed: source-diff empty across the eight executable files, manifest/child/post SHA-256 parity with Ny64, clean source, the same dependency module paths and versions, single-thread pools, ten ordered phases, no malformed records or stderr, exit 0, and each case below 8 GiB/900 s. KKT dimensions were 11,938 (Ny16), 20,098 (Ny32) and 36,418 (Ny64). New cases have scaled free residual ≤`2.66e−14`, weak ≤`2.95e−15`, global balance ≤`2.28e−12`, and finite ordered exact-rational field bounds. The observed `G2` range for the new cases is about `0.00924–0.00962`; these numbers are diagnostics against a still-unregistered physical contract.

The independently computed unchanged signed/floored Q4↔CST-CB **23-channel** comparison has 11 channels above 1% at Ny16, two at Ny32, and two at Ny64. At Ny16 the adverse channels are left-edge `Fy` `4.5101%`, beam energy `2.1493%`, station `.25` vertical displacement `2.0236%`, root `Mz` `1.6771%`, station `.5` vertical `1.4641%`, station `.75` yaw `1.4344%`, shell energy `1.4146%`, left-edge `Mz` `1.2629%`, tip yaw `1.1315%`, station `.75` vertical `1.1142%`, and tip vertical `1.0821%`. At Ny32, left-edge `Fy` `2.6079%` and beam energy `1.2068%` are adverse, while root `Mz` is `0.7151%`. At Ny64, left-edge `Fy` `1.6675%` and root `Mz` `2.0778%` remain adverse.

| Difference, CST-CB minus Q4 | Ny16 | Ny32 | Ny64 |
|---|---:|---:|---:|
| Left shell-edge `Fy`, absolute | 4,499.640755 N | 2,171.761559 N | 1,143.117528 N |
| Beam-root `Mz`, signed | +387.593168 N·m | −168.394760 N·m | −499.758179 N·m |
| Beam-root `Mz`, absolute | 387.593168 N·m | 168.394760 N·m | 499.758179 N·m |

The left-edge force difference contracts by factors `0.482652` and `0.526355`. The root-moment difference reverses sign and its absolute value **grows by 2.967778×** between Ny32 and Ny64. The registration's explicit *either stalls/grows* terminal rule is therefore triggered. Do not extend Ny merely by extrapolating the favorable left-force trend, change the 1% threshold after these outcomes, or advance the 96-case inventory. Return to connection/trace idealization and reaction partitioning. The fixed-diagonal old-CST failures and all failed/dirty prior roots retain their original identity; neither this diagnostic nor its successful numerical balances resolves F03/G0B.
