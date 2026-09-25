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
