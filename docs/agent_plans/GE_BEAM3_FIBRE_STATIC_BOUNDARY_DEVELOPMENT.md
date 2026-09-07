# Static interface required by native element transactions

Parent 1f99d128bb10964a2fc3d47c4159c46be01a6312, tree
5788e364dd4d11bd68b8406627e726badc1d31f9. Preserve the retained physical-fibre
potential, section law, loads, all earlier drivers and qualification evidence.

The current scalar nonlinear dispatcher expects 18 external element DOFs.
The retained beam has 24 additional internal coordinates: six physical cell
rotations and eighteen constitutive resultants. First provide an explicitly
STATIC stationarity boundary at fixed nodal coordinates/frames and accepted
material origins. Its Schur Hessian is Hqq-Hqi Hii^-1 Hiq from the same full
potential. Include internal spatial dead-line-load work when supplied. Retain
analytic spatial rotation Jacobian corrections in the local Newton equations.

No history is committed or inferred. Initial cell rotations/resultants and
accepted origin are explicit inputs; output history is only a trial candidate.
At most 24 internal updates and 8 line-search cuts, with a 60-second deadline.
Use the unchanged 1e-11 stationarity scale. Fail closed on local singularity,
chart/resource/iteration failure; do not return a partial response.

This boundary is not authorized for mass, modal or transient condensation:
physical cell inertia must be retained in a separately qualified dynamic path.
It is a prerequisite to native token-bound material transactions, not their
completion. Public routing, defaults and current beam/shell mechanics stay put.

Six tests cover straight/curved elastic and curved plastic stationarity, Schur
work and symmetry, independently differenced condensed energy/residual with
line work, fixed-origin unloading/replay, cancellation/failure and immutable
outputs. These are implementation checks, not an independent formulation
oracle. Smoke the three stationarity cases first; failure stops the candidate.
After the complete rehearsal passes, freeze and run two fresh bounded cycles;
canonical packets must match. Each test child: one numerical thread, 24 GiB,
600-second wall, 120-second inactivity, no retry. Independent review and the
full production/connection qualification remain outstanding.

## Unfrozen boundary correction

Initial smoke: three stationarity cases passed. The first complete rehearsal
had five passes and one failure before unloading evaluation: the wrapper called
the section's paired-history validator under ambient Decimal precision 28.
Existing retained-driver and physical-cell validation require precision 80.
Wrap only the new boundary's origin validation in an isolated 80-digit context;
do not alter any history values or section arithmetic. Extend the unloading
test to run under caller precision 16 and require that caller setting to be
unchanged afterward. Preserve the failed rehearsal as a separate inventory.
