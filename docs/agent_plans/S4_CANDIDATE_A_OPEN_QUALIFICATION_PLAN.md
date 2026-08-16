# Candidate-A open qualification: exact necessary screens

## Authority

This successor plan is based on local commit
`148ccb45ba79266d48dae1a84c4c500bdc1b4d85` and tree
`0a0809b2111c07098058fd43891729c6f9266b06`.  It supersedes only the
execution order proposed by the user-supplied open-qualification document,
whose raw SHA-256 is
`A27339F96DD798C93E0E3E16C441000C9C0FF57E8DEC454823DD466249DC2B25`.

The accepted MITC4+/D reference mechanics, restricted-release policy,
Candidate-B result, rank-four drill-constraint result, production source, and
public interfaces are immutable in this run.  No external paper is an
execution dependency.  No push, publication, cleanup, activation, selector,
serialization, penalty, stabilization, or `C^T C` operation is authorized.

## Frozen registration

The only candidates are:

- `candidate_a.d4.span_r_s`, with M-orthonormal basis
  `[(sqrt(3)/2) r, (sqrt(3)/2) s]`;
- `candidate_a.d4.span_1_rs`, with M-orthonormal basis
  `[(1/2) 1, (3/2) rs]`.

The exact flat moment rows, node/DOF order, orientation, two 174-row coverage
ledgers, and sign convention are inherited byte-for-byte from the accepted
Candidate-A contract.  Symbolic integration and tensor `2x2` Gauss reproduce
only the flat polynomial rows.  Any future finite constraint retains surface
`3x3` primary and `4x4` sensitivity quadrature.

## Screen A1: exact flat rank failure

Using the accepted facts `rank(B)=16`, `dim ker(B)=8`, and the exact A1 rows,
prove that all six rigid modes, the constant-drill gauge, and the alternating
positive-mass `Z` direction lie in `ker(C_A1)`.  Hence

```text
ker(B) subset ker(C_A1)
rank([B;C_A1]) = 16
rank(B T_A1) = 14, range(T_A1)=ker(C_A1)
```

Exact closure produces `PROVEN_FAIL_CANDIDATE_A1_FLAT_RANK`.

## Screen A2: exact bounded-patch inf-sup failure

Use a consistently oriented `2x2` Q4 patch with discontinuous local A2
multipliers.  Give every element the same nonzero normalized `rs` coefficient
and zero constant coefficient.  The local drill row is
`(+1,-1,+1,-1)/3`.  Clamp all boundary primal coordinates.  The four
contributions at the only interior node cancel exactly; every remaining
column is removed by the support.  Prove

```text
mu != 0
mu^T M_lambda mu > 0
C_admissible^T mu = 0
beta = 0
```

for the full unquotiented multiplier space.  Exact closure produces
`PROVEN_FAIL_CANDIDATE_A2_INF_SUP`.  Removing or quotienting this multiplier
kernel would define a different candidate and needs a new plan.

## Execution and terminal

Primary evidence uses exact integers, rationals, and registered radicals.
Numerical decompositions cannot determine either terminal.  Two fresh oracle
processes must emit byte-identical canonical UTF-8/LF JSON.  An independent
reviewer must accept both certificates before integration.

If both certificates close, the pair terminal is
`NO_GO_CANDIDATE_A_DISCRETE_PAIR` and the overall release terminal is
`NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`.  If either certificate is incomplete,
the pair terminal is `UNCLASSIFIED_CANDIDATE_A_DISCRETE_PAIR` and this run
stops.  Baseline, input, contract, reproducibility, execution, or review
failures are blocking terminals and never scientific results.
