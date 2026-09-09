# GE-B3 coupled physical-fibre cell — development checkpoint

Parent `7b8daa273c29fdacba7253be94a9074964314ea5`, tree
`29fb7be323247543b07667e30cf7d5d12d5f6f7c`.
Independent scientific review **PENDING**. Production qualification **false**.

## Implemented

The two-half-cell complementary problem now uses the actual physical-fibre
incremental potential with shared axial/shear coordinates and independently
stationary curvature. Every station and fibre participates in the coupled
solve. Recovered moments equal interpolated endpoint moments; weighted station
forces balance the retained half-cell forces. The gradient is the full work
map of shared strain and weighted curvature, and the Hessian uses the current
algorithmic material operator, not a substituted elastic energy.

The solver has fixed-origin, immutable cell-bound fibre history, paired fields,
physical fibre recovery, explicit semismooth labels, cancellation checkpoints
and a 60-second cooperative deadline. It permits at most 48 Newton updates and
4096 known material partitions per line minimization. Its private development
extent is 4–32 stations and at most 32 physical fibres per station; each
half-cell requires at least two distinct stations to resolve endpoint work.
An invalid/nonpositive tangent fails closed; no floor or pseudo-inverse is used.

## Failed development attempts retained

The first inventory failed before physics checks: the model helper returns a
tuple, and the arithmetic solver expects list rows rather than frozen tuples.
Both failed source files and the 23-failure inventory are archived.

After correcting those interfaces, the prototype returned 13 passes and 10
failures. Five assertions had an incorrect curvature-array index in the test.
The other five high-contrast paths genuinely hit generic backtracking/Newton
limits. These failures and the corresponding source files remain preserved.

The successor uses the known affine fibre-strain yield/table-knot crossings to
partition the actual one-dimensional energy. It minimizes each quadratic
segment and verifies decrease. The constitutive potential, coefficients and
scientific tolerances are unchanged. This removes the slow crossing of narrow
elastic intervals observed at contrast 10^12; it is not a qualification waiver.

## Separate inventories

- Initial interface prototype: 23 failed, 1.896 seconds.
- Corrected interfaces/backtracking prototype: 13 passed, 10 failed, 12.876 seconds.
- Piecewise-line smoke: 23 passed, 10.574 seconds.
- Expanded mutation/regression inventory: 93 passed, 11.352 seconds.
- General-rotation cycle A: 95 passed, 11.994 seconds.
- General-rotation cycle B: 95 passed, 11.890 seconds.
- Final cycle A, including endpoint-work admission: 97 passed, 11.838 seconds.
- Final cycle B, including endpoint-work admission: 97 passed, 11.903 seconds.

The final cycles have **23 byte-identical JSON pairs**. Maximum observed
original-equation residual is `5.20753832712479e-19`, below the unchanged
`1e-11` checks. Maximum observed Newton updates: 15 of 48. These are small
correctness tests, not performance benchmarks or formal resource runs.
No resource request was created, consumed or reused.

Coverage includes contrast 1/10^4/10^12, linear and tabular hardening, native
station/fibre recovery, work, first/second variations, mixed coupling,
loading/unloading/reversal, replay/discard, R90 and general spatial rotation,
line-minimum stationarity, mutation detection and invalid/foreign history.
The ordinary-strain station evaluator and original force/work equations provide
different checks; all remain same-author work, not independent review.

## Preservation and next work

Archive: `C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-fibre-cell-development-20260907-66a90fe5910c`.
143 content files, 5,103,620 bytes; manifest 22,777 bytes, SHA-256
`2c648de68bd31c8c88ff67e4c725872ac678d3370775d4e32bcec734064065f6`.
Original temporary test outputs remain intact. Final source hashes bind the
last two 97-test cycles, not every earlier successful source variant.

Next implement the retained finite-rotation fibre element potential and bind
the cell history into global trial/commit/discard, recovery, restart and
final-state replay. Then run the curved two-macro loading/reversal checks.
General nonlinear coupled sections and measure-consistent material adapters,
loads/couples, cutback/arc-length/postbuckling, reference-backed buckling,
broader geometry/slenderness campaigns, packaging/performance, independent
review and objective eccentric/curved beam-shell connections remain required.
No existing B2/B3/Q4/S3 mechanics, public route, default or release changed.
