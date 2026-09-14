# G1 exact-elastic admission prerequisite

Status: **BLOCKED_GE_BEAM3_STATIC_AUTHORITY**.
Reason: **EXACT_ELASTIC_EXTENSION_REQUIRED**.

G1 was requested against the static integration contract at
`51ebc3c07dc218ba7a78eb71c49f3f5fde829587`. Its section 4 explicitly requires
stopping if an exact elastic adapter cannot enter the unchanged native kernel.
This is that prerequisite stop, not a failed mechanics test, loss of prior
qualification, or completion of G1. S01-S08 have not been executed.

## Source-backed finding

The companion JSON binds the inspected source files and the frozen contract.
The lightweight tests inspect these sources without importing mechanics.

| Route inspected | Actual admission boundary |
|---|---|
| Current retained generalized operator | Exact `EllipsoidalGeneralizedSection` type required; no section protocol injection |
| Generalized cell conjugate | Same exact-type guard; histories are `GeneralizedCellHistory` with plastic station origins |
| Ellipsoid law | Finite positive yield and hardening; its elastic branch does not make the entire law linear elastic |
| Physical fibre law | At least one real fibre with positive area/modulus and a flow curve; empty background-only construction is rejected |
| Native definition/reconstruction | Only resultant-ellipsoid and physical-fibre families are registered |
| Static reduction | Exact retained generalized operator and generalized history types are required |
| Older retained elastic probe | Uses the directed-hardening section, permits only its virgin elastic interior and rejects distributed loads; not the accepted current-core adapter |

The desired law `s=C e`, `psi=e^T C e/2`, constant tangent C and empty history
has no admitted current-core section identity. A large yield value, infinity,
zero-area dummy fibre, monkey patch, changed class identity, or subtype bypass
would violate either the law or the preserved admission/authority guards.
Nor can the old elastic probe be relabelled as the accepted native workflow.

Therefore no implementation under `src/` was made. All existing runtime,
formulation IDs, defaults, replay schemas and qualification records are intact.
Source-admission checks establish this interface blocker; they are not numerical
qualification or a scientific NO-GO on the beam formulation.

## Proposed narrow successor: G1a exact-elastic extension

This section is a proposal for separate review, **not frozen implementation or
execution authority**. Once accepted, it supplies the missing prerequisite to
resume G1; it does not replace the G1 state/rollback/restart obligations.

1. Add an explicit immutable linear-elastic section identity with a captured
   SPD 6x6 matrix, exact work ordering, constant tangent and genuinely empty
   constitutive history. Adapt isotropic input and the existing external SPD
   section contract by validated snapshots and stable fingerprints.
2. Add a separately identified exact-elastic complementary cell. For retained
   force/moment coordinates p, solve the constrained quadratic station problem
   `min sum(w_j s_j^T C^-1 s_j/2)` subject to the existing cell-force balance,
   with station moments interpolated from p. Factor the constrained system;
   derive its value, gradient and Hessian consistently, without return mapping,
   artificial yield data, material stiffness floors or altered quadrature.
3. Compose an additive native elastic operator from the unchanged reference,
   SO(3), compensated-strain and analytic-derivative primitives. Preserve the
   centered two-cell potential `p.k(q)-Psi*(p)`, 18 external and 24 internal
   variables, physical cell rotations and existing load work. Register a new
   implementation/section identity, not a reclassification of existing objects.
4. Add a narrowly owned elastic element/definition/replay adapter. Reuse the
   shared nodal rotation store and validation protocol; no changes to the old
   ellipsoid/fibre admission branches or historical checkpoint interpretation.
   Avoid a broad refactor of the existing kernel to support duck typing.
5. Before general assembly, verify six isotropic modes, dense SPD coupling,
   primal/complementary energy and derivatives, empty history, frame/reversal
   work, and full 42-variable versus Schur equivalence including internal loads.
   Compare independently constructed equations, not a candidate's own matrices.
6. Then resume S01-S08: two-element shared poses and rolls, rejected trials,
   all-or-nothing prepare/commit, stale-token rejection, exact elastic assembly,
   recovery, authenticated continuation and atomic checkpoint publication.

Before coding G1a, review/freeze its exact additive path extent, identities,
equation map and independent fixtures. Keep the G1 contract unchanged and bind
it as inherited authority. Existing immutable mechanics paths remain unchanged;
if an existing path must change, identify that precise need in the successor
review rather than enlarging scope implicitly.

Retain 600-second children, 24 GiB per process tree, one numerical thread,
three workers maximum, 1800-second waves and no automatic retries. Smoke and
rehearsal precede any frozen two-cycle qualification. This prerequisite audit
requires no heavy run. G2, new selectors, defaults and publication remain out
of scope.

Recommended next step: review and freeze G1a, then implement the exact-elastic
extension and complete G1. Do not advance to constraints/MPC gate G2 yet.
