# Generalized-section retained-cell closeout

Implementation: `150353feb147a4b0b03d18320bf4d481e4a3b55b`.
Tree: `cf7724ac78a7af45728e6cb9030f6373265069b7`.
Base: `912933630ad2bb94f77741794d5c8279e8c4fd50`.

The five-file additive development gate passes. The six-resultant nonlinear
law now supplies the coupled station conjugate and retained finite-rotation
beam potential. It is not yet connected to the global native-state driver.
There is no production qualification, selector change, default change or
dynamic reduction authority. Existing physical-fibre, B2/B3 and Q4/S3 mechanics
and historical evidence are unchanged.

## Separate inventories

| Lane | Passed | Deselected | Supervisor seconds |
| --- | ---: | ---: | ---: |
| Smoke | 1 | 12 | 3.615 |
| Initial rehearsal | 13 | 0 | 5.821 |
| Complete rehearsal | 16 | 0 | 6.225 |
| Frozen cycle A | 16 | 0 | 6.622 |
| Frozen cycle B | 16 | 0 | 6.421 |
| Previous six-resultant section | 23 | 0 | 4.215 |

All tests passed with zero XML failures/errors/skips, empty worker stderr,
exit code zero, and zero remaining process-tree descendants. Each child used
one numerical thread, 24 GiB, 600-second wall and 120-second CPU-inactivity
limits. At most three children ran together. Longest observed supervisor
duration: 6.62247020000359 seconds; largest peak memory: 205144064 bytes.
No automatic retry or failed scientific attempt occurred.

All 16 scientific files match byte-for-byte between complete rehearsal and
both frozen cycles. The separate section regression's 23 scientific files
match the previous external section archive exactly. Runtime guards passed
before/after frozen runs; their scope is configured versions plus Python
executable identity, not a complete dependency graph. Existing Git ignore
permission warnings are retained without global configuration changes.

## Mechanical evidence and limitations

Independent station forces minimize the complete complementary section
potential subject to shared-cell force constraints. The station moment field
retains endpoint interpolation. The consistent 18x18 compliance differentiates
the entire constrained problem, including coupling between station force
solutions and moments. Histories remain fixed during all Newton/line-search
evaluations and returned proposals do not commit a global state.

The independent audit uses the separately authored primal section KKT solver
and reconstructs the opposite primal strain elimination. It verifies force
and moment work, compatibility, curvature, material state and full compliance.
It imports no producer cell/beam code. Separate authorship/algorithm does
not replace the still-pending independent review.

The retained 42-coordinate evaluate method is AST-identical to the frozen
physical-fibre geometry method except diagnostic strings. Material evaluation
uses the new conjugate. First/second variations, proper spatial re-expression,
large common rigid motion, native material-resultant recovery, loading/
unloading/reversal, 4/8/16 station coverage and output mutations pass.

Maximum recorded independent section/cell/history discrepancy:
3.2825635973857327e-16. Maximum finite retained tangent directional discrepancy:
8.233147109090028e-11, below the 1e-7 directional gate. Maximum rigid-motion
tangent covariance discrepancy: 1.823072505922178e-15.

Reference-state static condensation was checked numerically for straight and
curved fixtures. Six analytical rigid columns have normalized null errors
at most 4.586143447719159e-17. Their 12-dimensional complements are positive
(minimum eigenvalues 3.7180869753880477 and 3.6017504587696263).
This does not establish exact rank for all geometries, nonlinear stability,
mass, modal/buckling accuracy, locking, or production-scale qualification.

Generalized recovery supplies declared resultants and section histories, not
invented fibre stresses. Perfect plasticity/softening of this ellipsoidal
model remains outside its positive-hardening conjugate; existing physical-fibre
capabilities are unchanged.

## Preservation and next action

Archive: `C:\Users\AudunArnesenNyhus\AppData\Local\ANYrelease\ge-beam3-generalized-cell-150353f-20260908`.

128 data files plus the manifest preserve all six inventories, scientific
outputs, XML/stdout/stderr, commands, supervisor observations, frozen source
extent, unchanged authorities and audit. All files were checked by byte count
and SHA-256 after copying.

Manifest: 20,074 bytes; SHA-256
`FFE68DA2EA179BDA39DD5BDB250BBE6EC65A5B152CE95A971920A226D993E174`.

Original run directories and historical archives remain intact. Only the
verified redundant transfer directory may be removed.

Next is actual generalized-section static condensation and global native
trial/commit/discard/restart integration. Full solver-path/material parity,
consistent mass/modal/prestress/buckling, slenderness/curved engineering,
independent review/package integration and objective beam-shell joints remain
open. The overall production goal remains active and incomplete.
