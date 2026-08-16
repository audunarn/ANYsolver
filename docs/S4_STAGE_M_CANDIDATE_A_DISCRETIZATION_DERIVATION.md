# S4 Stage-M Candidate-A discretization derivation checkpoint

Status: proof-only blocked checkpoint. No Candidate-A mechanics equation has
been implemented or executed. Production activation remains unavailable.

## 1. Authority and frozen inputs

This record is governed by:

- full program raw SHA-256
  `17CB914002E362A5DB2B475981A46020C1F39E8BA5398B4A7BEC64C39EEEC4A7`;
- Stage-M plan raw SHA-256
  `4AE07F5954C9A2E6E6B002BEA24A9FC274B528D405EE6E5FCACE630893021E5B`;
- Candidate-A source/discretization addendum raw SHA-256
  `F05C643D28199AF4CB07B7E175F1674C2164ABC6D79F5F772260E94A9A3FD3AB`,
  committed as `2ab44817e50a72493bf55e129b52b4b2db41ce6c`;
- acquired-source amendment raw SHA-256
  `3A70FD3639A763ED5E34E8A0A8530FAF3FB944179EA190DC5660F8062A68EB73`,
  last changed by commit `d6784dc10dca405f900ac6a3ea91baf3c5c96d95`;
- Fox-Simo PDF raw SHA-256
  `A2075C06EB551FB317E09DF37E9BEFB6B525754A945EAC894F58F204CAB2D7D8`;
- immutable Candidate-B output raw SHA-256
  `3A26052DB79CE914FF8A1FCA7835F3B86C15F1D351754B45CA904753D8EFDA0D`,
  terminal `NO_GO_CANDIDATE_B`.

The current source snapshot is commit
`d6784dc10dca405f900ac6a3ea91baf3c5c96d95`, tree
`eead5098a68ae9e24f89e13c16d4f0bfe8c5430b`.

## 2. Formulation identity and source boundary

The source substantiates the continuum scalar constraint

```text
c(phi,Q) = <A1,Q^T a2> - <A2,Q^T a1> = 0
```

and its unregularized scalar-multiplier functional. It does not specify the
discrete Q4 primal interpolation, rotation interpolation, multiplier pair, or
quadrature. The present research candidate, if it becomes well-defined, must
therefore be separately named. It is not the literal Fox-Simo finite element
and it cannot rewrite the published 2025 MITC4+/D identity.

The intended composite is the immutable published MITC4+/D physical energy
restricted by a source-derived, unregularized holonomic constraint. It may use
only a mixed saddle system or an exact nullspace reduction:

```text
[ K + sum_a eta_a Hess(g_a)    C^T ] [dq  ] = -[r_q]
[ C                              0  ] [deta]    [g  ]

q = q_p + T q_hat,  range(T)=ker(C),
K_r=T^T K T,  M_r=T^T M T,  f_r=T^T f.
```

No penalty, regularization, `C^T C`, empirical coefficient, or invented drill
energy is admissible. The paper's Eqs. (49)-(50) and (55)-(56) remain excluded.

## 3. Fixed-lambda restriction

Let the source configuration be `(phi,Q,lambda)` and restrict it by the
constant inclusion

```text
i(q) = (phi_h(q), Q_h(q), lambda_e),
lambda_e > 0,
delta lambda = delta^2 lambda = grad(lambda_e) = 0.
```

Then

```text
d = lambda_e Q t0,
delta d = theta x d.
```

The scalar drill constraint is independent of `lambda`; its source
linearization has a zero `lambda` column. This makes fixed `lambda_e` an exact
restriction of the *constraint sector*. It does not establish equivalence
between the current five-component Reissner-Mindlin/section potential and the
source's extended primal potential.

Before this checkpoint can pass, a content-addressed derivation must freeze
whether the nondimensional director uses `lambda_e=1` or the physical director
uses `lambda_e=t_e/2`, then prove the surviving force, work, tangent, mass,
rotary inertia, load, generalized `A/B/D/As`, state, and recovery pullbacks.
Those conventions are not interchangeable.

Current result:

```text
UNCLASSIFIED_CANDIDATE_A_FIXED_LAMBDA_SPECIALIZATION
```

If an independent `lambda_h` is required, the terminal instead becomes
`BLOCKED_CANDIDATE_A_EXPANDED_PRIMAL_AMENDMENT_REQUIRED`; the 24-coordinate
rank theorem is then inapplicable.

## 4. Flat small-rotation constraint

Use the reference square `[-1,1]^2`, unit orthonormal covariants, node order

```text
1=(-1,-1), 2=(+1,-1), 3=(+1,+1), 4=(-1,+1),
```

and per-node coordinates

```text
[u,v,w,theta_x,theta_y,psi].
```

The source linearization is

```text
c_h = sum_i (N_i,s u_i - N_i,r v_i + 2 N_i psi_i)
    = u_,s - v_,r + 2 psi
    = 2 (psi - omega_3).
```

For a multiplier mode `m`, define the exact unweighted moment

```text
C_m q = integral_-1^1 integral_-1^1 m(r,s) c_h(r,s) dr ds.
```

Each row below is written as four six-coordinate node blocks:

```text
C_1 =
[-1,+1,0,0,0,+2 | -1,-1,0,0,0,+2 |
 +1,-1,0,0,0,+2 | +1,+1,0,0,0,+2]

C_rs =
[0,0,0,0,0,+2/9 | 0,0,0,0,0,-2/9 |
 0,0,0,0,0,+2/9 | 0,0,0,0,0,-2/9]

C_r =
[+1/3,0,0,0,0,-2/3 | -1/3,0,0,0,0,+2/3 |
 +1/3,0,0,0,0,+2/3 | -1/3,0,0,0,0,-2/3]

C_s =
[0,-1/3,0,0,0,-2/3 | 0,+1/3,0,0,0,-2/3 |
 0,-1/3,0,0,0,+2/3 | 0,+1/3,0,0,0,+2/3].
```

An opposite scalar-constraint orientation negates complete rows and is
equivalent, but one sign convention must remain frozen across assembly.

For a flat affine scale `A1=a e1`, `A2=a e2`, divide the raw constraint by
`a^2` before mixed-unit scaling:

```text
c_hat = u_,s/a - v_,r/a + 2 psi.
```

## 5. Exhaustive D4 rank-two catalog

In the exact basis `b=[1,r,s,rs]`, with the D4 generators, pullback action, and
L2 metric frozen in the governing addendum, the commuting M-self-adjoint
rank-two projector equations have exactly two images:

```text
candidate_a.d4.span_r_s:
  P_E=diag(0,1,1,0),
  basis=[sqrt(3)/2 r, sqrt(3)/2 s],
  C_E_raw=[C_r; C_s],
  C_E_M=[sqrt(3)/2 C_r; sqrt(3)/2 C_s].

candidate_a.d4.span_1_rs:
  P_AB=diag(1,0,0,1),
  basis=[1/2, 3/2 rs],
  C_AB_raw=[C_1; C_rs],
  C_AB_M=[1/2 C_1; 3/2 C_rs].
```

This enumeration is B-blind and preregisters no winner. Tensor 2x2 Gauss is
exact for every `m*c_h` term; symbolic integration and tensor 3x3 are the
required independent reproductions.

The `_raw` matrices are the unnormalized rational moment-row representatives
used by the exact row-space theorem. The `_M` matrices use the displayed
M-orthonormal multiplier modes and are the convention that a future physical
mixed-operator contract must use. The two forms have identical row spaces, but
their numerical row scaling and multiplier mass must never be interchanged
silently.

Both raw matrices have exact rank two and annihilate all six flat rigid
motions. Their pure-drill restrictions have

```text
ker(C_E|psi)  = span{1,rs},
ker(C_AB|psi) = span{r,s}.
```

These are polynomial patterns, not gauge classifications. Gauge and quotient
meaning still require the immutable B/H/rigid calculus.

For the frozen `rank(B)=16` and `B R=0`, the exact early gate for either pair
is

```text
rank(C)=2,
C R=0,
rank([B;C])=18,
rank(B T)=16,
T ker(B T)=range(R),
```

where `range(T)=ker(C)`. Passing this gate proves preservation of the complete
strain image; it does not alone prove nonlinear, topology-wide, or production
qualification.

No pair mechanics or rank classification has been executed because the
fixed-lambda and rotation prerequisites are not both closed.

## 6. Rotation-mapping checkpoint

Current `src/anysolver/corotational.py`, Git blob
`45cdeff56f5c94eb3963aa01ac11f24a6d28646c`, contains Rodrigues/logarithm
utilities and an element rigid-frame pullback, but it is not a pointwise
Fox-Simo `Q_h`:

- no rule interpolates `Q_h(r,s)` from four nodal rotations;
- solver updates remain additive rather than a frozen left/right
  multiplicative `SO(3)` update;
- the small-angle Rodrigues branch returns `I+skew(theta)`, which is not
  exactly orthogonal for nonzero `theta`;
- the logarithm has no history-continuous near-pi branch contract;
- no guard proves `det(tilde f)>0` or positive-polar uniqueness;
- the corotational frame tangent is not the source constraint Hessian/KKT
  tangent and uses numerical frame sensitivity.

The current nonlinear state/update path in
`src/anysolver/nonlinear_static.py`, Git blob
`9115aac9226a572654689fe2f88d04df758850e4`, also stores additive coordinates,
not committed nodal rotation matrices.

Current result:

```text
UNCLASSIFIED_CANDIDATE_A_ROTATION_MAPPING
```

A future pre-outcome contract must freeze `Q_i`, `Q_h(r,s)`, update side and
order, branch domain, reference-director relation, positive-polar rejection,
and exact first/second derivatives before any pair run.

## 7. Inf-sup and topology boundary

Local rank two yields a positive local singular value only after the primal
and multiplier metrics are fixed. It is not a uniform global inf-sup proof.
The future contract must define a quotient primal norm, multiplier L2 mass,
element-local versus shared multiplier topology, exact assembly, and a
shape-regular refinement family. It must certify a common positive lower
bound with exact or outward-interval evidence.

The same contract must freeze support/MPC feasibility, coupling, positive
activity, hard deletion, orphan removal, disconnected components,
noncoplanar/warped geometry, cyclic/reversal/frame/origin/scale covariance,
and force/mass/load/state/recovery pullbacks. Observed positive singular values
are not a proof and cannot select a pair.

## 8. Current terminal and authority

The prerequisite terminals are:

```text
fixed lambda: UNCLASSIFIED_CANDIDATE_A_FIXED_LAMBDA_SPECIALIZATION
rotation map: UNCLASSIFIED_CANDIDATE_A_ROTATION_MAPPING
pair catalog: NOT_RUN_PREREQUISITE_UNCLOSED
Candidate A:  BLOCKED_CANDIDATE_A_DISCRETIZATION_UNREGISTERED
Candidate B:  NO_GO_CANDIDATE_B
overall:      BLOCKED_CANDIDATE_A_DISCRETIZATION_UNREGISTERED
```

No scientific output, case result, pair winner, selector, production source,
activation, integration, push, publication, or cleanup is authorized by this
checkpoint.
