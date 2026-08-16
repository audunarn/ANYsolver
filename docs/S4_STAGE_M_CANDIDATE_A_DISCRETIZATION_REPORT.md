# S4 Stage-M Candidate-A discretization status

The user-supplied Fox-Simo paper closes the continuous source gate but does not
close the discrete Q4 gate.

## Frozen evidence

- Source PDF SHA-256:
  `A2075C06EB551FB317E09DF37E9BEFB6B525754A945EAC894F58F204CAB2D7D8`.
- Acquired-source record SHA-256:
  `3A70FD3639A763ED5E34E8A0A8530FAF3FB944179EA190DC5660F8062A68EB73`.
- Candidate-A discretization addendum SHA-256:
  `F05C643D28199AF4CB07B7E175F1674C2164ABC6D79F5F772260E94A9A3FD3AB`.
- Preserved Candidate-B output SHA-256:
  `3A26052DB79CE914FF8A1FCA7835F3B86C15F1D351754B45CA904753D8EFDA0D`.
- Candidate-A cases SHA-256:
  `BB29F6AE7AE53E961C992BBC2EA764D50B73F935C9B5F9C21C1E21462DCC3E9C`.
- Candidate-A oracle SHA-256:
  `3240C3C60754B44C06F790F74B553ACF2DF88070E3618082287C0D9DE175992A`.
- Candidate-A contract SHA-256:
  `8861943D1339373FB36448EA376E75D4CBAB64DE1A8450D6B547A235AA62844C`.
- Candidate-A output SHA-256:
  `6904490675315E7F2E17B1AA848837B56FC3E7633B4643B8B6C91989ED8E2059`.
- Candidate-A pytest wrapper SHA-256:
  `E777121E5EA40CE0FC3BE02E9B21AAA1633070903A4027091E5E5B5FE6F8BE87`.

## Result

The continuum scalar constraint, mixed multiplier functional, weak operator,
and tangent are source-substantiated. The exact flat small-rotation constraint
and the two exhaustive D4 rank-two multiplier spaces are now derived and
preregistered without choosing a winner.

The exact cases, independent oracle, contract, and canonical output are now
materialized. Two byte-identical executions covered 80/160/320 decimal digits.
They reproduce the exact flat moment rows and both D4 spaces; all registered
finite positive-polar samples pass objectivity/orthogonality checks, and the
singular blend is rejected without regularization.

The pair test was not run. Two mandatory prerequisites remain unclosed:

1. `lambda=1` is now fixed because unit directors and `t/2` are separate, but
   equality of the source primal potential with the immutable assumed-strain
   MITC4+/D force/work/tangent/mass/section/state/recovery maps is unproved.
2. A proof-only positive-polar `Q_h` is defined and its finite samples pass,
   but global `Q_h=Q_p`, analytic first/second variation closure, and a
   production multiplicative rotation state remain unproved.

Exact current terminals:

```text
continuous source: PASS_CONTINUOUS_CANDIDATE_A_SOURCE
fixed lambda:      UNCLASSIFIED_CANDIDATE_A_FIXED_LAMBDA_SPECIALIZATION
rotation map:      UNCLASSIFIED_CANDIDATE_A_ROTATION_MAPPING
pair catalog:      NOT_RUN_PREREQUISITE_UNCLOSED
Candidate A:       BLOCKED_CANDIDATE_A_DISCRETIZATION_UNREGISTERED
Candidate B:       NO_GO_CANDIDATE_B
overall Stage-M:   BLOCKED_CANDIDATE_A_DISCRETIZATION_UNREGISTERED
```

No Candidate-A pair mechanics, rank outcome, inf-sup claim, selector,
production path, or activation was implemented. All 348 inherited pair rows
are bound but remain `NOT_RUN_PREREQUISITE_UNCLOSED`. No Candidate-B shard was
rerun.

## Verification

- Candidate-A wrapper: 3 passed.
- Candidate-A plus the unchanged Eq21/Eq25, nullspace, drill-constraint,
  geometry-handoff, restricted-activity, restricted-integration, and improved
  qualification gates: 64 passed.
- The two direct oracle executions were byte-identical at 19,267 bytes and
  output SHA-256 `69044906...8E2059`.

## Resume condition

Resume requires an independently accepted, content-addressed derivation that
closes both the fixed-lambda physical pullback and finite `Q_h`/polar mapping,
then freezes the full multiplier assembly and uniform inf-sup contract before
the first pair mechanics run. A missing or ambiguous prerequisite remains
fail-closed; it is not permission to choose a multiplier space from the known
null modes.
