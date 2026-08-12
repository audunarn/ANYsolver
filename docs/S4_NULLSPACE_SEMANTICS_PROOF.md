# S4 nullspace-semantics proof

## Status and scope

This document reports proof-only algebra for the corrected literal MITC4+/D
element at quarantined commit
`f5cf8d925f47c816f5fe4857a83c5e38fd599570`. It does not select or apply a
gauge, constraint, stabilization, penalty, hourglass term, energetic
formulation, production coupling, or rank policy. It does not activate or
integrate the quarantined formulation.

The governing registrations are:

- proof plan SHA-256
  `855D76F0CA40549CBAEAD8360152F973B3162671295C53B16F58A5341CC382CA`;
- Vidar editor plan SHA-256
  `136CD18281F61D2705FD3C1145C95C63498BE8B255C1D0F8118701D3E33FF3A6`;
- Heimdall auditor plan SHA-256
  `6AB98DDB6F50139544610C2058D8FFB0C833749F25F126D404C8F18B76811530`.

All element maps come from four hash-checked numerical modules loaded through
an isolated synthetic package. The real `anysolver` initializer, shared
assembly, geometry/document APIs, sibling repositories, handoff commit
`931ed769`, and native-hybrid integration are outside this proof.

## Exact algebraic derivation

This section states algebraic definitions, not a production policy.

### Registered metric and operators

For element or retained topology diameter `ell`, the dimensionless DOFs are

```text
q_phys = S_q q_hat,
S_q = blockdiag(ell,ell,ell,1,1,1) per declared global node.
```

Using only positive quadrature, density, and retained activity weights,

```text
B_w = vertical_stack_a sqrt(alpha_a w_a/W_B) B_a S_q,
H_w = vertical_stack_a sqrt(rho_a beta_a w_a/W_H) H_a S_q / ell.
```

Consequently `ker(H_w)=ker(M)` for the quadrature-consistent physical mass
Gram matrix. The oracle independently corroborates
`B_w.T B_w` against the scaled identity-constitutive stiffness and
`H_w.T H_w` against the scaled consistent mass.

### Gauge and positive-mass quotient

The strain nullspace, zero-mass gauge, and registered-metric quotient
representative are exactly

```text
N_B = ker(B_w),
G = N_B intersect ker(H_w),
Pi_P = Pi_N_B - Pi_G.
```

`P` is the orthogonal representative of `N_B/G`. It is not itself a
non-rigid-mechanism label.

### Rigid quotient image

Let `R` be the analytic component-wise rigid candidate space in the same
dimensionless metric. Every represented-subspace intersection is computed
symmetrically: for projector-derived orthonormal bases `Q_U,Q_V`, form
`[Q_U,-Q_V]`, rank-reveal that O(1)-scaled augmented matrix, and require the
two mapped intersection projectors to agree.

The rigid strain-null space and its gauge overlap are

```text
R_N = R intersect N_B,
R_G = R_N intersect G.
```

The rigid image in the quotient representative is then

```text
Y_R = Pi_P Q_R_N,
Pi_RQ = projector(range(Y_R)),
Pi_Z = Pi_P - Pi_RQ.
```

At every SVD sensitivity multiplier the oracle requires

```text
rank(Y_R) = dim(R_N) - dim(R_G).
```

This quotient image is essential. Raw `R intersect P` is mathematically
wrong when a rigid strain-null vector has a gauge component: its quotient
representative need not remain in `R`.

### Constrained tangent semantics

For affine rows `C_phys q_phys=d_phys`, each nonzero transformed row and its
matching RHS are divided by the row norm. The RHS affects only affine
feasibility; the homogeneous tangent uses `C_hat`:

```text
N_C = ker([B_w;C_hat]),
G_C = N_C intersect ker(H_w),
Pi_P_C = Pi_N_C - Pi_G_C.
```

Constraint-compatible rigid quotient representatives may differ from raw
rigid vectors by gauge. Therefore the constrained construction is

```text
S_RG = R_N + G,
L_C = N_C intersect S_RG,
L_G_C = L_C intersect G_C,
Y_R_C = Pi_P_C Q_L_C,
Pi_RQ_C = projector(range(Y_R_C)),
Pi_Z_C = Pi_P_C - Pi_RQ_C,
rank(Y_R_C) = dim(L_C) - dim(L_G_C).
```

This does not conflate free element rank, assembled rank, homogeneous
constrained rank, affine feasibility, or any later reduced operator.

## Frozen numerical decision rules

All scientific arrays and operations use finite IEEE-754 binary64. Ordinary
rank decisions use

```text
tau(A) = 64 max(m,n) eps64 sigma_max(A),
rank(A) = count(sigma_i > tau(A)).
```

Every decision is repeated at multipliers `0.25`, `1`, and `4`. Derived
restrictions `T=A Q` inherit the multiplier-one parent scale
`sigma_max(A)`; their threshold is never rescaled by a near-zero
`sigma_max(T)`. In particular, `H_w Q_N` inherits the scale of `H_w`, and
`Y_R`/`Y_R_C` inherit the scale one of their nonzero parent quotient
projector.

The residual acceptance rule remains unchanged at all three SVD multipliers:

```text
r_tol(d) = 4096 d eps64.
```

Projector symmetry, idempotence, trace, containment, orthogonality, operator
annihilation, mapped-intersection agreement, and quotient reconstruction are
checked at every multiplier. A dimension change blocks a categorical claim.
Projector bases are derived from projector columns with the registered
two-pass pivot procedure, not from selected or visually interpreted SVD
vectors.

## Exact algebraic counterexamples

### Quotient-image counterexample

The frozen two-dimensional case is

```text
N = R^2,
G = span([0,1]^T),
P = span([1,0]^T),
R_N = span([1,1]^T).
```

At all three sensitivity multipliers the reproduced result is

```text
dim(R_N intersect P) = 0,
dim(R_N intersect G) = 0,
rank(Pi_P Q_R_N) = 1,
dim(Z) = 0.
```

The augmented intersection is exactly commutative in this case. This is an
exact algebraic counterexample to using raw `R_N intersect P` as the rigid
quotient image.

### Inherited-scale counterexample

For

```text
A_delta = diag(1,delta),
Q = [0,1]^T,
delta in {0,2^-60,2^-40,1},
s_A = 1,
```

the inherited-parent rule gives ranks `(0,0,1,1)` at each of `0.25`, `1`, and
`4` times the registered threshold. A threshold rescaled only by the
restriction's own singular value instead reports rank one for `delta=2^-60`.
The permanent regression detects that relative-only failure.

## Deterministic formulation evidence

The following values are deterministic evidence in the registered runtime;
they are not production-policy choices.

### Local elements

| Case | rank(B) | N | G | P | R_N | RQ | Z | sensitivity |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| square, uniform | 16 | 8 | 1 | 7 | 6 | 6 | 1 | stable |
| affine/skew, uniform | 16 | 8 | 1 | 7 | 6 | 6 | 1 | stable |
| tapered, nonuniform thickness | 17 | 7 | 1 | 6 | 6 | 6 | 0 | stable |
| distorted, varied directors | 17 | 7 | 1 | 6 | 6 | 6 | 0 | stable |
| warped, varied directors | 17 | 7 | 1 | 6 | 6 | 6 | 0 | stable |

Cyclic and anchored-reversal variants reproduce the corresponding subspace
projectors after DOF pullback. The largest reported numbering-projector
residual in the full registered catalog is below `4.0e-14`, within the frozen
residual gate.

On the flat square, the scalar constant drill candidate is in both `ker(B_w)`
and `ker(H_w)`. The alternating candidate is strain-null but has positive
mass participation (`H` residual approximately `0.8164965809277258`), and is
therefore not gauge. The corrected square partition is
`(N,G,P,R_N,RQ,Z)=(8,1,7,6,6,1)`.

For the varied-director distorted and warped cases, the visually constant
nodal scalar-drill candidate is not itself strain-null, even though the full
algebra still finds a one-dimensional `G`. No individual mixed numerical
basis vector is assigned a physical label by inspection.

### Assembled topology

| Topology | rank(B) | N | G | P | R_N | RQ | Z | categorical status |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| one element | 16 | 8 | 1 | 7 | 6 | 6 | 1 | stable |
| two shared-edge elements | 28 | 8 | 1 | 7 | 6 | 6 | 1 | stable |
| regular 2x2 | 46 | 8 | 1 | 7 | 6 | 6 | 1 | stable |
| odd-cycle prism | 29 | 7 | 1 | 6 | 6 | 6 | 0 | stable |
| distorted flat patch | 29 | 7 | 1 | 6 | 6 | 6 | 0 | stable |
| curved/warped patch | 29 | 7 | 1 | 6 | 5 | 5 | 1 | **blocked: threshold-sensitive** |
| two disconnected elements | 32 | 16 | 2 | 14 | 12 | 12 | 2 | stable |
| positively softened two-element patch | 28 | 8 | 1 | 7 | 6 | 6 | 1 | stable |
| deletion-created split | 32 | 16 | 2 | 14 | 12 | 12 | 2 | stable |
| deletion-created four-node orphan set | 16 | 32 | 25 | 7 | 6 | 6 | 1 | stable |

The odd-cycle connectivity is non-bipartite, so the oracle does not invent an
alternating candidate. Connected flat bipartite grids exhibit the familiar
positive-mass alternating strain null where their exact element maps support
it. Distortion or curvature can refute that candidate algebraically even when
the connectivity graph is bipartite.

Positive nonzero activity scaling changes the registered weighted metric but
does not change topology or act as a constraint. Deletion removes element
rows and incidence while preserving the declared global node/DOF universe.
For the orphan fixture, 24 orphan coordinates plus the retained element gauge
give `G=25`; fixing one orphan drill coordinate gives constrained
`N_C=31,G_C=24,P_C=7,L_C=30,L_G_C=24,RQ_C=6,Z_C=1`.

The curved/warped fixture changes a subspace dimension within the registered
SVD threshold band. Its multiplier-one values are retained as reproducible
numerical evidence, but no categorical physical interpretation is made.

### Supports, MPCs, and abstract coupling

On the two-element flat patch, every declared constraint matrix has rank one.
Rows that break the local gauge (fixed drill, weighted affine, and the tangent
of the inconsistent affine pair) give

```text
N_C=7, G_C=0, P_C=7, L_C=6, L_G_C=0, RQ_C=6, Z_C=1.
```

Rows that preserve the gauge (tied drill, dependent/redundant tied rows, and
the two abstract coupling rows) give

```text
N_C=7, G_C=1, P_C=6, L_C=7, L_G_C=1, RQ_C=6, Z_C=0.
```

The weighted affine row is feasible. The inconsistent affine pair is reported
infeasible while retaining its separate homogeneous tangent semantics. The
abstract shell/shell and beam/shell matrices demonstrate only the declared
work-conjugate algebra; they do not validate a production coupling.

## Reproducibility evidence

The full registered light catalog contains two algebraic cases, twelve local
base/numbering cases, and ten topology cases. In the accepted local runtime:

- cases JSON SHA-256:
  `223C0E1A1F03D30AA5EFBB13E8ECD8F64E5F7F0865E6F11274577D15C6691ABF`;
- exact environment-manifest SHA-256:
  `8EC3966B8AB8A72A304A4B340E6F18BAC6506391A877C9BB7510C0251295417D`;
- two standalone full normalized summaries were byte-identical at 23,003
  bytes including the terminal LF, with SHA-256
  `07E31EDC86ACBAC5073CCC1FD1138CB89271643110297D533423592AF47A1F22`;
- every checkerboard candidate classified by the oracle is either
  positive-mass strain-null or not strain-null, never gauge;
- the focused clean-process worker completed all 13 internal checks.

Snapshot hashes are exact reproducibility identities only when the complete
environment-manifest hashes match. Cross-environment scientific comparison
uses the frozen ranks, projectors, and residuals, not byte hashes.

The isolated numerical source identities are:

```text
protocol.py                32BF05E0BD0B282C49C47392CAF9400D2C8C136B9B6D1D398B3B54451EACB089
q4_common.py               DE2DCDCD3BC04A90A4DB2C074EC15D4E4B097123010F146A0C718506443C3D19
mitc4_plus_d_reference.py  AAF44046EEE607541F2A84EA16CBA948CB98130A568BBF8B5B03B243928E9536
mitc4_plus_d_scalar.py     9E3F1827F813546FF9C183C77E654F268C8A67F976B63FF010749EFDEAB3118B
```

## Claim classification and unresolved authority

Exact algebraic theorems in this packet are the definitions of `G`, `P`, the
augmented intersection, the rigid quotient image, the constrained `L_C`
construction, and the two-dimensional quotient counterexample.

Deterministic numerical evidence comprises the reported element/topology
ranks, projector dimensions/residuals, candidate classifications, activity /
deletion results, feasibility results, hashes, and repeatability observations.

Physical interpretation still requiring later authority includes whether and
how a true gauge is represented in a solve, and whether any positive-mass
mechanism receives a separately named and derived energetic formulation. The
positive-mass square checkerboard direction must not be constrained or called
gauge on the basis of this proof.

Unresolved items are the curved/warped fixture's threshold-sensitive
partition and every production meaning of the abstract coupling rows. Options
1, 2A, 2B, and 3 remain reserved. No result here relaxes the frozen rank gate,
changes the 113-claim contract, or authorizes integration.
