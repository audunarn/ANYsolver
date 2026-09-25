# C3 native retained round-station geometry

`native_retained_station.py` is an internal geometry and virtual-work map for
an explicitly declared circular section on a native B3-GE half-cell. It uses
the same physical centerline map as the existing native line-load work. For
cell `c`, local coordinate `t`, current nodal high/low positions `x`, retained
cell rotation `U_c`, and curved-reference half-cell lift `h_c(t)`:

```text
r(t)       = (1-t) x_c + t x_(c+1) + U_c h_c(t)
x(t,alpha) = r(t) + U_c R_ref(xi) [0, a cos(alpha), a sin(alpha)]
```

The first reference-frame axis follows the oriented tangent; the other two
define the round section. The radius `a` is explicit and positive. The station
belongs to one open half-cell; element ends and the shared cell boundary are
rejected until their physical ownership rules are implemented.

The contact position varies with the authoritative nodal translations and
the retained cell rotation. At a fixed pose, a left spatial rotation
variation gives `delta x = delta theta × U_c(h_c + rho_ref)`. The 24-column
geometric Jacobian includes that internal block. Its 42-column generalized
embedding sets the final 18 constitutive/resultant columns exactly to zero.
Nodal rotation columns are zero at fixed retained cell rotations; the native
structural equations couple those rotations rather than a contact geometry
shortcut. This map must be assembled with the full structural and contact
blocks before any future condensation.

Five focused tests passed (`c3-native-retained-station-first.txt`): straight
and curved virgin positions, internal motion at fixed external nodes,
directional virtual work, rigid covariance, rejection of ambiguous features,
and Gauss-integrated centerline work matching the separate native line-load
gradient. The checks cover a material station and its local work map. They do
not establish a search bound, surface integration, contact law, nonlinear
analysis owner, shell coupling, history, restart, native dynamics, or C3
engineering acceptance.

## Retained round-centreline/plane penalty kernel

`native_retained_line_plane.py` adds a separate **line** penalty specialization
for the declared round radius against one fixed analytic plane. It uses
`g = n·(r-p) - a`, positive on separation, and integrates
`0.5 epsilon_line min(g,0)^2` over reference arc length. The line stiffness
has units N/m². It is not a surface-pressure or endpoint regularization.

The centered half-cell lift is quadratic in cell parameter at fixed retained
rotation, so the plane gap is quadratic. The kernel finds every interior
zero and integrates only the closed intervals. Four- and eight-point Gauss
rules drive an adaptive estimate for potential, force and tangent under
explicit dimensional tolerances and a finite visited-interval budget. Budget
exhaustion raises `MemoryError` without dropping contact.

It returns potential, a 42-coordinate residual and tangent, opposite beam
and plane forces/moments about the global origin, an independent quadratic
minimum gap, and integration counters/errors. Retained internal rotation
blocks include the curvature-lift second variation. The final 18
constitutive/resultant rows and columns are exactly zero.

The first focused run failed before mechanics because a NumPy quadrature
scalar crossed the exact station constructor; its log is retained as
`c3-native-retained-line-plane-first.txt`. Converting that internal value to
a binary64 scalar produced three passing kernel tests
(`c3-native-retained-line-plane-second.txt`). The final affected station and
line-kernel set passed eight tests (`c3-native-retained-line-plane-final.txt`):
analytic straight full/partial line force and energy, opening, curved retained
virtual work and smooth tangent, common rigid transformation, paired wrench,
and explicit integration-budget failure.

## One-beam retained static development owner

`native_retained_static.py` composes the existing native model owner and
retained generalized nodal-force equations with this plane kernel. It admits
exactly one generalized B3-GE beam and one fixed plane. All 42 local
generalized coordinates, including both retained cell rotations and 18
constitutive/resultant coordinates, remain in the coupled Newton solve. The
contact tangent receives the same spatial rotation correction as the native
structural tangent. Material history origins remain fixed during Newton and
backtracking; accepted history advances only after the coupled equilibrium
and declared endpoint gap checks pass.

The owner rejects initial interference, bounds iterations and backtracking,
and returns the last accepted target on failure. A curved clamped beam loaded
toward a supporting plane completed with 0.005804 N integrated contact
reaction, 0.178 mm maximum penetration against an explicit 1 mm development
budget, nonzero contact work on retained cell rotations, and a coupled
directional tangent error below 1e-8. The affected geometry, kernel and owner
tests passed 13/13 (`c3-native-retained-static-final.txt`). A failed second
target preserved the accepted first target, and a foreign element identity
was rejected.

The owner has a distinct versioned accepted-target checkpoint. Its current
fixed-plane swept candidate uses checkpoint V2, superseding the earlier
development-only V1. It binds
the native model/program/support identity, contact geometry and all numerical
settings. Resume authenticates the external bytes and replays every accepted
mechanical/material state against its prior committed history, coupled
equilibrium, endpoint gap and integrated contact summary. Full and split
continuation produce identical checkpoint bytes. Changed contact settings,
tampered records and live definition mutation are rejected. A failed later
target retains the last accepted checkpoint. See the runnable internal example
at `examples/general_contact_native_retained_plane.py`.

The affected 16 geometry/kernel/owner checks passed
(`c3-native-retained-checkpoint-final.txt`), and the example completed its
split restart (`c3-native-retained-checkpoint-example.txt`). The first
checkpoint development run failed when the native support identity, already
canonical bytes, was passed to the JSON canonicalizer; the final binding uses
its SHA-256 value. That failure is retained in
`c3-native-retained-checkpoint-first.txt`.

## Conservative trial-path gap bound

For each native Newton or backtracking update, the one-beam owner now bounds
the physical plane gap throughout the retained-coordinate path. Nodal
translations vary linearly in the line-search fraction. Each retained cell
rotation follows the owner's SO(3) exponential update. The normal-gap change
per unit fraction is bounded by the largest nodal normal translation plus
the rotation-angle norm times the maximum reference half-cell lift. At an
interval midpoint, the kernel evaluates the exact quadratic minimum over
both cells; subtracting half the interval's Lipschitz allowance and a
roundoff allowance gives a conservative lower bound. Intervals are bisected
until the declared penetration budget is certified. A finite explicit
interval budget triggers trial cutback or solve failure.

A curved-beam test holds both trial endpoints clear while retained rotation
drives the intermediate path through the plane; the bound rejects it. A
shorter safe path passes. The current V1/V2 candidate's affected 17 checks
passed (`c3-native-retained-swept-v1-final.txt`), and the full/split example
still matched (`c3-native-retained-swept-v1-example.txt`). The path check covers this
fixed-plane owner and its actual interpolation only. It does not establish
general first-contact event placement, moving obstacles or paired-body
swept search.

This remains an internal development route only. It has no complete
first-approach event control, prescribed-motion tool, endpoint caps, multiple
beams, beam–shell coupling, friction or admitted public C3 profile. The
existing native context has its own 120-second execution limit. These checks
do not qualify engineering contact or the general restart contract.
