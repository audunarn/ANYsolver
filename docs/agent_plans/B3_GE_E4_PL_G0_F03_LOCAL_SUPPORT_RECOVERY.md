# Supplemental local support-recovery actions

This is a bounded manufactured classical Qp diagnostic for `p=1,2,3`.
It adds a separate result and leaves the original `Recovery` object and its
`unavailable_p1` status untouched. It neither solves an equilibrium nor
accepts a scientific reference. Its `Action` outputs preserve rational and
held-frequency cosine terms; `decimal_value` is never an acceptance test.

For the left/right support interpolation `phi_side=a+b*x`, with edge
coordinate `e=-1/2` or `3/2`, the Q1-admissible origin rotation is
`z=(-y*phi_side,e*phi_side)`. It agrees with `(-y,x)` on its selected edge,
vanishes on the other, and the two side fields sum exactly to the rigid
rotation. Q2/Q3 retain the existing `phi_side*(-y,x)` lifts. Translation
lifts are unchanged. The Q1 finite-pad pose on each exact station chart is

```
Az = (0, e*(a+b*s), [e*b*X2+(a+b*s)*Y2]/J),
X2=dx^2+a_pad^2/3, Y2=dy^2+a_pad^2/3.
```

The code samples the admissible local nodal fields, multiplies actual exact
local shell stiffness matrices by the recovered local `q`, and sums all
cell actions on the six support lifts. The same exact pose tests give two
independent routes in edge force/moment units:

```
route1 = a_shell(q,z)+a_beam(Aq,Az)-l_beam(Az)+eta.Az(0),
route2 = a_shell(q,z)-<mu,Az>.
```

Their symbolic difference is reported without using equality as a substitute
for stationarity. The first global free-coordinate nodal hat is independently
extracted from the exact trace, its shell residual is read from the local
stiffness actions, and its two full route residuals are returned. Adding that
hat to one lift and reevaluating both routes yields separate shift deltas and
binding defects. A manufactured nonequilibrated state must be allowed to
show a nonzero shift residual.

The sum of side lifts gives actual represented force and origin-moment
identities. Both physical and represented moment observations are retained:

```
M_support-eta_theta+M_load = (1-gamma)*(integral Q ds-eta_theta),
M_support-gamma*eta_theta+M_load-(1-gamma)*integral Q ds = 0.
```

Here `gamma=Jgeom/J` uses the held represented constants. The first line
is a real physical imbalance and is never repaired by rescaling reaction.
The actual held-frequency transverse resultant and moment remain symbolic
`Action` values; differences from nominal `(F0,F0*L/2)` are separate.
The two force balances are reported with both actual and nominal load.

The factory explicitly bounds free DOFs, station intervals, conservative
operation/workspace estimates, and exact symbolic storage. Before creating
any new Action, a conservative storage inventory charges 160 live Action
slots at the full rational and per-interval coefficient cap, all six lift
poses, the first-free-coordinate trace, state, cuts and temporary route/shift
expressions. The actual retained total is checked against both this bound and
the caller cap; it includes the two actual-minus-nominal load Actions. A grid
without a real free coordinate is rejected because its required shift test
does not exist. Public lift construction strictly validates tuple/list cuts,
bounded positive intervals, side, integer channel and polynomial order before
dispatch. It rederives one
factory `Recovery` from the supplied grid and exact `q,eta` and checks the
pose, resultants, interface and endpoint fields before computing supplemental
work. This rebinding is reported as work, not as a physical solve or a new
scientific authority. Q1 evidence still needs independent review, a certified
Action enclosure and a registered supervised case before any qualification.
