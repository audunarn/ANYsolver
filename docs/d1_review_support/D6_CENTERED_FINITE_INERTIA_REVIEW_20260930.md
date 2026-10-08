# D6 centered finite-inertia independent review — 30 September 2026

## Disposition

Scoped local development PASS for the separate centered finite-inertia owner and its retained focused checks. Source/evidence scrutiny found no consequential cache-ownership, finite-work-map, ordering, algebraic-zero, momentum-origin or nonzero-velocity derivative blocker in this slice. This is a pure inertial response owner. It does not implement or accept a time step, midpoint update, dynamics transaction, FEModel integration or public finite-dynamics admission. D6 acceptance and release remain open.

The reviewer read source and saved evidence, compared hashes and inspected retained test properties. No test, numerical run, solver, source edit or old evidence replay was executed. This new review note is the only D6 write. Source/test ownership remains in the managed worktree; the main package was not changed by this review.

## Source boundary and cache ownership

The reviewed module is `C:/Users/AudunArnesenNyhus/.codex/worktrees/general-contact-native-dynamics/ANYsolver/src/anysolver/_ge_beam3_centered_finite_inertia.py`, SHA256 `3334699c5a4c14ef67cbfcef3ad54c3be8c80a15b98f2c34aa6840be70d32f84`. Its test is `tests/test_ge_beam3_centered_finite_inertia.py` in that same worktree, SHA256 `a15cf51f0ad38262b4a0fc9c0178c8218898828ab57d64b9089904ff0185485d`.

`_CenteredFiniteKernel` (module line 22) creates a fresh `_CenteredRestInertia` solely to obtain its validated section inertia and station tuple. The section matrix, station frames and offsets are owned read-only copies. Each cache is local to a new kernel for that evaluation, with no persistent shared mutable cache or caller-array alias. The temporary rest object is not evaluated with finite speed; its unchanged rest-only guard is not disabled. The new finite subclass inherits `LiftedInertia.evaluate` directly.

The exact centered-reference restriction and exact integer order `(4,8,24)` come from the unchanged centered cache constructor. Section validation, positive finite measures, compensated normalized position/origin pairs, finite 24-vectors and proper cell rotations retain their existing validators. The four reused source files—finite inertia, centered mass, centered positions and coordinate recovery—match both their frozen hashes and the main development checkout. The only definition/reference to the new finite entry point in managed `src/anysolver` is the new module itself; no public dispatch integration is introduced.

## Finite work and coordinate semantics

The retained station map is `Q=U R0`, `d=U d0`, translational velocity `(1-t)vleft+t vright+omega cross d`, and angular velocity `omega`. Section-frame six-velocity is contracted with the same physical symmetric positive section inertia. Generalized momentum is the station-map transpose contraction, mass is its Gram matrix, and inertia includes the original centrifugal and momentum-cross terms. Positions enter the inherited algorithm only in its temporary physical angular-momentum recovery; energy, mass, force and force derivatives remain its original results.

The new response replaces only physical linear/angular momentum with compensated recovery. The original derivatives use spatial velocity and acceleration held fixed under left increments `Unew=Exp(eta) U`; they are force derivatives, not a symmetric potential Hessian. The new owner introduces no symmetry assumption or rest-mass substitution. The inherited original finite source SHA256 is `4274095b7a010a707aff68ede94c342f3b4504395dc0b3c9fc5bad075e269dfa`.

Convenience properties retain the original 24-dimensional physical arrays. `_mixed` (module line 125) copies that leading block into the declared nodal18/cellspin6/resultants18 ordering of dimension 42. Nodal rotation traces `(3:6,9:12,15:18)` are already zero in the finite velocity map; all 18 resultant entries added at `24:42` are exactly zero. The same extension applies to mass, momentum, inertia and both derivatives. Physical coordinate count is 15, not 24 or 42. No mass floor, static condensation or algebraic kinetic contribution is added. Returned arrays follow the existing owned read-only array convention.

## Compensated momentum and origin

`_momentum_pairs` (module line 85) reconstructs station momentum with the same represented `B`, `Q` and section matrix as the inherited finite owner. The lever uses the existing compensated station position and the full high/low origin. Fraction products/sums accumulate represented binary-float station momenta, measures and compensated lever components before the final high/low rounding. Thus `P=sum measure Qp` and `H_O=sum measure[(xstation-O) cross Qp+Qh]` preserve the stated origin dependence. This compensates recovery; it does not make section-law or reference geometry arithmetic exact.

The temporary inherited recovery receives relative full-pair coordinates, while the final returned momentum uses the compensated path. A common large translation together with a translated origin should preserve angular momentum; a fixed origin should add translation cross linear momentum. Retained evidence exercises both. Dropping legitimate lows is a nonvacuous negative control. There is no general arbitrary-magnitude or arbitrary-precision claim.

## Evidence reconciliation

All six frozen source/test hashes match current files, and the executed module/test snapshots match the identities above. The effective-process entry verifies the managed import paths, source hashes, single-thread environment and dedicated writable `NUMBA_CACHE_DIR` before running tests. V3 XML records 10 tests, zero failures/errors; resource status is completed, exit 0, 5.7665189 s / 197.337088 MB under 180 s / 1,073,741,824 bytes. Pytest reports 10 passed / 4 deselected in 2.33 s.

| Retained nonzero-mechanics quantity | Result | Check limit |
|---|---:|---:|
| Velocity directional relative error, steps 1e-5 / 2e-6 | 7.829e-11 / 6.726e-10 | 1e-5 |
| Left-configuration directional relative error, same steps | 1.591e-10 / 8.311e-10 | 1e-5 |
| Acceleration directional mass relative error, step 3e-6 | 2.143e-11 | 1e-7 |
| Rigid-rotation force/mass/momentum maximum relative error | 6.230e-16 | 2e-13 |
| Fixed-origin compensated translation covariance error | 4.922e-21 | 1e-12 |

Finite kinetic energy is 0.1697912439; gyro force norm is 0.0563884207, removal of section cross inertia changes force by 0.0417848633, and velocity-derivative nonsymmetry norm is 0.2917889646. These observations demonstrate that the derivative checks reach nonzero-spin, cross-inertia mechanics rather than only rest. The common translation `(2^40,-2^40,2^41)` gives zero reported moving-origin high-component discrepancy, while discarding valid lows produces angular-momentum error 6.770e-5. Exact rest mass parity, exact mixed algebraic zeros, algebraic-speed irrelevance and returned-array read-only checks also pass.

V1 collection NONPASS and V2 ten mechanics failures remain retained. V1 did not reach mechanics because of the Numba cache locator. V2's ten failures stopped at the exact section-symmetry guard; four typed-order/invalid-pair admission negatives passed. The only V2-to-V3 test-source difference mirrors the disposable analytically symmetric COM rotational inertia block before contraction. Negative test bodies and production source are unchanged. Therefore the retained four V2 negatives and ten V3 mechanics checks have distinct, honest scopes; no failed mechanical derivative was erased or tolerance relaxed.

- V3 frozen inputs: `733540aae7b9144b5af8d872eb74f55a89336a4bd134d4fa99f07911f0cf158a`.
- V3 XML: `fd642e9bc69767fc97cf2501083ca0e54b74fb18063b9bc75b78186be39bdfa5`.
- V3 resource JSON: `d48541c4f70b96c2910ab58602d76f258a2469097eba54a0e60e338aa82aa7a8`.
- V3 log: `1fba1cbe2158ce83214304d59771a5c5a68861746dc915e59c04ca3af580fcd5`.

The prospective finite-owner contract and raw inputs correctly retain `accepted=false` and `released=false`. A subsequent midpoint/time-history slice must separately define and verify stage mapping, finite-work use, state ownership and atomic commit/rollback. This review neither changes existing public rest/modal restrictions nor supplies those later obligations.
