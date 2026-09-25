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

The kernel is not an analysis owner. It has no first-approach swept event
control, physical endpoint caps, beam–beam or beam–shell pairs, friction,
material transactions, restart or admitted public C3 profile. Its local
checks do not qualify engineering contact.
