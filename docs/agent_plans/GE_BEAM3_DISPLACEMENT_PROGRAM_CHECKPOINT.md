# GE-B3 native displacement-control development

## Scope

Private successor of `4255472ce948a7cbc6f52a36a7ed704ed1f027c3`.
The new `anysolver._ge_beam3_displacement_program` module adds native scalar
translation control and an unknown common load parameter to the preserved V4
beam/state infrastructure. No existing source file, beam/shell mechanics,
coefficient, tolerance, public selector, default or historical qualification
record is changed. Independent review and production qualification remain
pending. This is not a replacement for the full straight/curved beam and
objective beam-shell connection goal.

## Augmented solve and exact control

For net chart residual `R(u,p)` and a free translation `u_j = target`, the driver
solves the complete bordered Newton system `[K, R_p; e_j^T, 0]`. It does not
factor/invert `K` separately to form a load sensitivity. The nonsymmetric sparse
backend is used without modifying the tangent, regularizing a singular system,
deleting spatial modes or assuming a positive global stiffness.

`R_p` is assembled from each element's live, token-owned native load derivative
and the separately declared nodal pattern. This retains internal line-work
condensation and the native rotation-chart pullback. All trial evaluations use
the same preceding accepted section histories; neither parameter differentiation
nor line search advances state. Numerical differentiation is used only in tests.

The control equation is affine. Each initial guess and backtracking trial is
placed exactly on its prescribed translation plane before evaluation. Other
free coordinates and the load parameter are solved together. This does not
impose a new support or replace the equilibrium equation at the controlled DOF:
all free force equations still have to pass. The plane enforcement changes no
accepted displacement or material origin until the complete step commits.

The current control is one `ux`, `uy` or `uz` coordinate at an explicitly named
free node. Rotation control, general functionals, arc length and adaptive cutback
remain separate work. Supported model boundaries are inherited from the force
driver: native V4 standalone models, homogeneous supports and complete rotational
support blocks, no MPC/activity/point masses/mixed formulations, and bounded size.
The force-pattern capture helper is reused with a nonexecuted dummy target only
to capture model/pattern ownership. The displacement program has its own schema,
identity, target interpretation, unknown parameter and restart record.

## Failure and restart safety

Explicit targets, iteration/backtracking bounds, control identity and load
patterns are bound into the global capsule. Each record stores the prescribed
displacement and the solved parameter. Restore validates every typed element
state at its original accepted origins, global/local displacements, epoch/cursor,
parameter, physical-reaction replay, free equilibrium and the control equation.
The force-program schema cannot hot-restart as displacement control.

The complete capsule is staged before the accepted pointer swap. Cancellation,
failed line search, exhausted iterations, singular parameter columns, invalid
evidence and observer mutations leave the previous accepted capsule intact.
There is no automatic retry. The 600-second deadline is cooperative; formal
execution still requires the independent process-tree/memory watchdog. Canonical
parsing retains duplicate/nonfinite, exact-key/type, size and depth rejection.

## Genuine development failure and correction

The first 20 small algebra, elastic, plastic, derivative and restart tests passed
in 51.18 seconds. A newly added coarse two-element arch then exhausted its
16-update bound, first in 42.88 seconds and again with diagnostic tracing in
42.90 seconds. Neither failed run accepted its first target. The traced failure's
checkpoint, status and progress are retained as failed development evidence.
The first run had no raw trace; its test failure is recorded, not reconstructed.

The trace showed line search gradually approaching the new control target while
balancing the force residual: the linear displacement equation remained violated
after 16 updates. This was corrected in the new, unfrozen driver by enforcing
the exact affine control plane on every trial. No mechanics, section constants,
target schedule, tolerances or iteration bounds changed. The revised 29-test set
passed in 74.38 seconds. A regression checks zero control error at every recorded
arch iteration, not just at final acceptance.

## Coarse arch observation and limits

The two-element arch directly reconstructs the preserved small specimen's
parabolic height `0.1` and elastic section diagonal
`[1000,400,400,0.02,0.01,0.02]`, using native V4 elements, all spatial free DOFs
and fully fixed ends. Crown drops `0.02, 0.04, 0.06, 0.08` completed in four
Newton updates each. Load parameters were approximately
`0.030853, 0.035721, 0.033876, 0.029418`: the sampled path has a decreasing-load
portion. No symmetry reduction or stabilization was applied.

This is a small driver capability observation. It is not a resolved critical
point, stability/PSD certificate, continuum accuracy comparison, convergence
study or engineering post-buckling qualification. Earlier formal arch/onset
records remain unchanged and unresolved where they were unresolved.

## Final verification and archive

The combined source regression passed **132 tests in 200.44 seconds**: 29 new
displacement checks, 39 preserved force-program checks, 28 native load/state
checks, 21 accepted straight opt-in checks, five generic state-cleanup checks,
and two five-node static evidence inventories. Python 3.13.9, NumPy 2.4.3 and
SciPy 1.16.3 ran with one numerical-library thread. These were small correctness
checks, not a performance campaign or formal resource request.

The corrected arch checkpoint, status and complete progress trace are
byte-identical between two fresh pytest processes. No installed-wheel check of
the displacement driver has run; the preserved force-driver wheel does not
cover this new source. No continuum/stability qualification is inferred.

Permanent archive:
`C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-displacement-development-20260906-39febb5ba037`

Nine files, **148,004 bytes**, retain the traced failure and both corrected
arch outputs. The canonical development record binds every file's bytes and
SHA-256. Exclusive copies were verified against all nine recorded hashes from
the normal workspace context. Only verified relay duplicates and empty relay
directories were removed; original temporary diagnostics remain too.

Each corrected checkpoint is 39,759 bytes with SHA-256
`2163ab9dd439a1451de9a386494f1566da23a75cb7f6b225566e35cf4cbe2866`.
Failed records remain failed; they were not overwritten or promoted.

## Continuation

Next: objective arc-length continuation, adaptive cutback and installed-wheel
validation of this new control path, then broader section/load/constraint parity,
loaded modal/buckling and straight/curved engineering qualification. Independent
review and objective beam-shell connection qualification are still required.
No release or activation is authorized by this development checkpoint.
