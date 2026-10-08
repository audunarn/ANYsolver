# Matched Mx beam and interface resolution — development diagnosis

The prior 16×8×4 shell and C3D20 beam with 80 five-channel physical P0 rows
gave `0.0010092788470 J` applied work. One bounded fixed-shell run refined the
beam to 32×8×4 and grew the interface to 160 rows at the corresponding beam
segments. It passed the unchanged KKT, physical work and wrench guards and
gave `0.0010029187834 J` (`−0.63016%` combined).

To separate the two changes, a second bounded run held that refined beam,
shell, section-dual 10 N·m torque, root and material data fixed. It constructed
80 coarse rows by **summing adjacent pairs of already integrated 160 physical
rows**, avoiding a quadrature rule that crosses a beam element boundary.
The 80-row result passed the same controls and gave `0.0010104242171 J`.

| Contrast | Work change |
|---|---:|
| Beam 16→32 axial cells with 80 rows | `+0.11348%` |
| Same refined beam, 80→160 rows | `−0.74280%` |
| Beam and rows refined together from the saved base | `−0.63016%` |

These are finite-grid response contrasts, not additive error estimates or
multiplier-space acceptance. The 160-row space lowers compliance here; that
can represent improved enforcement, locking, or a changed approximation to
the declared physical bond. Neither a small weak gap nor lower work decides
which interpretation is correct. The next bounded mechanics discriminator is
the **same two solved models' supported local interface traction/couple work,
continuous gaps and possible unresolved/overconstrained modes**, interpreted
with the actual trace norm and physical shell shear/drilling behavior. Only a
mechanically justified law advances to the complete registered ratios and
growing-space mixed-system assessment.

[Combined result and receipt](bl5-mx-beam-interface-20261008-v1/result.json),
[aggregated result and receipt](bl5-mx-interface-aggregation-20261008-v1/result.json)
retain exact inputs, source/output hashes, effective CPU0/one-thread/JIT-off
state, bounded process wall, sampled memory, and full stdout/stderr. No
CalculiX run, formal F03 authority, tolerance change or acceptance claim is
associated with these contrasts.
