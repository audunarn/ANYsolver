# D6 centered finite inertia: prospective development contract

Frozen before source authoring, 2026-09-30. This first C7 slice is a pure inertial
owner, not a midpoint/time integrator, scientific acceptance or public admission.
Source/test ownership is confined to the two new files in the managed worktree
`C:/Users/AudunArnesenNyhus/.codex/worktrees/general-contact-native-dynamics/ANYsolver`;
this note and fresh evidence remain in the main development worktree.

## Exact API and semantics

`evaluate_centered_finite_inertia(reference, section_inertia, positions_high,
positions_low, cell_rotations, velocity, acceleration, *, order=24,
momentum_origin_high=(0.,0.,0.), momentum_origin_low=(0.,0.,0.))`

returns immutable `CenteredFiniteInertiaResponse`. Reference must be the exact
existing centered reference type; order is an exact integer in `(4,8,24)`, not
bool. Inertia is the existing positive symmetric physical 6×6 section matrix.
Positions are normalized finite `(3,3)` high/low pairs; origin is a normalized
finite `(3,)` pair. Cell rotations are two proper spatial rotation matrices.
Velocity/acceleration are finite `(24,)` arrays, in external nodal 18 then cell
spin 6 ordering. Cell angular velocity/acceleration and increments are spatial;
configuration derivatives hold the supplied spatial velocity/acceleration fixed
and use left cell increments `U_new=Exp(eta)*U`.

The response exposes the original physical `(24,)` force/momentum and `(24,24)`
mass/velocity/configuration derivative through `.physical`; convenience properties
retain these original dimensions. `.mixed_mass`, `.mixed_generalized_momentum`,
`.mixed_inertia`, `.mixed_velocity_derivative` and `.mixed_configuration_derivative`
zero-extend to the retained 42 ordering: nodal 18, cell spins 6, resultants 18.
Physical coordinates are nodal translations 9 plus cell spins 6. Nodal rotation
traces 9 and all resultants 18 are algebraic with exactly zero inertial rows and
columns. Nonzero velocities in algebraic nodal slots are inertially ignored,
not assigned a mass floor. Every returned array is an owned read-only copy.

## Mapping and physical momentum

A separate finite-kernel subclass is initialized with the exact immutable station
cache and section inertia produced by `_CenteredRestInertia`. It inherits only
the original `LiftedInertia.evaluate` finite work algorithm. No rest instance's
`evaluate` is called with finite velocity, and no rest guard is bypassed. Original
energy, M, generalized momentum, inertia, `dI/dv` and `dI/dq` are retained.

For cached station `(cell,left,right,t,R0,d0,measure)`, `Q=U*R0`, `d=U*d0`,
`v=(1-t)*vleft+t*vright+omega×d`, and section-frame momentum is
`[p,h]=Jsection*[Q.T*v,Q.T*omega]`. Position appears only in the physical angular
momentum lever arm. Recover it with the existing compensated affine
`station_position(high,low,cell,t,U,d0)`, preserving
`xstation=xleft+t*(xright-xleft)+U*d0` before final two-component rounding.

About the explicitly supplied momentum origin O,

`P=sum measure*Q*p`,
`H_O=sum measure*[(xstation-O)×(Q*p)+Q*h]`.

Exact products/sums of the supplied binary-float station values and compensated
position pairs are rounded to high/low momentum pairs. `.physical` reports their
high components; `.linear_momentum_low` and `.angular_momentum_low` retain residuals.
This compensates recovery, not the section law, reference geometry or finite
force derivatives. A translated common origin preserves H; with fixed O,
`H'=H+translation×P`. Relative high coordinates passed to the original kernel
affect only its unused angular recovery; finite M/I derivatives remain unchanged.

## Focused check authority

One new test process, 180 s / 1 GiB, fresh log/resource/XML evidence. Tests cover
unchanged rest-M parity; nonzero translation/spin with physical cross inertia;
left-configuration, velocity and acceleration directional derivatives with useful
recorded steps; linear/angular momentum covariance under large common translation
and small low coordinates; exact zero algebraic inertia; typed admission and array
immutability. No FEModel insertion, static/modal codec edit, rest-mass dynamics
shortcut, public dispatch, coupled solve or broad regression.

If the retained finite kernel's directional derivatives fail, preserve that
finding and propose a targeted correction without editing original source.
Midpoint SO3 stages, time/velocity history, atomic commit/rollback and dynamics
admission remain a later slice requiring their own complete contract and review.

## Execution record

The v1 focused process stopped during collection: unchanged Numba cache decorators
could not obtain a writable locator under the managed worktree. No mechanics
checks ran. Its log/XML/resource and frozen inputs/sources are retained under
`d6_centered_finite_inertia_v1_20260930.*` (2.907092 s, 187.858944 MB, exit 2).
The lead authorized one environment-only v2 replacement with a dedicated writable
`NUMBA_CACHE_DIR`; source, test mechanics and 180 s / 1 GiB caps remain unchanged.

V2 verified the effective managed imports/cache/source hashes, then retained four
passing admission negatives and ten failures at the existing exact-symmetry
section guard. The disposable COM inertia fixture had constructed its rotational
block with floating multiplication before the matrix product, introducing a tiny
asymmetry. No finite work or derivative comparison reached the kernel. The fixture
was corrected by mirroring one upper triangle of the analytically symmetric
rotational block. No source/tolerance/kernel change was made. V2 NONPASS remains
under its unique evidence stem (3.863702 s, 199.041024 MB).

V3 ran only those ten blocked checks: **10 PASS, 4 deselected**, 5.766519 s,
197.337088 MB. The four earlier passing negatives were not replayed; their inputs
fail before the repaired inertia block is admitted, so their evidence remains
applicable. Thus 14 distinct focused checks are covered, not a broad regression.
Velocity directional relative errors at h=`1e-5,2e-6` were
`7.83e-11,6.73e-10`; left configuration errors `1.59e-10,8.31e-10`; acceleration
mass derivative error `2.14e-11`. The original finite derivative algorithm was not
changed and no defect was found in these checks. Rest-M parity is bit-exact.

Nonzero gyro force norm was `0.0563884`, cross-inertia force difference
`0.0417849`, and velocity-derivative nonsymmetry norm `0.291789`; the checks do not
collapse to rest/diagonal/potential mechanics. With common translation
`(2^40,-2^40,2^41)`, moving-origin angular momentum agrees exactly in the reported
high component, and fixed-origin high/low covariance error is `4.92e-21`.
Discarding the valid position/origin low components changes angular momentum by
`6.77e-5`, a nonvacuous control. Rigid-rotation force/mass/momentum relative errors
are below `6.23e-16`. Mixed algebraic inertial rows/columns are exactly zero.

Locally tested development identity:

- Module SHA256 `3334699c5a4c14ef67cbfcef3ad54c3be8c80a15b98f2c34aa6840be70d32f84`.
- Current test SHA256 `a15cf51f0ad38262b4a0fc9c0178c8218898828ab57d64b9089904ff0185485d`.
- Source/test files reside only in the managed D6 worktree named above.
- Complete v3 raw log/XML/resources/frozen inputs and source snapshots use
  `docs/d1_review_support/d6_centered_finite_inertia_v3_20260930.*` in the main
  worktree; v1/v2 failures are retained there separately.

Recommendation: independent review of this finite owner can now precede the next
midpoint contract. This authoring/check result is not D6 acceptance, a public
finite-dynamics capability or a time-step implementation. Existing accepted
native source, rest/modal guards, static codecs and main-package identity remain
unchanged by this worker.
