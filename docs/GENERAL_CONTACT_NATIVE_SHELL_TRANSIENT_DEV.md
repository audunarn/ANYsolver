# Native beam–S3 common-stage development candidate

## Status

Implemented and **verified against the assigned development criteria** in a
private installed artifact: eight shell selectors, eight changed-route compatibility
selectors and the public CLI passed. Engineering acceptance and release remain
separate. The native–native pair's earlier purse and evidence were not pooled.
The exact execution disposition is saved in
`C:/ANYworkspaceWork/contact_native_shell_c8_20261007/author_execution_disposition_v2.json`.

The explicit public selector is `ge_beam3_native_s3_small_motion_transient_dev`.
Use `anysolver.create_native_transient_shell_analysis` and
`anysolver.solve_native_transient_shell` with the existing `TransientConfig`.
The root and `general_contact` namespaces expose the same additive functions.
The example `examples/general_contact_native_shell_impact_dev.py` declares every
contact, geometry, integration, path and small-motion control. Its development
smoke fixture has two steps of 0.003 s, horizon 0.006 s; restart uses one fresh
step plus one genuinely additional step. CLI arguments are `--steps 2 --dt .003`.

## Exact admission

One free, centered native B3_GE element and one free elastic S3 V2D element form
two separate bodies. Both retained native half-cells must have exact zero lift;
the cell constructor uses the retained reference instead of node-count inference.
The native stable SO3/precise-work arithmetic policy is explicitly selected by the
example. Existing native and connected policies/defaults are unchanged.

The shell is the exact `NativeParityE4PLS3V2DShellElement`, with three nodes and
18 DOFs, centered reference offset zero, positive density, isotropic elastic
material, no plasticity, shell section, loads, supports, point masses or activity.
The admitted physical side is **top**, director polarity **+1**, and the ordered
reference triangle normal must agree with that outward director. Other physical
sides and polarity profiles are refused. Arbitrary material node numbering and
insertion order are supported through the formulation DOF map.

The actual shell skin is `S_ref + W q`, where the existing S3 skin adapter includes
`offset * (delta_theta cross director)` in its rotation columns. Absolute shell
translation and per-node rotation limits are explicit; rotation is at most
0.05 rad. These are small-motion formulation coordinates, not finite shell
rotations. Each initialization, trial path and fresh restore revalidates side,
nondegenerate oriented area, rim, signed gap and small-motion admission. Changed
model/material/mass/stiffness/skin/contact definitions fail the identity guard.

The line penalty stiffness is in N/m², radius, rim clearance, geometry tolerance
and maximum penetration in metres; energy/force/tangent tolerances are J, N and
N/m. Maximum penetration is positive and strictly smaller than radius, so the
permitted signed height remains positive. Contact is frictionless interior line
measure; no cap-area or dedicated rim/endpoint force law is admitted.

## One retained descriptor equation

The common system has 60 unknowns: native 42 plus shell 18. There are 24 physical
coordinates (native 15 and shell nine translations) and 36 algebraic coordinates
(native 27 and all nine shell rotations). No child time stepper is called.
The private shared retained midpoint assembly and its transaction/controller
services are reused; the old connected graph guard is preserved exactly.

The native part retains finite-rotation physical inertia and complete internal
coordinates. The shell uses its formulation stiffness `K_s` and actual mass
`M_s`; its rotational mass rows and columns are exactly zero. Its equations are
`M_s a_s + K_s q_s + r_contact,s = 0`, including all rotational algebraic rows.
The native and shell contact residuals come from the same existing retained
line–S3 potential/pullback. The native 42×42 diagonal contact Hessian is converted
to spatial-work Jacobian before assembly; both 42×18 and 18×42 cross blocks and
the shell 18×18 block are retained. The complete stage chart is applied before
reactions (this exact free profile has none).

For physical unknown acceleration `u`, endpoint chart increment is
`d = h v0 + (h²/2) u`, stage configuration is half that physical increment,
stage velocity `v0 + (h/2)u`, and stage acceleration `u`. Native nodal algebraic
frames use the full algebraic increment; native cell frames use half the physical
cell increment at stage. Shell algebraic coordinates use `q_r0 + eta_r` at
stage, without a spurious half factor. The shell chart is linear. The stage
Jacobian includes `(K + d_config f_inertia) C_stage + (h/2)d_velocity f_inertia + M`.

At the physical endpoint the shared endpoint solver reestablishes all algebraic
equations at fixed physical coordinates and then physical acceleration balance.
This may change shell rotations and native resultants/frames. Shell rotations
move the offset skin even though their inertia and stored rate slots are zero.
Those slots are explicitly **non-inertial placeholders**, never material-surface
velocities or a claim that the shell skin is stationary. Endpoint native
resultants use the exact declared native tail, excluding appended shell DOFs.

## Declared swept path and finite resource budget

The native physical chart path is affine translation/Exp rotation. Exact zero
retained half-cell lift proves each physical contact half-curve is affine between
its current native material nodes; cell rotation still enters native inertia.
The shell physical skin path has two affine legs through the actual accepted
stage and the algebraically consistent projected endpoint. Endpoint projection
is part of the second leg and contact work uses the full accepted shell increment.
The path is a declared controller contract, not a Hermite or constant-acceleration
interpolation claim.

For each leg, exact rational polynomials from binary64 endpoint inputs use
`N = (S1-S0) cross (S2-S0)`, `h = N dot (P-S0)` and
`b_i = N dot (edge_i cross (P-S_i))`. Exact Bernstein hulls over rational
subintervals bound every polynomial, not sampled signs. Positive reference
orientation/nondegenerate area and **positive h** precede squared clearance:
`h² >= (radius - maximum_penetration)² |N|²`. Each positive rim numerator must
satisfy `b_i² >= (radius + rim_clearance)² |N|² |edge_i|²`. The native segment
ends suffice because signed height and each edge numerator are affine along a
zero-lift physical half-curve. Normal and edge norm upper bounds sum squared
componentwise absolute envelopes; a scalar maximum is used only in error terms.

Two uniform arithmetic envelopes cover evaluated endpoint-to-exact affine
inputs and exact interior-to-rounded advance/skin/reconstruction evaluations.
The allowance `2*(256*eps*magnitude + 64*smallest_subnormal)` conservatively covers
the bounded split-position reconstruction and at most six nonzero shell work-map
terms per coordinate; shell magnitude includes reference skin and the absolute
row sum of W times the complete coordinate maximum. Exact rational products then
propagate these component errors through edges, normal, signed height and rim.
These are arithmetic bounds, not inflated physical or contact tolerances.

**One prospective visited counter is shared by both legs.** Each processed
interval is debited before work, including intervals subsequently subdivided or
refused. At exhaustion the exception records total visited and the frozen total
cap; the second leg does not receive a renewed allowance. Unresolved signs,
geometry, rounding bounds or finite interval resolution fail with the retryable
path refusal. The shared controller may make only its finite configured cutbacks;
zero-gap activation is permitted within the explicit negative-gap budget.
The reported minimum certified gap is the proven threshold floor `-P`, labelled
as such; it is not a sampled minimum. Clear endpoints do not prove the path safe.

## Results, work and persistence

Kinetic energy, native elastic energy, shell elastic energy and normal contact
regularization storage are reported separately. Total energy is their sum.
Normal storage is not beam/shell constitutive work. Physical contact forces are
negative potential gradients; assembled internal residuals are positive gradients.
Pair forces and moments are both reported about global origin `(0,0,0)`.
Shell translational momentum and angular momentum gather actual nodal DOF slots,
so insertion order cannot change the moment ledger. There is no exact energy or
angular-momentum conservation claim for this finite SO3/small-motion method.

The new exact profile/checkpoint schema binds the native definition, actual shell
operators/material/geometry/skin work map, contact fingerprint and all explicit
limits. Shared prepare/commit/discard/replay services publish atomically. Pending
candidates cannot be checkpointed. Restore checks trusted digest, complete state,
physical and algebraic equilibrium, exact identity, skin/rim/orientation/gap and
small-motion admission before publication. Trajectory replay also reconstructs
actual stages, exact shell translation chain/reference correspondence, endpoint projection and both path certificates; saved diagnostics
cannot replace recomputation. Cancellation/refusal rolls back the current state,
issued receipts and candidates. Existing noncontact identities/schema/default
results are unchanged by the additive hooks.

## Executed development evidence

The separate human-authorized scope was 480 measured seconds, with 60 s protected
reserve, one process tree at a time, <=60 s/job and 953 MiB. Thirteen attempts
consumed **261.4690997000034 s** on the declared conservative wrapper basis;
**218.53090029999657 s** remain including reserve. Precise child launch-to-wait,
whole-tree duration, peak RSS, commands, input/source identities, stdout/stderr
and per-selector setup/call/teardown outcomes are retained in unique raw ns8_*
directories. No process remained alive. No other purse was used.

All eight selectors in `tests/test_general_contact_native_transient_shell.py`
have terminal pass evidence:

1. Actual formulation mass/open equations and permuted-node momentum.
2. Complete60 stage/contact/work derivative at both 1e-6 and 1e-7, offset rotation
   columns and both cross blocks; original 1e-5 gates retained. Scalar FD error
   values were not separately logged; the source-bound assertions/phase records
   establish the measured gate results.
3. Two accepted impact stages, both-body response, equilibrium, projected two-leg
   path, storage and force/moment diagnostics.
4. Exact fresh full2=fresh1+1 bytes, path-journal tamper and physically altered
   initial-shell-translation refusal with digest/accounting repaired.
5. Constant-plane touch with P=1e-3 radius and shared total path-cap exhaustion.
6. Clear-endpoint/intermediate-penetration and wrong-side path refusal.
7. Trusted direct capsule inversion and shell small-motion refusal.
8. Side/polarity refusal, changed definition, cancellation and trial rollback.

The installed wheel is `native_shell_dist_v2/anysolver-0.4.7-py3-none-any.whl`,
SHA256 `1383098ea2f4d03e383dfead546201208bd6ed5fc3989666286618c4b65f6709`,
with 555 package payload files. The private site is `native_shell_site_v2` under
the raw root. Before/final runtime guards verified actual imported module paths
and hashes, both public namespaces, JIT disabled, Numba 1 and all observed numerical
pools 1. Pytest source-path settings were cleared. Product payload remained unchanged
through the test-only repair; source/wheel/site identities are compared in the
final handoff. Final source comments/documentation are separate from the exactly
snapshotted executed test inputs; their executable AST is unchanged.

Preserved nonpasses: `ns8_restart_v1` failed because its tamper calls omitted the
producer max_steps64 and therefore hit configuration identity first. The repair
sets max_steps64/max_cutbacks8 explicitly in both calls and asserts the actual
refusal reasons; `ns8_restart_v2` passed. `ns8_compat_v1` timed out after six
complete selector phase passes. Its final runtime record was unavailable; one
bounded connected completion group supplied that evidence, while pair restart
and axial comparison ran separately. No physics, scientific tolerance, admission,
fixture or resource cap changed. No failed evidence was overwritten.

Eight affected connected/pair selectors passed. The registered historical connected
axial public result and capsule bytes match their actual producer baseline; this
is a matched-fixture comparison, not a universal legacy-byte claim. The actual
public CLI `--steps 2 --dt .003` completed two steps to 0.006 s. Prepared-result
captures preserve original returned objects but are labelled prepared records;
the initial-only capture must not be used as trajectory evidence.

Saved two-step diagnostics: maximum stage residual 3.4705519489074807e-14,
endpoint algebraic residual 1.1930365038732155e-20; contact force/moment balance
maxima 1.0408340855860843e-17 N / 8.819878370121108e-18 N m. Each step used two
certified path intervals total, one per leg. Second-stage gap was
-0.00018994377190514888 m with storage 2.370820103022937e-6 J. Rotational endpoint
minus stage norms were 1.234522681988844e-10 and 2.8503623776952006e-8 rad, confirming
actual algebraic skin projection. Energy 0.0204→0.02040012249944116 J has descriptive
relative change 6.0048745665099835e-6; these are fixture diagnostics, not temporal,
energy or engineering qualification.

Full programme rows still open: native curved/lifted contact, finite shell motion,
other sides/polarity, true rim/endpoint force models, native/shell friction and
broader multibody common-stage qualification. This development slice admits none
of those rows. Different-family independent engineering assessment remains unmet
under cached Mistral/local unavailability; supporting review and worker verification
do not establish engineering acceptance.
