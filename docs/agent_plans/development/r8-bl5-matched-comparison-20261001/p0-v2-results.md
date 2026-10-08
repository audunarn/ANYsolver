# Controlled external weak enforcement — 1 October 2026

Disposition: retain the declared BL5 five-channel law and P0 candidate for the
required matched growing-space convergence assessment. Independent complete
[review](p0-v2-raw/independent-review.md) found no consequential mechanics,
integration or recovery defect. This is development evidence, not multiplier
selection, converged 1% accuracy, F03 acceptance or a replacement for CalculiX.

The unchanged external 16×4 Q4/32-interval Timoshenko model replaces only its
160 strong constraints with 40 integrated P0 work rows over eight 0.125 m
supports. Raw nodes, elements, materials, frames, roots, loads and all other
assembly commands match exactly. Reference and native retained half-cell traces
remain different operators. All 14 physical recovery checks pass; maximum
4.5108084e-12. Actual-update derivative checks separately reach 3.28733e-10
against 1e-6. Complete primary states and element covectors precede predicates.

| Mz=10 Nm applied work | J |
|---|---:|
| External strong | 1.56929208707257e-5 |
| External P0 | 1.774153836642759e-5 |
| Native P0 | 1.769339530874084e-5 |

Changing only external enforcement increases its work by 13.054405%; the native
result differs from external P0 by -0.271358%. Common nodal P1/Q1 beam and shell
L2 differences are 0.497691% and 0.907274%. These include all six nodal components
with the existing 1 m scale; they do not identify retained-cell rotations with
nodal fields. Smooth regional Mz is 1.47173005 Nm externally versus 1.48354001 Nm
natively. Integrated quantities and endpoint measures remain separately retained.

This controlled sensitivity accounts for most of the earlier +12.747623% strong
reference discrepancy. It does not establish the continuous limit or allocate
the remaining difference uniquely to shell, beam or trace operators. A coarse
same-space match cannot select a production multiplier policy.

V2 completed in 0.305754 s with sampled peak 29,880,320 bytes, single-CPU affinity
and sampled maximum eight OS threads. Only three thread snapshots were retained.
Thread-start module classification is not proof of executed work; dynamic DLL
resolution remains possible. The thread API returned None. Neither an effective
library setting nor lifetime thread-count/resource qualification is claimed.
The earlier stricter-total-thread V1 stop remains unchanged failed execution
evidence. This ordinary diagnostic does not consume formal F03 authority.

[Manifest](p0-v2-manifest.json) preserves 24 raw, supervisor, binary-metadata,
review and provenance files. Original manifests, results and stopped runs are
unchanged. The original inline read-only comparison is retained; a subsequently
saved postprocessor reproduces every field component exactly without importing
product code or solving again.

Next discriminator: hold the declared geometry, properties, supports, loads,
arms and five-channel work law fixed while both meshes and P0 spaces grow over
16×4/32×8/64×16 shells and 32/64/128 beam half-cells or external intervals.
Include Fy=100 N, Mx=10 Nm and Mz=10 Nm. Reuse completed external 16/Mz only
after exact ID-remapped inventory checks. Compare physical work, common fields
and integrated transfer across the same three levels. Consistent convergence
supports progressing to the remaining envelope; persistent disagreement or
nonconvergence identifies a specific outstanding operator or reference issue.
No automatic fourth grid, law tuning or new acceptance threshold follows.
