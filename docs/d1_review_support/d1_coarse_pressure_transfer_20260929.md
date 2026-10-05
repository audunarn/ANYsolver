# D1 coarse pressure functions on the saved fine structure — development check

## Decision question

The independently bounded minimum squared pressure dual ratio drops from
`[0.59161649, 0.59313747]` for 48 settled-active Q1 modes on the saved 16×8
source to `[0.43278269, 0.44315587]` for 96 active modes on the saved 32×8
source. Does refining the structure weaken the *same physical pressure
functions*, or does the lower value require pressure functions added by the
fine basis?

This check maps the 48 coarse active Q1 hats by exact linear x interpolation
onto the 32×8 pressure grid. It evaluates their full `diag(S) D(gbar)` work
against every admissible coordinate of the saved fine shell structure. The
target is fixed; the source has the same guided, planar fixture and y knots as
the previous scalar-reference check. The two saved poses are separate accepted
equilibria, so this is a matched physical-subspace comparison rather than an
exact same-pose nested structural experiment. The mapped space is not the
32×8 settled KKT critical cone.

## Result

| Check | Result |
|---|---:|
| Transferred Q1 Gram vs independently clipped mass | 1.329e−15 relative |
| Transferred full pressure work vs independent source transverse mass | 3.082e−13 relative |
| Structural response solve residual | 2.346e−14 relative |
| Nonzero transferred fine pressure modes | 96/96 fine settled-active modes |
| 512×512 Fourier omitted-mode upper bound | 1.284% of finite compliance |
| Minimum squared dual ratio, 48 coarse functions on 32×8 structure | `[0.59169812, 0.59322070]` |
| Prior minimum, same functions on 16×8 structure | `[0.59161649, 0.59313747]` |
| Prior minimum, all 96 fine settled-active functions | `[0.43278269, 0.44315587]` |

The transferred interval overlaps the coarse interval closely. At the *same*
saved fine pose and structural metric, the lower 96-mode minimum requires a
direction outside the transferred 48-dimensional pressure subspace. Structural
x refinement does not materially weaken detection of those 48 functions in
this fixture. An independent read-only review checked the interpolation, full
structural work and reference comparison. It cautioned that this result does
not attribute the observed physical pressure or force changes to the extra
modes. The scalar Fourier interpretation uses the source-transverse reduction
verified separately on the same fine pose. This local separation does not
prove mesh-uniform stability, pressure convergence, deformable-target mechanics
or D1 acceptance.

After adding explicit guards for coarse pressure-node ordering and that all
nonzero transferred modes lie in the fine settled-active span, the final
bounded replay took 22.56 seconds. Its sampled process-tree RSS peak was
362.39 MB, while the process's own recorded peak working set was 410.95 MB;
use the larger value for the resource statement.
Both remain below the existing 180-second/1-GB development cap. The run used
the isolated worktree's source at base commit `2c454310`, Python 3.14, and no
new coupled equilibrium solve. [Final raw output](d1_coarse_pressure_transfer_final_20260929.json),
[resource record](d1_coarse_pressure_transfer_final_resource_20260929.json) and
[captured log](d1_coarse_pressure_transfer_final_log_20260929.txt) retain the
exact inputs and module path. Earlier [first](d1_coarse_pressure_transfer_20260929.json)
and [second](d1_coarse_pressure_transfer_v2_20260929.json) runs remain
development history; their numerical intervals were identical.
SHA-256: final runner `D7D0B341DC5761C236C42BBB0ADBC3694C359BAF8EBA2BD34AA69E711385CF77`;
final raw `DAE7171A543AB18EE17D02C8CFE1B9D5C9BE6FD57BCE12126DD079CDD477C9E0`.

**Next decision:** Treat fine pressure resolution and the near-rim partial
support as the principal unresolved pressure-space question. Preserve the
current physical pressure modes and D1 criterion. Any further expensive mesh
run needs a declared discriminating hypothesis and resource preflight; this
single transfer is development evidence, not a substituted acceptance gate.
