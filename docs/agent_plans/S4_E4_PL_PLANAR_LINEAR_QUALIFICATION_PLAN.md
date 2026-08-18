# E4-PL-Q1A planar identity and local-algebra qualification

## Authority and purpose

This bounded successor starts from commit
`97c3150c9ecd41cf42fc108e9ff476497154428c`, tree
`9ea7e81a17c246e41b3fdfc236200d9dbf3e2b60`. It preserves the accepted E4
packet byte-for-byte and binds the user-supplied design input
`S4_E4_PL_PLANAR_LINEAR_QUALIFICATION_PLAN_MAIN_97C3150.md`, 26,423 bytes,
SHA-256 `91CFD5305896AE4DAA5875BB55B70B3EE9D140F8E14165DBFD5904E6BA6D43BD`,
as background rather than executable authority.

The registered research identity is
`candidate_e4_pl_q1.wg2020_n7_k0_surface_pl_planar_linear_iso_v1`, with status
`DORMANT_UNQUALIFIED`. Q1A decides only whether its non-affine planar identity,
local algebra, covariance, recovery boundary, and DNV-compatible material
interface close. It does not qualify assembled stability, locking, production,
or a general shell element.

## Frozen formulation

- WG2020/WG2004 Hu-Washizu core: `n=7`, `k=0`, source MITC shear, 35 local
  variables, and positive unshifted 2x2 surface quadrature.
- External node-major coordinates are
  `[u1,u2,u3,theta1,theta2,theta3]`; `T5` injects the 20 physical coordinates
  and `QD` injects the four drilling coordinates.
- The PL field has basis `[1,r,s]`, `gamma_PL=G`, and the faulty equal-order
  `r*s` mode is excluded only through the uniquely closed non-affine source
  construction.
- The residual-mode coefficient is `epsilon_hg=1e-3`; no coefficient may be
  tuned or selected from outcomes.
- Thickness is `t`; mesh size is `h_e`. Physical loads are in `range(T5)`.
  Direct drilling moments and nonzero prescribed drill rotations are excluded.
- Physical WG resultants/recovery, projected total reactions, and projected
  PL/hourglass reactions are separate records.

All reference code remains under `docs/reference_cases`. Nothing under `src`,
the package configuration, API, selector, serialization, dispatch, workflow,
or production tests may change.

## Preregistered Q1A gates

1. Verify the exact main authority, accepted E4 hashes, 20-node detached E4
   suite, six preserved evidence roots, attachment, sources, and ANYmaterial
   identity.
2. Close exactly one non-affine planar construction for the WG skew maps, MITC
   shear map, multiplier transformation, centre-linear drill projection,
   `C_e`, `B_e`, `M_e`, and geometry-dependent residual row. More than one
   source-consistent construction blocks before mechanics.
3. Reproduce the accepted affine E4-0 certificate and assemble the actual
   source-ordered 35+3 stationary system. Generic Gram or identity witnesses
   and post-condensation rank repair are forbidden.
4. For `L_e(p,d)=A_e p+R_e d`, prove `R_e` nonsingular, `K_dd` SPD, and
   `K_pp-K_pd K_dd^-1 K_dp=K5`. Prove mixed/condensed energy, work, residual,
   tangent, load, and recovery parity; PSD rank 18; and exactly six element
   rigid modes.
5. Prove all D4, orientation-reversal, rational frame, origin, and unit actions
   on the two exact affine controls and two frozen rational non-affine probes.
   General membrane patches prescribe drill equal to continuum spin.
6. Validate all 17 existing RP-C208-backed S235/S275/S355/S420/S460 fixtures
   with zero new public fields. Density remains required metadata but is unused.
   Report only compatibility with DNV analysis workflows, never DNV approval.
7. Run the caller-bound independent oracle twice in fresh processes and require
   byte-identical strict canonical UTF-8/LF JSON, followed by independent review.

## Evidence and execution boundary

The first local commit freezes every input, threshold, case, implementation,
oracle, contract, and scientific test before an outcome is emitted. The second
local commit may add only outputs, reports, reviews, status, closeout evidence,
and the conditional Q1B plan. No push, merge, publication, or cleanup is
authorized.

The accepted E4 20-test suite runs only in a detached worktree at its immutable
authority because its historical closeout test intentionally rejects successor
paths. The live successor uses new hash-verification and Q1A tests.

## Terminals

Precedence is:

1. `BLOCKED_E4_PL_Q1A_BASELINE_MISMATCH`
2. `BLOCKED_E4_PL_Q1A_PLAN_AUTHORITY`
3. `BLOCKED_E4_PL_Q1A_SOURCE_OR_PLANAR_IDENTITY`
4. `BLOCKED_E4_PL_Q1A_CONTRACT_OR_NONDETERMINISM`
5. `BLOCKED_E4_PL_Q1A_ORACLE_OR_REVIEW`
6. `NO_GO_E4_PL_Q1A_LOCAL_ALGEBRA`
7. `NO_GO_E4_PL_Q1A_PATCH_OR_COVARIANCE`
8. `NO_GO_E4_PL_Q1A_DNV_MATERIAL_OR_RECOVERY_CONTRACT`
9. `UNCLASSIFIED_E4_PL_Q1A_PLANAR_IDENTITY_AND_LOCAL_ALGEBRA`
10. `PROVISIONAL_GO_E4_PL_Q1B_NONINTRUSION_STABILITY_LOCKING_PLAN`

A Q1A pass authorizes only a separately frozen Q1B theorem and numerical
campaign. Every outcome retains `NO_GO_PRODUCTION_RESTRICTION_UNCHANGED` and
legacy `ShellElement` as the production default.
