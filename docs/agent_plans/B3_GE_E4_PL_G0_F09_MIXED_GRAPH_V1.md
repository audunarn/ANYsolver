# F09 mixed weak-shear graph: exploratory physical oracle

24 September 2026. This is Level-A development evidence, not the formal F09
assessment or public B2 admission. Parent integration source was `8943220b`.
The private physical-flexibility operator is unchanged. Its source SHA-256 is
`4951a9cada5a779489fe8d031d09e71da00199d76cf31ea2177c389c8f1ed237`;
the new probe SHA-256 is
`065cbf2cfbd95caf2ab3b854e7c84b0ac8045519e4964a2ddfde18348373fbb8`.
The four raw result lines are in `B3_GE_E4_PL_G0_F09_MIXED_GRAPH_V1.jsonl`,
SHA-256 `41e564fd71ccf0aee3e300b0582293650bae3ff6c9def99cd5cce4ac7407c84d`.
Command: `python -B -u scripts/probe_b3_ge_e4_pl_g0_f09_mixed_graph.py`.

The probe assembles one or two collinear unit-length members into a rooted
sparse graph. It uses the candidate's rounded local tangent, including the
weak-shear action, and solves with sparse LU. A separate Castigliano oracle
integrates the physical diagonal-section energy with exact `Fraction`
arithmetic before output conversion. The terminal wrench contains axial,
two shear, torsion and two bending components. Axial/shear loads scale with
their very weak stiffness, while torsion/bending couples remain order one.
The two admitted areas are `2^-12` and `2^-80` m²; all other section values
and the precise terminal wrenches are in source and raw results.
As a separate algebraic check of the oracle, exact Simpson integration of
`[N²/EA + Vy²/GAy + Vz²/GAz + T²/GJ + (My−(L−s)Vz)²/EIy +
(Mz+(L−s)Vy)²/EIz]/2` over both lengths was differentiated by exact
centered `Fraction` differences for all six wrench components in all four
cases. The 24 derivatives round to exactly the six stated tip formulas.

All four cases returned finite solutions. The largest componentwise tip
relative error was `2.23e-16`; largest scaled free-force residual was
`3.41e-16`, support-force discrepancy `3.32e-16`, and support-moment
discrepancy `3.52e-16`. The two-member extreme case gives the oracle and
computed tip `(1.5, 2, -1.75, 0.5, 0.25, -0.5)` in local translation/
rotation coordinates. Energy/work agrees to floating precision. The four
existing private operator/definition/trace/oriented-graph suites passed
**27/27** in the same worktree. An initial package-root import made the
exploratory process unacceptably slow and was stopped; the final probe loads
only the self-contained private operator source. No product source changed.

This extends the earlier shear-only root-clamped result to combined weak
forces and strong couples. It does **not** establish a uniform graph
condition range, arbitrary generalized sections, reversed or rotated
extreme graphs, shell attachments, spectra or a public fast profile. The
loads deliberately scale with the weak stiffness, so fixed-magnitude
loading and small response components still need separate assessment.
F09 remains open; F03/G0B also remain open and G1 is barred.
