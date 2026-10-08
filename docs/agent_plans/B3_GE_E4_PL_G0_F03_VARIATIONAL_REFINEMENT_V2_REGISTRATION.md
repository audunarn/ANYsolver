# F03 independent classical line: three-axis refinement registration

21 September 2026. Status: **registered exploratory execution only**.
F03/G0B remain open. This reuses the exact frozen classical variational
source of the v1 pilot, preserving its applied load/line virtual work,
section constants, four-point shell pose and root support. Its v1 raw
manifest, preflight and records SHA-256 are required to match their
historical identities; **all five current inherited source hashes must
also match the sealed v1 manifest**, not only the old raw-file hashes,
before an exclusive v2 root is created. Freeze
this runner and registration at a clean integration commit and obtain
independent pre-execution mechanics/code review before running once.

The previous 32-case pilot found an 11.8–12.5% P0/P1 tip spread, a
23–30% smooth response change on beam-subcell refinement, material
shell changes, and pointwise sampled gaps. This inventory changes one
resolution axis at a time while keeping the same classical model and
weak bond law. It is not a new native B3/E4-PL candidate.

For each Q4/S3 panel, smooth/sine load and weak P0/P1 test, run these
eight `(Ns,Ny,Nm,beam subcells per mortar cell)` cases:

```text
16,8,8,16     # 128 beam subcells; first mortar level
16,8,16,2     # 32 beam subcells; first beam level
16,8,16,4     # 64 beam subcells
16,8,16,8     # 128 beam subcells; anchor for all three axes
16,8,16,16    # 256 beam subcells
16,8,32,4     # 128 beam subcells; third mortar level
32,16,16,8    # 128 beam subcells; second shell level
64,32,16,8    # 128 beam subcells; third shell level
```

This gives 64 cases. For both loads, add crossed shell controls
`16,16,16,8`, `32,8,16,8`, `32,32,16,8`, and `64,16,16,8`
for both shell types and both weak tests: 32 additional cases.
Total: **96 distinct cases**, run serially.
The fixed-beam mortar sequence is 8/16/32; the fixed-mortar beam
sequence is 32/64/128/256; shell length and transverse width jointly
double at 16/8→32/16→64/32, with crossed controls disaggregating
*each* shell length/width doubling. There is no external solver in
this inventory.

Every response records the tip and station motions, shell and beam
energies, line work on each side, support force/moment, native units,
normalized assembled weak residual, sampled scaled pointwise gap
**lower bound**, row Gram ratio, matrix dimensions/nnz, case resource
use and failure details. Preserve the v1 physical scales: characteristic
translation `U=1e6/(210e9·.07) m`, yaw length `.46 m`, line length
`1 m`. A printed near-zero quantity cannot serve as its only relative
denominator. For refinement/law tip differences use
`|a−b|/max(|a|,|b|,0.01U)` and report signed load responses.

Preflight reuses the v1 independent cantilever/rigid-pose self-check and
four- versus six-point coupling quadrature check (`≤1e−11` relative).
Every case must have full row-normalized constraint Gram rank above
`1e−12` relative; finite output; free equilibrium, both force balances,
moment and doubled-energy work balance `≤1e−8` relative; interface-work
cancellation `≤1e−8 J`; normalized assembled weak residual `≤1e−9`;
force/moment quadrature errors `≤1e−6 N/Nm`. A numerical failure is
preserved and blocks a physical comparison, never replaced by an
estimated result or a new hidden case.

For a *provisional* classical comparison, preregistered warning screens
require all of these for both loads and shell types: P0/P1 difference
`≤1%` at the finest fixed-beam mortar level; each law's terminal
mortar 16→32, beam 128→256 and shell 32/16→64/32 tip change `≤1%`;
sampled physical gap `≤.05 U`; and each of the eight separate length
or width edges across the two crossed shell-refinement rectangles has
a tip change `≤1%` under the same normalized measure. A sampled lower
bound below `.05 U` is insufficient to certify a continuous gap. Even
if every screen passes,
this three-level *classical* model is not a native target without a
continuous-gap upper check, local multiplier stability, matched
section/shell idealization, independent external numerical comparison,
and six-channel torque/shear and eccentric mechanics. The existing G0
physical tolerances and complete G0–G6/B2 gates remain unchanged.

The one-time supervisor records frozen source hashes and imported path,
previous v1 raw hashes, Python/NumPy/SciPy and thread settings, manifest,
preflight, all stdout/stderr, flushed records and resources under a new
exclusive root. It checks a clean committed worktree and preflight
before creating that root, uses one BLAS/Numba thread and serial child
cases, sampled child RSS ≤8 GiB, 900 s/case and 7,200 s total, polling
every 0.5 s. RSS is sampled, not a hard whole-tree peak. Never overwrite
or discard a failed run. Require independent post-run raw evidence and
mechanics review before interpreting trends. No G1 production integration
or F03 acceptance follows merely from successful algebraic solves.
