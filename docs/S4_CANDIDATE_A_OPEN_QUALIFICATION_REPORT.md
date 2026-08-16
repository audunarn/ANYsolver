# Candidate-A open qualification: exact-screen result

## Result

The two registered Candidate-A multiplier spaces both fail an exact necessary
condition.  The aggregate terminal is
`NO_GO_CANDIDATE_A_DISCRETE_PAIR`, and the release terminal remains
`NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`.

This is a proof-only result.  The legacy `ShellElement` remains the production
default.  No improved-S4 selector, production source, public export, assembly
path, serialization path, penalty, stabilization, or `C^T C` term was added.

## A1: `span{r,s}`

The registered A1 moment rows annihilate all eight exact witnesses spanning
the accepted flat `ker(B)`: six rigid modes, the constant-drill gauge, and the
alternating positive-mass `Z` mode.  Exact rational arithmetic establishes

```text
rank(C_A1)       = 2
rank([B; C_A1])  = 16
rank(B T_A1)     = 14
```

The mandatory targets are 18 and 16, respectively.  A1 therefore receives
`PROVEN_FAIL_CANDIDATE_A1_FLAT_RANK`.  This is loss of two published strain
directions under restriction, not a floating-rank or tolerance result.

## A2: `span{1,rs}`

On the frozen, consistently oriented `2x2` Q4 patch, the same nonzero
element-local normalized `rs` multiplier is selected on all four elements.
After clamping the eight boundary nodes, the four contributions at the sole
interior node cancel exactly.  The full unquotiented multiplier space has

```text
mu != 0
||mu||_Lambda^2 = 4
C_admissible^T mu = 0
beta = 0
```

A2 therefore receives `PROVEN_FAIL_CANDIDATE_A2_INF_SUP`.  Removing or
quotienting the multiplier annihilator would define a new candidate and was
not done.

## Reproducibility

The oracle uses only Python's standard library and `fractions.Fraction`.
Symbolic integration and tensor `2x2` Gauss are retained only as exact flat
polynomial-row reproduction; the registered future finite-constraint rules
remain surface `3x3` primary and `4x4` sensitivity.  Finite-rotation,
nonlinear, 80/160/320-digit shard, and performance work was not run because
both necessary screens failed exactly.

Two fresh oracle processes returned byte-identical canonical UTF-8/LF output:

- contract: 4,855 bytes,
  `0DA83A23A62F5DFB1B9FEF7A060D39024EA7A28B1E3A7C91E601A0AC8BC5DE79`;
- output: 2,597 bytes,
  `F450C905C05C5A5E0DD71353BEAB04CC93A89F90CBED3932B2E4D251480D2990`.

The accepted eight-file baseline contains exactly 64 ordered test nodes; its
canonical node-list SHA-256 is
`7D71339F0621328AF54BC4BDFC04E3C7082EDA333B58E100C4C9550F0E9C85D9`.
It passed before implementation (`64 passed in 98.30s`).  The integrated A1
and A2 exact-screen regressions passed together (`6 passed`).

## Content-addressed evidence

- governing plan: `630EEEFD846CCFC4DE5B61C5530F8E76F5ACD33A6014A78135F4A36D8FE90999`;
- baseline manifest: `C3BB5E4AB79C9B6278B6E39F642AE3F99DA001ABF5DE0D1E01274FBC0187199A`;
- offline source registry: `8EF2E09B76046A4070A7A2BCDAC52EC16A25D50C7557F789335AC6173E5A6986`;
- environment manifest: `1348DF6CE0DBC19BE84A0A28243820EAFDD7EA361AB78A5F586EBC98391D28F5`;
- 64-node inventory: `4F016F85EFABFC459823BC3B290F5E2AB2143677AE8765246017D19CC2A4FC11`;
- A1 certificate: `2198458DCDC7EFB4684B5CC59ADAF6E9A0EECF381951CBDD21B286D6DB11097C`;
- A2 certificate: `68691E4F1F23E23ED7DF00C4210436BDD1A730ADB58ED3E755E15CC01ECC5F3B`;
- oracle: `C229C498A2DAC7A6519613A0A2A26398940A769EB98C35D06BDC63216078AB77`.

Candidate B remains the accepted `NO_GO_CANDIDATE_B` packet at
`3A26052DB79CE914FF8A1FCA7835F3B86C15F1D351754B45CA904753D8EFDA0D`.
The rank-four drill-constraint packet remains
`NO_GO_PRODUCTION_RESTRICTION_UNCHANGED` at
`8005C6D285263E33FF7F6D4B5138D5FBE4EFAB6A95834C401F94AF044ACD9E1B`.
Neither was rerun or reinterpreted.

Independent-review acceptance and the final combined focused regression are
separate closeout gates; this report does not claim either before it occurs.
