# P5 compensated-coordinate local evaluator

Parent `466c851097142a578d4c7194feb0b97dc963381b`, tree
`edaad837ff7638c41f8e912432fc94798bfe6de7`.
Four added research paths: this plan, compensated_coordinates,
compensated_mixed, and the compensated_mixed tests. All existing modules,
failed evidence, defaults and production mechanics remain unchanged.

## Evidence-driven purpose

The independent saved-force audit found that exact scatter and a 90-digit
elastic metric reconstruction leave the represented-state residual above
1e-11. A summation-only repair is insufficient. The current controller adds
small Newton increments to absolute binary64 positions, potentially discarding
them before any local force calculation. This prototype preserves an extra
numerical coordinate part through the native mixed potential. It does not yet
change an assembled controller or claim convergence of the failed arch.

## Representation and analytic variations

A position is represented by a normalized finite `(high, low)` pair. Advance
the pair using a rounded accurate sum and the rounded residual of the original
terms. This is a finite two-part expansion, not arbitrary-precision or universally
exact arithmetic. Overflow and nonfinite or unnormalized pairs fail closed.
The low part is numerical state, not an extra physical degree of freedom.

The explicitly instantiated CompensatedMixedBeamProbe requires a copied,
immutable three-node low-part array. Each local solve sees the same low parts
and fixed station origins. It inherits the unchanged material law, quadrature,
local Newton limits, force-accuracy estimator and Schur condensation.

Evaluate the exact identity

`z = (U^T-I)d0 + U^T(d-d0)`

with both expansion components retained in the reference chord and displacement
chord. Form the displacement chord directly from original coordinate high/low
parts and external increments, before any absolute-coordinate rounding.
The linear coordinate map has exact unit nodal derivatives and zero second
derivatives. Attach those derivatives to its high jet and a constant low jet;
multiply both through the rotation jets. Thus low parts participate in the
rotational first and second variations rather than being added to the final
residual as a correction.

Stable scalar summation of Jet2 terms retains the analytic sum of their
gradients and Hessians. Energy, residual and Hessian come from the same mixed
potential. No finite differentiation, empirical stabilization, force clipping,
coefficient change or new tolerance is introduced. Distributed dead-load work
also retains high/low positions and increment terms. Physical station recovery
uses the resulting native strains and fixed material origins.

This class is opt-in research only, with identity
`GE_BEAM3_P5_COMPENSATED_MIXED_EVALUATION_V1`; coordinate identity
`GE_BEAM3_P5_COMPENSATED_COORDINATES_V1`. It supplies no production selector,
global state schema, commit protocol, serialized restart or qualification.

## Local acceptance checks

- Compare short sums with exact Fractions, retain/cancel sub-ulp increments,
  and reject invalid, unnormalized, nonfinite and overflowing inputs.
- A straight end displacement of 2^-60, lost by ordinary addition to coordinate
  1, must produce the analytical native axial force 1000*2^-60, energy
  500*(2^-60)^2, physical section resultants and distributed-load work.
- Compare full potential/residual/Hessian with the historical expression on
  straight/curved, coupled elastic/plastic and dead-line-load cases.
- Check condensed energy/residual/tangent directional agreement at the unchanged
  1e-7 limit and conservative symmetry at 1e-11.
- Check arbitrary common rigid motion, connectivity reversal, transformed
  material origins and recovered resultants at the existing 1e-11 limits.
- Reconstruct a solved local state in a fresh instance at the same accepted
  local coordinates/origins and require exact response equality. Dropping a
  nonzero low part must alter the response rather than silently replay.
- Preserve constructor input isolation, copied low-part exports and the old
  local evaluation-budget failure behavior.

These checks are small scalar/one-element tests, not another 32-element run.
The local replay check does not establish globally accepted material history.

## Next required integration

An assembled successor must carry and hash-bind low parts in trial, committed,
failure and restart records; normalize them on each nodal correction; enforce
zero low parts at prescribed exact clamps/targets; and use the same data during
evaluation, recovery and accepted-origin replay. Missing/foreign coordinate
schemas must fail closed. No retroactive reconstruction of missing low parts
in preserved failures is allowed.

Test small assembled loading/unloading, true failure rollback, deterministic
serialization and rehashed mutation rejection before freezing a new bounded
two-state comparison. Retain 1e-11 global equilibrium, 1e-12 total estimated
local-force budget, all iteration limits and the resource-manager protocol.
No larger onset wave, publication or activation follows from this local gate.
Broad GE-B3 dynamics, material parity, restart and beam-shell joint requirements
remain open. `NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`.

## Development result

The six-file focused regression passed: 88 tests in 9.67 seconds, including
26 compensated-coordinate tests. The first expanded run found a test-harness
type error (passing a tuple to the existing dataclass-only digest helper);
hashing each station dataclass corrected that harness error. No mechanics or
acceptance tolerance was altered to resolve it. `git diff --check` passed.
No heavy resource request, 32-element solve or qualification wave was run.
