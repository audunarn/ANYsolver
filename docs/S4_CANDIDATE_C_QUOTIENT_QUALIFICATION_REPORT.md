# Candidate C global multiplier-quotient qualification result

## Result

Candidate C receives `NO_GO_CANDIDATE_C_QUOTIENT_INF_SUP`.  Quotienting the
exact dual kernel of the registered A2 constraint removes multiplier
nonuniqueness but does not produce a mesh-uniformly stable mixed pair.  The
overall release terminal remains `NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`.

The result is an exact linear necessary-screen failure.  It does not modify
the A2 primal constraints, add energy, reinterpret gauge, or authorize a
finite-rotation/nonlinear Candidate C.  Legacy `ShellElement` remains the
production default.

## Exact free-family certificate

On the unit square split into `n x n` consistently oriented cells, the free
multiplier transpose is injective.  Candidate C therefore has no exact dual
gauge to remove on this family.  The integer witness

```text
x_i=(i+1)(n-i),  alpha=0,  beta=x tensor x
```

and the exact consistent-mass lower bound give

```text
0 < beta_n_free <= 10/(n^2+2n+2) -> 0.
```

Thus the instability is not caused by retaining a zero multiplier mode.

## Exact clamped-family certificate

For a fully clamped boundary, the complete dual kernel has dimension `2n+1`.
The symmetric zero-mean witness

```text
x_i=(i-(n-1)/2)^2-(n^2-1)/12,
alpha=0,  beta=x tensor x
```

is exactly orthogonal in the physical multiplier mass to that entire kernel.
It is a nonzero minimum-`L2` quotient representative with nonzero transpose
action.  Exact summation and the clamped consistent-mass lower bound give

```text
0 < beta_n_clamped <= 30/((n+1)(n+2)) -> 0.
```

Candidate C therefore retains positive quotient near-kernels whose inf-sup
values decay as `O(n^-2)`.

## Reproducibility

The standard-library oracle uses `fractions.Fraction`; numerical SVD and
floating tolerances are non-authoritative and were not used.  The all-`n`
polynomial identities determine the terminal.  Direct exact assemblies at
selected finite `n` only corroborate the result.

Two fresh processes emitted byte-identical canonical UTF-8/LF output:

- contract: 4,719 bytes,
  `6FC6EACBA183E93C5A0E4CFF2B4EB0E294C22BA9423CC5EA1F55E9094946D70E`;
- output: 3,701 bytes,
  `A44ED2DD5F11A0BBF9A0CB8D01B869A1D7E12632B3E85E773A804FC2CCC140B6`.

The accepted pre-implementation suite contains exactly 75 ordered nodes;
its canonical node-list SHA-256 is
`AA024AA5E14FAE296B854F6E2DDE289DE5978C6B795BE8D2CE58A12B7A170CC4`.
The nine Candidate-C focused regressions passed in 14.84 seconds.  The frozen
75-test baseline plus those nine tests passed together: `84 passed in
117.13s`.

## Preserved boundaries

- Candidate A remains `NO_GO_CANDIDATE_A_DISCRETE_PAIR`.
- Candidate B remains `NO_GO_CANDIDATE_B` and was not rerun.
- The rank-four constraint remains
  `NO_GO_PRODUCTION_RESTRICTION_UNCHANGED` and was not rerun.
- No penalty, stabilization, `C^T C`, selector, production source, public
  export, finite-rotation, nonlinear, precision-shard, performance, push,
  publication, or cleanup action occurred.

A quotient of the flat linear multiplier space is not, by itself, a valid
finite holonomic formulation.  Such a formulation would additionally require
functional redundancy of the nonlinear constraint and its first and second
variations.  That work is unnecessary because the exact linear inf-sup gate
already fails.
