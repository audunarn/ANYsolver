# Candidate E1-R planar regularizer derivation

## Element block

Let `c>=0` and define the four-node normal-rotation block by diagonal entries
`c` and off-diagonal entries `-c/3`.  Algebraically,

```text
R4(c)=(4c/3)(I4-1 1^T/4).
```

It is symmetric, has zero row and column sums, and has eigenvalues
`{0,4c/3,4c/3,4c/3}`.  A leading 3 by 3 minor is `16c^3/27`; therefore its
rank is three for positive `c`, and its kernel is exactly the constant vector.
No term couples a drill coordinate to ground.

For stiffness, `c=10^-8 trace(K_theta_theta^mat)/12`, where the trace is taken
from the condensed physical material tangent before geometric stiffness,
constraints, supports, MPCs, or artificial terms.  The trace makes the scale
invariant under orthogonal changes of the rotational frame.  Projection onto
a common planar normal makes the assembled block objective; reversing that
normal negates both projection maps and leaves the quadratic form unchanged.

## Component gauge

On a connected active Q4 component, the assembled regularizer energy is a sum
of element energies.  It vanishes only when every element's four projected
drills are equal.  Edge connectivity then makes that value constant over the
whole component.  With `w_i=sum_e A_e/4`, the functional

```text
g_C(theta)=sum_i w_i (theta_i dot n_C)
```

is nonzero on that constant vector and removes exactly one component gauge.
It is unchanged as a zero set by normal reversal and covariant under a global
rigid frame change.

For several components collect their constant-drill vectors as columns of
`Z`.  Existing homogeneous support/MPC rows `A` remove `rank(AZ)` combinations.
Let `S` be a canonical exact basis of `ker(AZ)` and let the columns of `W` be
the component area-weighted covectors.  Add exactly
`H=S^T W^T`.  Since `W^T Z` is the positive diagonal matrix of component
areas, `H Z S` is positive definite and removes precisely the surviving gauge
combinations.  This handles cross-component pure-drill MPCs without deciding
components independently.  Constraints mixing drill and physical coordinates
are ineligible in E1-R v1.  Activity and hard deletion rebuild both the
component graph and the weights; zero-scaled elements disconnect, while every
positive scale remains connected.

## Non-intrusion and conditional mass

An eligible host has block form `diag(K_phys,0)` in physical and drill
coordinates, with zero drill load and zero drill geometric stiffness.  Adding
`R4(c)` and the component gauge changes only the drill equations; physical
static solutions and the physical buckling pencil are therefore identical.
If the host contains physical/drill coupling or must transfer a normal drill
moment, E1-R is ineligible.

The mass analogue uses
`cM=10^-12 trace(M_theta_theta^phys)/12` and the same projector.  It is
symmetric PSD, has zero resultant under common drill, and cannot alter total
translational mass.  It is used only when an exact pre-audit proves a relative
drill mass singularity.  The current legacy shell already assigns positive
rotary inertia to all three rotation axes, so the mass branch is not applied
to that host.  No modal or transient property is qualified.

E1-R supplies numerical diagnostics only.  It is excluded from physical
resultants, stresses, yielding, fatigue, recovery, external loads, and
geometric stiffness.

The stiffness scale is computed from the unscaled physical element tangent.
Existing positive activity scaling is applied exactly once to the combined
physical-plus-regularizer contribution.  Computing the mean after activity
scaling and scaling the result again is forbidden because it would produce an
activity-squared term.  The `trace(M_theta_theta)/12` rule is the independently
frozen E1-R mass interpretation of the documented analogous pattern; it is
not represented as a byte-exact Sestra implementation detail.
