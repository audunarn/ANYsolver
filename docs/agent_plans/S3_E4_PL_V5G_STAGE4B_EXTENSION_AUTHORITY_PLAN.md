# S3 E4-PL V5G Stage 4B extension authority

## Purpose

Authorize only the formulation-native operations needed to construct a V2C
candidate for the bounded modal, buckling, recovery, batch and performance
gate. V5F and its V2B static production candidate remain immutable.

## Source-selected operations

- Mass follows MYSTRAN `TREL1`: each corner receives
  `MASS_PER_UNIT_AREA*AREA/3` on its three translations. Rotations, including
  drilling, have zero inertia and must be projected as algebraic coordinates by
  the solver. No invented rotational mass or legacy TRI3 mass is allowed.
- Geometric stiffness follows MYSTRAN `TMEM1`: form the CST physical-gradient
  stress stiffness from `(Nx, Ny, Nxy)` and copy the same 3x3 nodal block to
  each global translation component. Rotational and PL rows remain zero.
- Recovery follows `TPLT2`, `CALC_PHI_SQ`, and `ELMOUT`: shear resultants use
  the same `phi_squared` multiplier as shear stiffness. Membrane, bending and
  shear fields remain physical; PL fields remain numerical and excluded.
- Serialization and batching may expose these operations only with a successor
  V2C formulation/schema/fingerprint. Hot restart between V2A, V2B, V2C,
  qualified S3 V1, and legacy S3 is forbidden.

The V2C candidate may reuse V2B stiffness code only through a hash-bound port.
It may not import or dispatch to legacy TRI3 or the earlier qualified S3 V1
mechanics. Q4 and both defaults remain unchanged.

## Implementation gate authorized by a pass

Implement and independently reconstruct mass, geometric stiffness, recovery,
serialization round trip and scalar/batch equality. First run local and small
mixed N20 modal/buckling screens. Only after those pass may a separately frozen
Stage 4B campaign run the historical 10%/25% modal, buckling and paired
performance coverage with updated candidate identities.

Every child remains bounded to 600 seconds, one numerical-library thread and
24 GiB; at most three workers may overlap and no consumed attempt is retried.

Terminal precedence:

1. `BLOCKED_E4_PL_S3_V5G_EXTENSION_AUTHORITY_PROCESS_OR_EVIDENCE`;
2. `UNCLASSIFIED_E4_PL_S3_V5G_EXTENSION_SOURCE_GAP`;
3. `PROVISIONAL_GO_E4_PL_S3_V5G_V2C_EXTENSION_IMPLEMENTATION`.

A pass authorizes implementation only. It does not authorize Stage 4B
execution, S3 activation, or any default change. Every result retains
`NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`.
