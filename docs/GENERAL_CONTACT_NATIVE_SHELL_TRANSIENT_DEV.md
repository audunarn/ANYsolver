# Native beam–S3 common-stage development candidate

## Status

Implemented source candidate; **UNVERIFIED**. No solver or reference imports,
pytest, builds, installs, examples or numerical jobs have run for this slice.
The native–native pair evidence belongs to its separate fixture and authority.
This guide makes no engineering acceptance or release claim.

The explicit public selector is `ge_beam3_native_s3_small_motion_transient_dev`.
Use `anysolver.create_native_transient_shell_analysis` and
`anysolver.solve_native_transient_shell` with the existing `TransientConfig`.
The root and `general_contact` namespaces expose the same additive functions.
The example `examples/general_contact_native_shell_impact_dev.py` declares every
contact, geometry, integration, path and small-motion control. Its prospective
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

## Prepared checks and separate execution proposal

Eight selectors in `tests/test_general_contact_native_transient_shell.py` cover:

1. Actual shell mass/open equations and permuted-node momentum.
2. Complete 60-coordinate stage/contact/work derivative at both 1e-6 and 1e-7,
   nonzero offset rotational columns and both cross blocks (1e-5 gate).
3. Two actual accepted impact stages, both-body response, equilibrium 1e-11,
   declared path, storage/force/moment diagnostics and linear momentum 1e-6.
4. Exact fresh full2 versus fresh1+1 bytes and trajectory tamper refusal.
5. Constant-plane touch with P = 1e-3 radius and shared two-leg cap exhaustion.
6. Clear-endpoint/intermediate-penetration and wrong-side path refusal.
7. Trusted direct capsule inversion and shell small-motion refusal.
8. Side/polarity refusal, changed definition, cancellation and trial rollback.

No selector has been executed. A separately authorized first installed-artifact
plan should allow up to **480 measured seconds total**, reserve 60 s, with one
process tree at a time, at most 60 s/job and 953 MiB, JIT disabled, Numba/BLAS pools
one. This estimate is prospective; shell costs have not been measured. Suggested
caps: private offline build25/install10; mass/geometry/admission group30;
derivative50; impact45; restart60; rollback35; CLI45; changed shared-owner legacy
compatibility60. These job caps total 360 s, with 60 s retained reserve and up to
60 s for scoped repair inside the prospective 480 s total. Remaining allowance permits concrete scoped diagnosis/repair,
not automatic sweeps. Every attempt must bind source/wheel/site/tests and record
precise wall duration, effective runtime/import hashes, full outputs and charges.
Build/install must use isolated private paths without downloads/global installs.
Verify public namespaces resolve installed payload, overcoming pytest source-path
settings. Shared changes need actual default connected historical byte comparison
where matched saved fixtures exist plus affected controller/refusal regression;
source AST equivalence alone does not establish byte parity.

Full programme rows still open: native curved/lifted contact, finite shell motion,
other sides/polarity, true rim/endpoint force models, native/shell friction and
broader multibody common-stage qualification. This source slice admits none of
those rows and consumes no execution authority.
