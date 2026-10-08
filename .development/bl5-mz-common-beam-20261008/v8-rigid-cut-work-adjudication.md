# V8 saved rigid cut-work map

One saved-only reference-linear postprocess imposed the native V5 one-sided
retained spins as rigid virtual cut traces on V7's equilibrated C3D20 nodal
ports. It executed **no solver**, external job or F03 assessment. The child
reported CPU0, one numerical/BLAS thread and JIT disabled; source evaluation
wall was `0.21632 s`. The command tool reported `2.8729274 s` total wall.
Process wall and peak tree memory were not measured for this small postprocess,
so the record makes no claim about those quantities. The interpreter emitted
its known location warning; exit was 0.

Full nodal outward work is `-4.009200810356648e-7 J`. Its six-wrench
contraction differs by `-1.058791184e-22 J`. The native saved endpoint-log
first variation is `+4.009200810375506e-7 J`; the signed sum is
`1.885812978e-18 J`. Shared nodal-spin work is `-7.761998170e-19 J`.
Independent read-only review confirmed the restricted rigid trace and opposite
outward/endpoint-log signs. The saved input hashes match; the reviewer also
checked the seam→jump/material→native chain for these frozen inputs. The V8
source itself does not enforce that entire provenance chain, so comprehensive
stale-input refusal is unproven.

This is an **algebraic dual-map check** under an imposed reference-linear
virtual field. It neither creates a split-solid solution nor measures port
flexibility or section warping. Identical source balance already explains the
matching moment scale. No V5 body-work allocation, BL5 law accuracy,
multiplier selection or F03/G0 acceptance follows. A subsequent response
reference needs independently declared two-sided port kinematics, matched
loads, outer-boundary conditions, and treatment of rigid modes before its
numerical output can be used to decide the connection law.

SHA-256: source `d3eca0f3caf1829a580a9fe49b066b072efe27942a91d8011c0c31ea7b88abb8`;
result `56daba759eff17e388d46b9ec679c7daedc86342adf98b6d8ecc5841b0ccfb0e`;
receipt `d46ae2f7cdd6e3b477d5b582c94c554fc78d90f551c0e1d5ab38d5301e63ebd4`.
