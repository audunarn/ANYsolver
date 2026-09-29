# D1 cut-weighted pressure-jump screen

**29 September 2026. Algebraic development screen; no contact law changed.**
Source before this note: `dcb21106`. The exact two-hat Q4/S3 cut-front
counterexample and its accepted failure record remain the discriminator.

## Decision question

The earlier full-reference Q1 gradient-jump matrix `J` is positive
semidefinite and annihilates affine/bilinear pressure, but its work on the
two-hat mode remains `O(1)` as the overlap strip shrinks. Can support weighting
make that work comparable to the physical `O(theta^4)` squared dual response
without penalizing constant traction?

For the same four-by-two source grid and overlap `0 <= y <= 1+theta`, let
`M_i = integral_overlap N_i dA`, `M_i_ref = integral_source N_i dA`, and
`W = diag(M_i/M_i_ref)`. On the three source y rows, the ratios are
`1`, `0.5+theta-theta^2/2`, and `theta^2`. Define the nodal polynomial matrix
`A=[1,x,y,xy]` and the support-weighted projection

```
P = A (A^T diag(M) A)^-1 A^T diag(M),   Q = I-P,
S = Q^T W J W Q.
```

`S` is symmetric positive semidefinite by construction and annihilates the
four represented bilinear pressure fields. These properties do not establish
contact consistency. `J` has units m^2; a coefficient with units m/Pa would
be needed to add `S*lambda` to the integrated-gap equation in m^3. No such
coefficient or altered contact law is selected here.

## Bounded result

The unprojected `W J W` gives the desired weak-mode order, but its quadratic
work on unit constant pressure is 0.0648 m^2 at `theta=.1` and 0.00121895
m^2 at `theta=.0125`: it fails the constant-traction patch condition.
Projection `Q` removes that defect in this fixture.

| theta | Two-hat `p^T S p` (m^2) | Divided by theta^4 | `||S A||` |
|---:|---:|---:|---:|
| .10000 | 5.45855236254e-4 | 5.45855 | 7.44e-16 |
| .05000 | 3.79069855961e-5 | 6.06512 | 7.12e-16 |
| .02500 | 2.53324567065e-6 | 6.48511 | 5.82e-16 |
| .01250 | 1.64585736777e-7 | 6.74143 | 5.52e-16 |
| .00625 | 1.05049516395e-8 | 6.88453 | 6.20e-16 |

The smallest computed eigenvalue in this execution was `-2.41e-16`,
consistent with roundoff around an exactly semidefinite matrix; an independent
reconstruction obtained a slightly different roundoff minimum. The
support-weighted four-field projection Gram condition estimate remains
89.8–95.1. Additional `theta=1e-3,1e-4,1e-5` evaluations give normalized
two-hat work 7.01364, 7.03666 and 7.03898, respectively. These are
fixed-family observations, not a uniform bound or coupled response.

At the tested cuts, the 15-by-15 `S` has numerical rank 11 at a
`1e-10` relative eigenvalue threshold, leaving the four represented
bilinear fields as its observed nullspace. Its smallest positive eigenvalue
decreases from `1.91e-5` at `theta=.1` to `4.66e-9` at `.0125`, approximately
with `theta^4`. This is **not** an inf-sup result: the comparison norm for
physical pressure response and arbitrary cut geometries has not been set.

Independent algebraic review found no material formula error and reproduced
the two-hat values. For this positive-support grid, `J` has nullspace
`span(A)`, so the nullspace of `S` is also exactly `span(A)`: if
`W Q p = A c` lies in the nullspace of `J`, then
`A^T diag(M) Q p = A^T diag(M_ref) A c = 0`. The full-reference Gram is
positive definite, hence `c=0`, `Q p=0`, and `p` is represented by `A`.
This exact fixed-grid rank result does not supply a uniform physical
pressure-work bound.

This uses the unchanged independent pressure-grid construction in
[`d1_jump_stabilization_screen.py`](d1_jump_stabilization_screen.py), with
the displayed `M`, `W`, `P`, and `S` evaluated in NumPy 2.4.6 / Python
3.14.2. It does not call ANYsolver's contact kernel or change its source.

## Disposition

The projection is an **unqualified cut-aware stabilization lead**. It keeps
the represented bilinear Q4 skin and every positive-support fine-Q1 pressure
hat, but `S*lambda` would change finite-dimensional active complementarity.
The exact-law no-go result still applies. Before implementing this lead,
derive its continuum consistency, physical coefficient and moving-overlap
derivatives; check supported-mode rank, edge/partial patches, traction moments,
nonnegative pressure, small-cut limits, two-body work, and response against
independent references. Rank loss of `A^T diag(M) A` on a degenerate support
must fail explicitly rather than remove small supported hats. The screen is
neither a D1 acceptance result nor evidence of a speed improvement.
