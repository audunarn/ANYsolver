# Qualified Q4 state-seal guard V2 incident and authority

## Frozen base and incident

- Base commit: `62464bea649229aa2c9f89ba7cbe431bf6a9282a`
- Base tree: `c5cc24fa60a3ce1cdc3a1910bd45fe0efe7ec620`
- Branch: `codex/s3-q4-state-seal-guard-v2`
- Incident class: `REFERENCE_GUARD_COHORT_IDENTITY_DEFECT`

The production vector return map has used cohort-wide convergence since commit
`a51340eb5ccde816593a6d5cbbe90d6066fff464`. Rows that have already met their
scaled residual condition continue to receive Newton updates until every row in
the cohort has converged. A fixed cohort is deterministic, but replaying one
accepted row through the scalar kernel can therefore differ in the last binary64
bits of `plastic_strain` and `alpha`.

Commit `16cfc012d70ccda688079b1ad9f88659348b67b7` added an exact scalar replay guard
for accepted qualified-Q4 states. It correctly proves scalar-produced states,
but incorrectly applied the same cross-cohort equality requirement to vector
states. The four reproduced ANYfem nonlinear/fracture cases retained exact layer
strain while their accepted vector plastic histories differed from scalar replay:

- ordinary nonlinear case: 41 plastic-strain components, maximum absolute
  difference `5.071724290539592e-14`;
- fracture case: 3 plastic-strain components, maximum absolute difference
  `2.7200464103316335e-15`;
- bounded two-row witness: 21 plastic-strain and 6 alpha components, with maxima
  `4.336808689942018e-19` and `8.673617379884035e-19` respectively.

No mechanics contradiction was observed. The rejected invariant was the guard's
assumption that a vector-cohort update must be bitwise identical to a later
one-row scalar replay.

## Authorized correction

The V2 origin closes each accepted update with a registered producer identity and
an exact binary64 SHA-256 over the parent plastic history and accepted
`plastic_strain`, `alpha`, and `layer_strain`. Packed trial/commit/discard storage
carries that producer and digest atomically with the constitutive core.

- Scalar and exact-replayed V1-migration producers retain exact scalar replay of
  all three core fields.
- The vector producer retains exact scalar replay of `layer_strain`; its
  cohort-dependent plastic and alpha fields are instead verified by the exact
  producer/core digest and the outer committed-state binding.
- Existing V1 states and element descriptors are accepted only through the
  closed V1 schema. A V1 state is upgraded only after its original exact scalar
  replay succeeds.
- No tolerance, ULP allowance, approximate equality, or mechanics fallback is
  introduced.

Authorized edits are limited to Q4 state guards and serialization, nonlinear
state lifecycle plumbing, the two vector producer call sites, focused tests, and
this record. `plasticity.py`, `vectorized_nonlinear.py`, Q4 forces, tangents,
recovery, coefficients, tolerances, and physical state laws remain unchanged.

## Required regression evidence

The correction must pass the four reproduced ANYfem cases; producer/core hash
mutation; packed-state partial commit, discard, and deletion; scalar exact replay;
V1 state and element migration; current restart/lifecycle suites; and the existing
Q4 numerical/current-tangent tests. Repository diffs must confirm no change to
the frozen mechanics files named above.
