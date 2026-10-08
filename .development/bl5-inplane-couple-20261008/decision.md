# BL5 in-plane couple development screen — 8 October 2026

Decision sought: Does the five-row, drill-free BL5 line transfer a beam-tip
moment about the shell normal through a finite supported panel, or does this
fixture expose an unsupported mechanism or numerical failure?

The single registered source probe at `333b1e7b` completed. A +1 N m beam-tip
Mz generated a -1.000000000000000 N m shell-side interface moment and
-0.999999999999922 N m support moment about the same origin. Resultant
interface and support forces were approximately zero. The free-equilibrium
ratio was 4.66e-14; the maximum constraint gap was 7.03e-24. The matrix was
134 x 134 with 4,692 nonzeros and 20 multiplier rows. Process wall time was
3.8291954 s and sampled peak RSS 177,664,000 bytes. The child verified CPU
affinity [0], one numerical thread in loaded pools, and disabled JIT. The
receipt's `effective_affinity` field describes the supervisor, not the child;
the child's effective affinity is in `result.json`.

The preceding Python 3.11 launch exited before a numerical attempt because
that interpreter had no psutil. The successful attempt used Python 3.14 and is
the only numerical execution. Full stdout/stderr, probe hash and exact wall
accounting are in `receipt.json`, `stdout.txt` and `stderr.txt`.

This supports finite, balanced transfer in this one model. The BL5 local law
uses shell top-surface translation and a two-component director gap; it does
not constrain shell-normal spin directly. The observed moment is consistent
with distributed interface action, but the saved aggregate cannot separately
quantify its force-arm and nodal-covector contributions. Do not infer physical
accuracy, mesh-uniform stability, a selected multiplier space, or G0/F03
acceptance from this screen.

Next action: define a physically matched Mz reference with the same five
continuous work channels, shell surface/beam axis offsets, support semantics,
and measured interface action before requesting another external solve. Reuse
the saved F5/E02 and projected-assessment evidence for applicable controls.
Do not compare this result to a six-row nodal-spin or fully welded surface
reference as though their connection laws were identical. The consumer
current-main installed packet remains pending separate authority.
