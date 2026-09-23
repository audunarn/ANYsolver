# F03 conforming Qp reference: signed recovery contract draft

23 September 2026. This is a preparatory contract for the independent
classical finite-pad reference. It is not a native B3-GE/E4-PL attachment,
a registered scientific run, a physical-convergence decision, or authority
to modify the failed F03 attempts. The physical panel, four pads, held
`J`, three beam-root pose constraints, load and support conditions are
unchanged from the original primal reference.

## Beam-side distribution

For a solved finite Qp field `u`, use the fixed-pad pose
`b(s)=A(u)(s)=(U,V,Theta)` and its first two station derivatives. Define

```
N = EA U'                 Q = GA (V' - Theta)          M = EI Theta'
d = (N', Q' + q_load, M' + Q)
alpha_0 = (N,Q,M)|_(0+) - eta
alpha_1 = -(N,Q,M)|_(1-)
```

The physical line density `d` has components `(N/m,N/m,N)` and endpoint
atoms have `(N,N,Nm)`. The root multiplier `eta` is included exactly once
in `alpha_0`; physical root support reaction is `-eta`, not `-alpha_0`.
The load is `q_load=F0(1+0.25 cos(2 pi s))` in the transverse beam
channel. At a shell-cell/pad crossing, evaluate `b''` one-sided. `b` and
`b'` remain continuous, so no extra beam atom occurs at an interior
crossing. Retain all represented positive station intervals, including
one-ulp intervals, and identify any limiting binary64 evaluation as a
numerical approximation.

For any admitted virtual shell field `z` with beam pose `w=A(z)`, the
required signed identity is

```
integral_0^1 d . w ds + alpha_0 . w(0) + alpha_1 . w(1)
  = integral_0^1 q_load w_y ds - a_b(b,w) - eta . w(0).
```

Check this independently for nonzero axial, transverse and yaw channels,
nonzero root and tip atoms, and positive/negative virtual fields. Comparing
`A.T` to `A` through the same matrix is not an independent physical-work
check. Keep the physical yaw moment and the represented `gamma=J_geom/J`.

## Shell-side distribution

For each rectangular Qp cell `K`, reconstruct the physical field and
its derivatives from shared nodal values. Let
`T=t D_plane eps(u)` be the symmetric membrane stress resultant and
`g_K=div T` in the cell interior. On an interior edge shared by `K+`
and `K-`, define the signed jump

```
j_e = T_+ n_+ + T_- n_-.
```

For any continuous virtual field `z`, including declared support lifts,

```
a_s(u,z) = -sum_K integral_K g_K . z
           + integral_outer (T n) . z
           + sum_interior_e integral_e j_e . z.
```

Keep left/right support edges, top/bottom free edges, and internal edges
separate. Count each interior edge once with both opposing cell normals.
Check force and moment about one declared origin, not only scalar work.
The jumps are discrete residuals, not material-interface loads.

## Finite-pad area adjoint and complete residual

Only after the beam distribution has passed the signed work identity,
construct `f_mu=A*mu` from the line density and two atoms using the
fixed physical squares. At a shell point `(x,y)`, each horizontal pad
interval `[l,r]` contributes over beam stations
`a=max(0,x-r)`, `b=min(1,x-l)` when `b>a`:

```
f_x = 1_Y(y)/S [ integral_a^b d_x ds
                   - y/J integral_a^b d_theta ds ]
f_y = 1_Y(y)/S [ integral_a^b d_y ds
                   + (x integral_a^b d_theta ds
                      - integral_a^b s d_theta ds)/J ].
```

Add each endpoint atom once on its translated physical pad, with
`(alpha_x-y alpha_theta/J, alpha_y+(x-e)alpha_theta/J)/S` for endpoint
`e`. The area load has units `N/m²`. Piecewise station primitives must
split at every Qp trace crossing; the cosine load receives a separate
fixed quadrature comparison. Do not substitute a point or line traction
on the shell for this finite-area adjoint.

Global force, origin moment and virtual work must satisfy

```
integral_Omega f_mu,x = integral_I d_x + sum_e alpha_e,x
integral_Omega f_mu,y = integral_I d_y + sum_e alpha_e,y
integral_Omega (x f_mu,y-y f_mu,x)
  = integral_I (s d_y+gamma d_theta)
    + sum_e (e alpha_e,y+gamma alpha_e,theta)
integral_Omega f_mu . z = integral_I d . A(z)
                           + sum_e alpha_e . A(z)(e).
```

The displayed moment formula uses the registered four-pad arrangement,
whose offset centroid is zero. For a diagnostic translated-pad arrangement,
the physical origin moment also contains the corresponding offset-centroid
force terms, and `gamma` must be recomputed from that arrangement. The
preparatory area implementation integrates the smooth cosine load with an
analytic primitive and separately compares it with fixed 48/64-point rules.

For each cell, the physical strong residual is `r_K=g_K+f_mu`. The
complete virtual residual against supported `z` is

```
<mu,A z> - a_s(u,z)
  = sum_K integral_K r_K . z
    - integral_free (T n) . z
    - sum_interior_e integral_e j_e . z.
```

For a declared nonzero support lifting `z_e`, its reaction is
`R_e=a_s(u,z_e)-<mu,A z_e>` and includes the supported boundary term,
the cell residual, the free-edge traction and interior jumps by the same
integration-by-parts identity. At a finite Ritz level, boundary stress
alone is not generally this reaction. Compare six physical edge
liftings, signed wrenches and pointwise/weak interface quantities.

The identities above are algebraic and numerical-recovery prerequisites.
They cannot by themselves establish p/h convergence, a native exact
multiplier law, shell torque/drilling admissibility, F03 or G0B closure.
Before any one-use physical study, freeze exact source, case inventory,
normalization, absolute floors, quadrature, time/RSS limits, raw arrays,
adjudication and independent review. The older failed Ritz and F03
registrations remain immutable.
