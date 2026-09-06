# P5 explicit force-accurate assembly development

Parent `ee33b8a47578c8862f1ccbcfa5787e16b035d42e`, tree
`6406d0ad8f0410f884259ac4f58bfc82b7f32fd6`.
Scope is four research/test paths: new assembly module, its tests, this
contract, and explicit recognition of the successor class in the existing
research displacement controller. No production path is edited.

## Numerical policy fixed before assembly testing

The successor class `ForceAccurateAssemblyHistoryProbe` uses the existing
local force-accuracy option. The original `NonlinearAssemblyHistoryProbe`
source, constructors, mechanics, global solve, transactions and default
behavior remain unchanged. The new class inherits their implementation and
overrides only local evaluation, response metadata checks and accepted
element reconstruction. Displacement control explicitly permits these two
exact classes, not arbitrary subclasses or duck-typed assemblies.

Freeze the total absolute force-equivalent estimated-error budget at 1e-12,
one tenth of the unchanged 1e-11 global equilibrium limit. Allocate exactly
1e-12/N to each of N elements. Scale moments by the original assembly
diameter and use force normalization one. The existing global normalization
is at least one, so this allocation is conservative with respect to that
normalization. There is no case-specific or runtime budget tuning knob.

For each element, use the local first-order stationary-force estimate from
the parent contract. Each scattering map inserts distinct local nodal DOFs;
therefore the norm of the sum of scattered estimates is no greater than
the sum of their norms. Restriction to free DOFs cannot increase that norm.
Check every per-element limit and the accurately summed aggregate limit.
This reasoning bounds the **assembled estimate**, not residual rounding
error or the unknown nonlinear remainder. It is not a qualification proof.

All local and global iteration/evaluation/backtrack budgets remain in force.
Every mixed evaluation still consumes the shared budget. Computing the
scalar error metadata uses the already evaluated successful local iterate,
not an extra mechanics evaluation. No residual is corrected, clipped or
substituted, and no physical section resultant is replaced by an estimate.

## Evidence and transaction identity

Only successor element responses add three fields: accuracy schema
`GE_BEAM3_P5_ASSEMBLY_LOCAL_FORCE_ACCURACY_V1`, the exact `LocalForceAccuracy`
policy and the estimated force error. Their dataclass fields participate in
the existing canonical trial digest. Historical responses keep their old
class and fields, hence their byte-bound fixtures remain meaningful.

Before commit/replay, reconstruct each element from its accepted nodal and
internal coordinates and its accepted material origins. Recompute its full
mixed derivatives, stationary-block checks, Schur tangent and error estimate.
Reject a policy/schema mismatch, absent metadata, excess estimate or digest
mismatch before whole-model publication. Do not trust cached matrices or a
rehashed scalar claim. Failure on the last element cannot commit earlier
element histories. Discard and failed solves leave the checkpoint intact.

The successor rejects an injected historical lower-accuracy checkpoint when
the displacement controller validates accepted replay. This is in-memory
research transaction safety only. No serialized assembly restart codec is
introduced; full restart, loading untrusted serialized state and production
restart compatibility remain separate requirements.

## Small test extent and next execution boundary

Use two-element coupled directed-plastic cantilever loading, unloading and
discard, plus the existing two-element arch targets 0.1 and 0.095. Check
physical interface action/reaction, global force/moment balance, estimator
recomputation, triangle-inequality allocation, deterministic trial bytes,
late-element failure, changed/rehashed policy/estimate and cross-instance
ownership. Retain all historical default-byte and source-identity checks.

No 32-element equilibrium, onset grid, bisection or continuum solve is run
here. Initial development tests exposed a NumPy scalar at the strict policy
boundary; explicitly converting the existing assembly length to a Python
float corrected that interface mismatch without changing its value.

Final focused regression before this freeze: **147 tests passed in 37.21
seconds**, including the 14 new successor-assembly tests and unchanged
historical source-identity and byte-bound small fixtures. `git diff --check`
passed. The original assembly source and all production files have no delta
in this step. This is author development validation, not independent review.

Any later resource comparison must use a new frozen runner, schema and
unique request, retaining the prior observation and failure packets. The
old two-state worker must not be reused: its authority and raw response
schema bind the historical assembly. The question remains whether improved
local stationarity resolves control32 stagnation; a failure must be preserved
without tolerance relaxation or automatic retry.

The pending administrator notification still requires the previously
requested communication permission. No ledger or external evidence is
modified by this implementation. No qualification, integration, default
activation, publication, or broad state/material/dynamics claim follows.
NO_GO_PRODUCTION_RESTRICTION_UNCHANGED.
