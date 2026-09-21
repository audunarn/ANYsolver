# F03-D1 v1: registered diagnostic design, not acceptance

21 September 2026. This new diagnostic addresses two anomalies in the
immutable F03-K0 v2 screen. The original evidence, criteria, local failures,
and unselected multiplier spaces remain unchanged. Execute this study once
from a clean reviewed integration commit, with an exact registration and a
new evidence directory. It is a **source-backed G0 experiment**, not an
installed-wheel qualification and not the full six-channel F03 gate.

## Frozen inventory and measures

The common native retained B3 and physical in-plane Q4/S3-V2D operators,
reference trace, and finite pose map are exactly those of F03-K0. Use Q4
and S3-V2D at `(N_b,N_s)=(4,4),(16,16)`; at each, test stations
`0.337,0.5-1e-7,0.5+1e-7` on both the original active differential-rail
plus retained-cell-yaw direction and the separate retained-cell-yaw-only
direction. The native fixed root is unchanged. For each, compare the same
analytic station trace to a *central difference through actual pose/chart
updates* at dimensionless steps `0.3,0.1,0.03,0.01,0.003,0.001,0.0003,
0.0001,0.00003,0.00001`, times the frozen displacement direction scale
`u*=1e6/(210e9*0.07) m`. Record individual finite planar derivatives,
absolute scaled norm and normalized error, physical perturbation length,
out-of-plane translation in metres and two rotation components in radians,
and independent multiplier virtual-work difference. Reproduce the original
`h=0.001` step and original `1e-10` threshold without modifying v2.

The parity inventory is six Q4 P1-shell solves: `(N_b,N_s,load)` of
`(4,2,smooth)`, `(8,8,alternating)`, `(16,8,smooth)`,
`(16,8,alternating)`, `(16,16,smooth)`, `(16,16,alternating)`.
Compare the work-scaled sparse full KKT, dense full KKT, and exact signed
retained-elimination KKT on the same model and load. Record pairwise forward
solution differences, each backward residual divided by
`||A||_F ||x|| + ||b||`, full scaled KKT singular ratio, retained block
condition, and coordinate counts. Full dense matrices are **bounded
diagnostic oracles** only, never production assembly. These cases include
the five v2 parity exceptions and a small control; both load histories at
`(16,8)` make the diagnosis load-sensitive.

The complete evidence grammar is one start, four derivative meshes in the
listed order, six parity cases in the listed order, and one terminal: twelve
JSONL records. Append and fsync after every record. A supervisor separately
attests the exact inventory, child exit, source/environment identity, logs,
raw hash and sampled peak child RSS. Exact registration identity includes
the clean source commit, the fourteen predecessor-runner sources, the full
tracked solver tree, the new scripts and this manifest, source/installed
package versions, import paths, Python/dependencies, hardware, threadpools,
and environment. One-thread BLAS and an explicit Numba cache are mandatory.
Use a 3600 s external wall limit and 4 GiB sampled RSS limit; a sampled
maximum cannot guarantee an instantaneous hard memory ceiling. Any run
abort remains evidence and requires a new reviewed revision/registration.

## Interpretation fixed before execution

An error plateau for one mesh requires **the same two adjacent step sizes**
to have both derivative and work normalized errors at or below the original
`1e-10` threshold for *every station and both directions*. Report the
plateau separately for each topology/mesh; a topology-wide plateau requires
a common adjacent pair across both of its mesh sizes. If absent, state that this finite pose
derivative oracle remains unresolved. A plateau permits a proposed new
finite-difference step for a separately reviewed future screen; it never
retroactively passes v2. Inspect nonplanar residual components and host
variation if the plateau differs by topology or station.

For each parity case, present pairwise scaled forward differences beside
the scaled KKT singular ratio and all backward residuals. A forward mismatch
can reflect ill-conditioning even when all backward residuals are small;
that is a numerical explanation to test, not an automatic waiver of the
frozen parity tolerance. If a dense full solution and sparse full solution
disagree beyond the tolerance, investigate sparse ordering/factorization;
if full solutions agree but condensed differs, investigate the signed
elimination, retained scaling, and cancellation. Any unresolved discrepancy
remains open.

No study status selects a multiplier. Revisit reduced multiplier spaces,
norm-scaled physical trace modes, and refinement independently after D1;
the required six-channel torque, director/shear, eccentricity, curved
interface, thickness and 1:8 reciprocal checks are still foundational G0.

Preexecution review checks source contracts, exact inventory, finite-pose
directions, work scaling, parity elimination and evidence single-use
enforcement. Postexecution review recomputes hashes, inventory, plateau
disposition and parity interpretation without modifying raw evidence.
