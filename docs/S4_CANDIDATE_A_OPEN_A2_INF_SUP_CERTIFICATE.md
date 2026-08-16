# Candidate-A2 exact inf-sup counterexample

Status: exact research certificate. Production and historical S4 artifacts are
unchanged.

## Frozen pair and patch

Candidate A2 is the already registered discontinuous element-local multiplier
space

```text
Lambda_A2|e = span{1/2, (3/2) r s}.
```

Use four affine Q4 cells in a consistently counter-clockwise `2 x 2` patch.
The nine nodes have coordinates `(2 i,2 j)`, `i,j in {0,1,2}`. Every cell is
a translated copy of `[-1,1]^2`, so its positive surface Jacobian is exactly
one. All six primal coordinates at the eight boundary nodes are clamped. The
only retained primal columns are

```text
[u,v,w,theta_x,theta_y,psi] at the centre node n11.
```

No multiplier row is removed or quotiented.

## Exact witness

For the normalized A2 `rs` mode, the accepted flat constraint moment has the
local drill row

```text
C_rs|psi = [ +1/3, -1/3, +1/3, -1/3 ]
```

in local Q4 node order `[bottom-left,bottom-right,top-right,top-left]`. Set the
constant-mode coefficient to zero and the normalized `rs` coefficient to one
on every element:

```text
mu_e = [0,1],  e in [e00,e10,e01,e11].
```

Before applying the boundary clamp, assembly leaves nonzero drill forces only
at the four corner nodes. Contributions at every edge-middle node cancel. At
the sole interior node, the four contributions are

```text
+1/3 - 1/3 - 1/3 + 1/3 = 0.
```

Removing the 48 clamped boundary columns therefore gives, exactly,

```text
C_adm^T mu = [0,0,0,0,0,0]^T.
```

The witness is nonzero. Because `(3/2)rs` has unit squared `L2` norm on each
cell and the multiplier is discontinuous, its patch norm is

```text
||mu||_Lambda^2 = 4 > 0.
```

For every admissible primal variation `v`, `b(v,mu)=mu^T C_adm v=0`.
Consequently, under any positive primal norm,

```text
inf_(nu != 0) sup_(v != 0)
    |nu^T C_adm v| / (||v||_V ||nu||_Lambda) = 0.
```

The full unquotiented discontinuous Candidate-A2 multiplier space therefore
has an exact zero inf-sup bound on this admissible patch:

```text
classification: PROVEN_FAIL_CANDIDATE_A2_INF_SUP
```

Quotienting the annihilator or deleting multiplier rows after inspecting
supports/topology would define a topology-dependent candidate. It is not this
registered A2 pair and is not authorized by this certificate.

## Machine certificate

The canonical exact record is
`docs/reference_cases/s4_candidate_a_open_a2_certificate.json` (SHA-256
`68691E4F1F23E23ED7DF00C4210436BDD1A730ADB58ED3E755E15CC01ECC5F3B`). All terminal arithmetic is reproduced with
`fractions.Fraction`; no floating-point rank or tolerance enters the result.
The regression also binds the accepted Candidate-A cases and derivation by
their canonical-LF SHA-256 identities, accepting a consistently CRLF-checked-out
worktree but rejecting lone or mixed carriage returns.
