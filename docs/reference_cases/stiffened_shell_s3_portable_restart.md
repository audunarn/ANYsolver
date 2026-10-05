# Experimental portable S3 restart candidate

The explicitly selected admission identity is
`B3_GE_S3_RESTART_PORTABLE_CONSISTENCY_V1_DEV`. Strict legacy restore, framing,
default meanings and the model-bound V2D reader remain unchanged. This candidate
is wired into an isolated opt-in restore candidate, but is not adopted or
scientifically accepted. The current candidate rejects the unchanged old seed;
it does not yet provide portable restart.

The old unloaded seed contains paired accepted/predecessor S3 blobs. Their alpha
and plastic strain are identical for all four elements; elements 1/2 retain
nonzero plastic history and elements 3/4 have zero history. This supports an
elastic unloading hypothesis, but admission must prove its branch margin. The
general yielded-update certificate remains required.

## Implemented private draft

`_stiffened_shell_s3_restart_certificate.py` uses private directed Decimal
arithmetic for bounded three-node, 4x4 and scalar witnesses. A 65-term Rodrigues
series with an analytic remainder encloses each physical/local rotation on the
explicit four-radian evaluation domain. Each node independently supplies

`Rfit_i = Exp(theta_i) anchor_i Exp(-phi_i)`.

The draft does not average these frames or echo a saved local vector as its
expected value. It checks quaternion projection defects and the largest
Procrustes eigenspace using a checked spectral residual and separation.
Translations independently check the same fitted frame. Error components retain
metres for translations and radians for rotations. Unresolved chart, separation
or evaluation domains fail explicitly.

Material verification uses the exact saved predecessor, initial fields and
history. The inactive branch must preserve alpha/plastic strain exactly. For a
yielded branch, the scalar equation is

`F(lambda) = phi_squared(lambda) - flow(alpha_parent + lambda*g(lambda))^2/3`.

On a positive monotone hardening branch, `-F' >= -phi_squared' > 0`. The actual
consistency residual divided by this derivative lower bound encloses the root;
the existing `1e-10` local criterion remains a cap, not an added state tolerance.
Stress, alpha, plastic strain, layer fields and generalized resultants must lie
inside the resulting same-parent enclosures. Unresolved yield/hardening branches
or scalar floors fail explicitly. Physical/local uncertainty is propagated into
these material intervals, including yielded updates. This is draft code and
requires functional checks and independent review.

## Complete work map draft and publication

Global admission cannot use only `D.T delta_f`. With `g = P^-T D.T f`, it must
also cover the pullback differential and additive-chart inverse uncertainty.
The draft encloses the first differential using the bounded 5x5 system

`B = [[lambda*I - M, q], [q.T, 0]]`,

`dq/dx = (B^-1)[:4,:4] (dM/dx) q`.

A checked approximate inverse with `eta = ||I - B*inverse|| < 1` gives an inverse
error bound `||inverse||*eta/(1-eta)`. Propagate the certified quaternion/eigenvalue
enclosures through this system and the quaternion rotation polynomial. For each
node, differentiate `T_i = Rfit.T Exp(theta_i) anchor_i`, then the bounded SO3
logarithm. Compare this enclosed differential with the actual receiver `D`.
It encloses `P^-T` separately with its own bounded 3x3 inverse certificate. All work
is local; no global dense operator or full loading-path replay is needed.

The final interval spatial residual must fit within the existing `1e-8` free
equilibrium cap; the existing `1e-9` constraint check stays unchanged. The
publisher installs original accepted histories and checkpoint bytes, reports
the selected admission identity, and leave the live owner unchanged on failure
or cancellation. This implementation still requires independent proof review;
syntax and isolated passing controls do not establish admission.

## Bounded development checks and current obstruction

Evidence is preserved under
`.qualification/b3-ge-e4-pl/r8-native-s3-portable-candidate-dev-20261005-v1`.
All numerical children use the existing 600-second, 2-GiB supervisor, one CPU,
one numerical job, one thread per pool and disabled JIT. Runtime files verify
the isolated NumPy 2.5.3, SciPy 1.18.1, Numba 0.68.0 and llvmlite 0.50.0 imports
and actual Haswell pool dispatch. Source, fixture and wheel hashes are retained
in bindings; executed source copies precede each child. No fixture was changed.

Version 1 produced **3 passed, 1 failed**: the predecessor physical-pose
corruption was incorrectly admitted. The original implementation returned its
association defect as uncertainty without independently consuming that
predecessor certificate. Version 2 adds an archive-independent receiver fit
gate for both families and checks predecessor strain, elastic constitutive
relation and alpha/yield admissibility using its actual committed history.
It produced **4 passed, 3 failed**. The unchanged old seed now fails the receiver
fit gate before material/work validation; yielded-update and continuation
setups fail at the same gate. Corruption tests reject, but material-corruption
rejection can occur at this earlier gate, so that result does not independently
validate the downstream static check. The strict-default rejection passes.

The witness-only version 3 stopped before pytest because its runner selected a
nonexistent isolated dependency path; the actual-import guard caught the older
global runtime. That failure remains preserved. Correcting only that path with
fresh version 4 output produced **1 failed** in 1.49 seconds, with no admission
change. Its first failing component is predecessor local rotation index 3:

```
saved: -2.57636486091036909078675895636270014137092498884840097161941230297088623046875e-11 rad
lower: -2.57636486077163879219944527136605035995977989925617120483901906606104829e-11 rad
upper: -2.57636485747967744175882934512556564888533454269959133822330549547295746e-11 rad
```

The preceding three translation components are inside their intervals. This
witness does not establish which missing arithmetic term caused rejection.
The current gate certifies an exact centred covariance divided by its exact
squared norm. The primal instead rounds reference/displacement centring,
reference norm and divisions, constructs two Davenport contributions
separately, and pivot-refines using the producer eigensolver's top eigenvalue
(`_ge_beam3_variational_shell._quaternion_jets`). The stable translation uses
the quaternion increment directly; it does **not** subtract an evaluated unit
diagonal. No allowance for that nonexistent subtraction is justified.

A final bounded source-DAG coefficient candidate now encloses rounded nodal
means/subtractions, the nine-entry norm dot and square root, reference and
displacement divisions, three-term covariance dots, each separate Davenport
contribution and their final addition. Its receiver eigenpair enclosure is
independent of archive discrepancy; it makes no producer eigenvalue guarantee.
Version 5 tested only the affected old-seed positive case and original
predecessor-pose corruption: **1 passed, 1 failed**, 3.09 seconds pytest. Both
unchanged physical/local families now pass; the altered predecessor pose still
rejects. The positive case passes predecessor field and elastic constitutive
inclusion, then fails station 0 stress/alpha yield admissibility. Its required
inequality is

`sup(phi_squared(C*(epsilon_physical-epsilon_p_committed)) - flow(alpha_committed)^2/3) <= inf(1e-10 * max(flow(alpha_committed)^2, 1))`.

The propagated physical-coordinate/field interval cannot certify that original
margin. Numerical endpoint values for this bound were not emitted by the test;
no size or sign beyond the recorded failed inequality is claimed. Global work
margin and continuation were not reached. Tightening dependency enclosures may
be a future option, but this result does not authorize widening the cap or
discarding the predecessor material invariant. The final bounded candidate
stops here. Its runtime and source snapshots are in the same evidence directory
under version 5; all earlier failures remain intact.
The legacy archive stores neither the producer top
eigenvalue nor its backward-error witness. The receiver's checked eigenvalue
does not prove an a priori bound on the producer eigenvalue used in pivot
refinement. Such a bound needs an explicitly justified algorithm contract, or
admission must fail when the independently certified physical/material margin
cannot establish consistency. Saved-rotation residuals must not become their
own acceptance allowance. No empirical floor, widened tolerance or producer
arithmetic guarantee has been adopted.

Old-seed restore/continuation, supported plastic continuation, downstream
corruption discrimination, independent proof review and an installed boundary
check remain mandatory. No portable capability or qualification is claimed.

## Root disposition: stopped candidate, source preserved

The final V5 result does not demonstrate usable admission. All seven executed
source/test files match the final binding and are retained byte-for-byte in
`closed-candidate-source/`, with a baseline/source/disposition manifest. The
five modified owner/service files are restored to delivered HEAD; the two new
candidate package/test files are removed from the working import path after
verified preservation. The public solver has no new restore policy from this
experiment. No default, archive, fixture or scientific cap changed.

This closes the bounded diagnostic route, not the portable-restart obligation.
The exact predecessor yield-certification obstruction and all V1--V5 failures
remain evidence. Global consistency, continued plastic stepping, independent
proof assessment and installed portable acceptance were not reached. A future
archive-witness design requires a distinct technical decision; no automatic
interval expansion or legacy producer theorem follows from this result.
