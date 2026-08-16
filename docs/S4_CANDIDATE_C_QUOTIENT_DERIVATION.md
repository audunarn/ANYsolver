# Candidate C global multiplier-quotient derivation

## 1. Candidate and local normalization

Candidate C retains the registered A2 primal moments and changes only the
representation of the multiplier gauge.  On a square cell of side `h`, set
`a=h/2`.  The normalized modes are

```text
m_1  = 1/2,
m_rs = (3/2) r s.
```

They are orthogonal in physical surface `L2`, and each has squared norm
`a^2`.  The `m_rs` row acts only on the four nodal drill rotations:

```text
(a^2/3) (+1,-1,+1,-1).
```

For an assembled raw matrix `C`, Candidate C uses the physical quotient
`Lambda/ker(C^T)` with the minimum-`L2` representative.  This leaves
`ker(C)` and `range(C^T)` unchanged.  The question is therefore whether the
smallest *positive* inf-sup value is bounded away from zero as the mesh is
refined.

## 2. Free structured family

Let `E` and `H` be the `(n+1) x n` signed incidence and unsigned sum maps from
cell coefficients to nodes.  Both have full column rank.  With multiplier
coefficients `(alpha,beta)`, the assembled transpose action has blocks

```text
alpha -> (a/2)(E tensor H) alpha,
        -(a/2)(H tensor E) alpha,
         a^2 (H tensor H) alpha,
beta  -> (a^2/3)(E tensor E) beta.
```

Consequently the free multiplier transpose is injective; there is no exact
dual gauge to remove.  Choose

```text
x_i=(i+1)(n-i),  beta=x tensor x,  alpha=0.
```

Direct summation gives, for every positive integer `n`,

```text
|x|^2  = n(n+1)(n+2)(n^2+2n+2)/30,
|E x|^2 = n(n+1)(n+2)/3.
```

The free consistent one-dimensional Q1 mass satisfies
`M_1 >= (h/6) I`, hence its tensor product satisfies
`M_psi >= (h^2/36) I`.  Combining the dual mass bound with the physical
multiplier norm `a |beta|` yields

```text
0 < beta_n_free <= 10/(n^2+2n+2) -> 0.
```

This alone disproves a mesh-independent positive inf-sup bound.

## 3. Fully clamped structured family

Let `D` and `S` be the `(n-1) x n` signed difference and unsigned sum maps at
the interior nodes.  The active transpose blocks are

```text
alpha -> (a/2)(D tensor S) alpha,
        -(a/2)(S tensor D) alpha,
         a^2 (S tensor S) alpha,
beta  -> (a^2/3)(D tensor D) beta.
```

With `one_i=1`, `z_i=(-1)^i`, and `r_i=i-(n-1)/2`, the complete dual kernel is

```text
{(0,beta_0): beta_0 in ker(D tensor D)}
 + span{(z tensor z,0)}
 + span{(one tensor one,-12 r tensor r)}.
```

Here `D r=one`, `S one=2 one`, and `S z=0`.  The kernel has dimension
`2n+1`, so the raw transpose rank is `2n^2-(2n+1)`.

For `n>=3`, define the symmetric zero-mean vector

```text
x_i=(i-(n-1)/2)^2-(n^2-1)/12,
beta=x tensor x,  alpha=0.
```

Because `x` has zero mean, it belongs to `range(D^T)` and `beta` is
orthogonal to `ker(D tensor D)`.  Symmetry gives `x dot r=0`, so the witness
is also orthogonal to the mixed kernel vector.  It is therefore the exact
minimum-`L2` representative of a nonzero quotient class.

Exact summation yields

```text
|x|^2   = n(n^2-1)(n^2-4)/180,
|D x|^2 = n(n-1)(n-2)/3,
|D x|^2/|x|^2 = 60/((n+1)(n+2)).
```

The clamped one-dimensional Q1 mass satisfies `M_1^I >= (h/3) I`.
Therefore

```text
0 < beta_n_clamped <= 30/((n+1)(n+2)) -> 0.
```

The failure is a positive near-kernel in the quotient, not an exact gauge.

## 4. Consequence and nonlinear boundary

Both admissible mesh families fail the necessary uniform inf-sup condition in
exact rational arithmetic.  Candidate C therefore receives
`NO_GO_CANDIDATE_C_QUOTIENT_INF_SUP`.

This quotient is only established for the flat linear bilinear form.  A
finite holonomic functional could descend to a fixed multiplier quotient only
if every quotient direction `k` satisfied `k^T g(q)=0` identically over the
admissible configuration set.  That stronger identity was neither assumed
nor tested because the exact linear failure already terminates the candidate.

No finite-rotation, nonlinear, precision-shard, performance, or production
claim follows from this proof.  The legacy production restriction remains
unchanged.
