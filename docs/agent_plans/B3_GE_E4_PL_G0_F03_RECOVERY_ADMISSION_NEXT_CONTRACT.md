# Next bounded recovery-admission contract

22 September 2026. Independent read-only mechanics review by
`finite_pad_axis_review` identified the following implementation contract.
**This note records reviewed derivations and remaining work, not executed
qualification.** The current recovery helper, old evidence and unavailable
P1 recovery status remain unchanged.

## Certified actions and saved recovery

Add a separate bounded enclosure evaluator for the existing exact `Action`
representation. Leave `decimal_value` as a display function. Normalize exact
interval unions and polynomial restrictions before symbolic cancellation.
Use a fixed-order local-coordinate expansion with an explicit remainder and
exact rational or directed interval arithmetic. Freeze order/precision and
term, bit, work and memory limits; no automatic retry after a failed bound.
A saved-value comparison passes only when its worst-case enclosed error fits
the frozen tolerance. An interval straddling the threshold remains HOLD.

Bind saved piecewise density, cosine and both external atoms to the recovered
q, eta and exact traces. Preserve six polynomial coefficients per channel,
root/tip partition checks at `1e-11` and density checks at `1e-10`, using
the held force scale. Keep all original eight bands, including total and
line-only observations, signed origin moments and endpoint atoms exactly
once. Compare analytic enclosures with independently saved numerical band
values after division by F0, with limit `1e-10`.

Compare two edge-work routes for every admitted lift:

```
a_shell(q,z) + a_beam(Aq,Az) - l_beam(Az) + eta . Az(0)
a_shell(q,z) - <mu,Az>
```

Retain saved-row/action bindings and the separate route difference limit
`1e-8` after division by F0. Preserve the original first-free-coordinate
lift-shift residual check at the same scale. Equality between the two routes
does not prove stationarity or invariance under an admissible lift shift.

Freeze a complete bounded virtual-work inventory with amplitudes U0, U0 and
U0/ell. Require work discrepancy/E0 at most `1e-10`, including independent
saved-value binding. Feed the fully bound functional to the existing fixed
48/64 full-H1 norm check. Retain signed per-channel and total raw quantities,
both atoms and divide the physical third channel by ell once per operand.
No negative/zero repair.
The resolution threshold remains `1e-10` with the existing `1000^2` floor.
This is quadrature-resolution evidence, not a certified analytic Green-norm
error unless a separate enclosure is implemented and reviewed.

## Actual physical and represented adjoint balances

Preserve the held constants, including `gamma=Jgeom/J`, rather than assuming
gamma equals one. The shell rigid-origin-rotation test has pose
`A(-y,x)=(0,s,gamma)`. Write

```
Ttheta = <mu,(0,0,1)> = integral Q ds - eta_theta.
```

For the summed shell support moment M_shell and the physical beam-root
reaction `-eta_theta`, the represented law predicts

```
M_shell - eta_theta + M_load = (1-gamma)*Ttheta.
M_shell - gamma*eta_theta + M_load - (1-gamma)*integral Q ds = 0.
```

The first expression is the raw physical moment imbalance. The second is
the represented adjoint identity. Record both; do not silently rescale the
root reaction or subtract the predicted defect from physical acceptance.
Keep the original global force/moment balance tolerance. These identities
still require executable independent tests before use in an adjudicator.

Likewise the held frequency Omega is not exactly mathematical `2*pi/L`.
For distributed load `q0+qc*cos(Omega*s)`, the actual resultant and moment
are

```
F_load = q0*L + qc*sin(Omega*L)/Omega
M_load = q0*L^2/2 + qc*(L*sin(Omega*L)/Omega
                        + (cos(Omega*L)-1)/Omega^2).
```

Report the difference from the historical nominal `(F0,F0/2)` values
separately. It is a represented-load discrepancy, not recovery roundoff.
Preserve the nominal checks and add actual-load identities; do not change
the load operator or weaken either acceptance requirement.

## Admissible P1 support-recovery route

The current rotation lift `phi_side(x)*(-y,x)` is quadratic and cannot be
assumed Q1-admissible. A separately bound P1 family can use

```
z_side = (-y*phi_side(x), x_edge_side*phi_side(x)).
```

It lies in Q1, gives the same rigid-origin-rotation displacement on the
selected support edge, and vanishes on the other. Its two side lifts sum
exactly to `(-y,x)`. Translation lifts are unchanged. For `phi=a+b*x`,
`e=x_edge_side`, `X2=dx^2+a_pad^2/3`, `Y2=dy^2+a_pad^2/3`, its trace is

```
Az  = (0, e*(a+b*s), (e*b*X2+(a+b*s)*Y2)/J)
Az' = (0, e*b, b*Y2/J)
Az''= (0, 0, 0).
```

The difference from the current Q2 lift is `phi*(e-x)*e_y`, which is
boundary-zero but not Q1. Do not use Q1 stationarity to equate those lift
actions. For independent shifted-lift tests, use an actual supported global
Q1 nodal hat at an interior x node, a chosen y node and component, and bind
the change to that free-coordinate residual. Freeze the P1 lift identity
and prove both routes, shifts and summed balances before enabling recovery.
This changes virtual-lift selection, not equilibrium physics. It does not
waive the currently missing P1 evidence.
