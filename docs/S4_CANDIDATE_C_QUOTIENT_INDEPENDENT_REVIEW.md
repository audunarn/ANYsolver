# Independent review: Candidate C multiplier quotient

## Verdict

`ACCEPT` with no P0 or P1 findings.

Candidate C fails the exact flat-linear necessary screen and receives
`NO_GO_CANDIDATE_C_QUOTIENT_INF_SUP`.  The overall release terminal remains
`NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`.  This review does not authorize a
finite-rotation, nonlinear, or production formulation.

## Authority and identities

The review is based on commit
`2cb8c53cd1097380c872ba2802ec0eacc5198304`, tree
`f95d74e3ed1bb760f622e188f75f62a8b7ae43f6`.  The reviewed Candidate-C
artifacts are:

| Artifact | Bytes | Raw SHA-256 |
| --- | ---: | --- |
| Governing plan | 4,044 | `82762B0FAD7CC200B76C6262D3B2DFEDAA0E2261FD5E7DF1195F8BAEA85D8901` |
| Derivation | 3,962 | `447AB70BE8D34A08FFAAE98C6FA5583A15DE7C384789AA8C31838A5B7FFB6ACE` |
| Cases | 1,858 | `B41360811714ED7A52B40F6ED282EA9F89C91A6FD0FE818F7A0AA51CA9A84936` |
| Test inventory | 10,598 | `2A79F6E5F1683BC6D2F8FD049DFDBA9FF0457EDE486F1F9B0ACA8CEFCC5AA592` |
| Exact oracle | 25,728 | `4476B913393DB536CB374D8E458DC29250FF535A4C5AB340F6014C93F6323F16` |
| Contract | 4,719 | `6FC6EACBA183E93C5A0E4CFF2B4EB0E294C22BA9423CC5EA1F55E9094946D70E` |
| Canonical output | 3,701 | `A44ED2DD5F11A0BBF9A0CB8D01B869A1D7E12632B3E85E773A804FC2CCC140B6` |
| Qualification report | 3,323 | `51F7E5BA22C13EE0EA0642C83EA8DEBBB5888CE8517AB677572D1FB79131179E` |
| Exact mechanics test | 8,451 | `5B55C7318CDBBD12BFA176E70644E2EACE5CDD5AB42DAF5B63A1D63E021BCE43` |
| Qualification wrapper | 7,193 | `CE56C0D19A355AADEFCF98EF17BA5DA540FE4B6DF0C285E7461B120047932E56` |

The contract also binds the accepted Candidate-A A1 and A2 certificates,
Candidate-A output and independent review, Candidate-B output, and rank-four
constraint output.  Their existing terminals are preserved without rerun or
reinterpretation.

## Independent mechanics audit

Candidate C retains the registered A2 basis
`[(1/2) 1, (3/2) rs]` and changes only the representation of exact multiplier
redundancy.  The quotient does not delete a raw primal row and leaves
`ker(C)` and `range(C^T)` unchanged.

The corrected constant-mode transpose uses

```text
u:     +(a/2)(E tensor H) alpha
v:     -(a/2)(H tensor E) alpha
psi:     a^2 (H tensor H) alpha.
```

The negative `v` sign agrees with the frozen constraint
`u_,s - v_,r + 2 psi`.  At `a=1`, the oracle and an independent exact test
compare all 24 columns of the resulting local constant row with the accepted
A2 `normalized_1_full` row.  The normalized `rs` drill row remains
`(a^2/3)[+1,-1,+1,-1]`.

For the free `n x n` family, the signed incidence and unsigned sum maps have
full column rank, so the multiplier transpose is injective.  With
`x_i=(i+1)(n-i)` and `beta=x tensor x`, exact sums and the consistent-mass
bound give

```text
0 < beta_n_free <= 10/(n^2+2n+2) -> 0.
```

For the fully clamped family, the complete dual kernel has dimension
`2n+1`.  The centered-quadratic tensor witness is orthogonal in the physical
multiplier metric to that complete kernel, has nonzero transpose action, and
gives

```text
0 < beta_n_clamped <= 30/((n+1)(n+2)) -> 0.
```

Both are positive quotient near-kernels, not retained exact gauges.  Either
all-`n` rational bound is sufficient to disprove a mesh-independent positive
inf-sup constant.  Numerical SVD, fitted rates, floating tolerances, interval
arithmetic, and high-precision shards do not determine the terminal.

The quotient is established only for the flat linear bilinear form.  A
finite holonomic functional would additionally require every quotient
direction `k` to satisfy `k^T g(q)=0` identically, including the corresponding
first- and second-variation identities.  No such nonlinear claim is made.

## Reproducibility, tests, and scope

The standard-library `fractions.Fraction` oracle is fail-closed and emitted
byte-identical canonical UTF-8/LF output in two fresh processes.  The accepted
execution records `9 passed in 14.84s` for the focused Candidate-C tests and
`84 passed in 117.13s` for the frozen 75-test baseline plus those nine tests.
This reviewer separately reproduced the focused result as `9 passed in
15.25s`.

The allowed tracked extent is `.gitattributes` plus the Candidate-C plan,
derivation, cases, inventory, oracle, contract, output, report, tests, and
this independent review.  No production, package, workflow, selector,
serialization, dispatch, or public-export path is included.

No penalty, stabilization, `C^T C`, inferred coefficient, finite-rotation or
nonlinear execution, precision shard, interval run, performance work,
production activation, Candidate-A/B rerun, push, publication, cleanup, or
removal of preserved evidence is authorized or claimed.  Legacy
`ShellElement` remains the production default.
