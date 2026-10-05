# Actual tangent-owned rim: energy-space limitation

4 October 2026. Development disposition, not general contact qualification.

## Mathematical discriminator

A straight terminal B3 cell of length h has reference unit tangent t and a
perpendicular unit vector v. Impose transverse displacement
`delta r(s)=a*h*s*(s-1)*v`, with both endpoints and all nodal section rotations
fixed. The endpoint derivative changes from t to t+a*v, independently of h.
The admitted Timoshenko/vonKarman beam energy is

`U_h=h*(GA*a²/6+EA*a⁴/40)`.

This follows by integrating squared shear a²(2s-1)² and squared axial strain
a⁴(2s-1)⁴/4. There is no section bending/rotation in this variation. U_h tends
to zero while the normalised endpoint tangent changes by a fixed amount.

Take t=(b,0,sqrt(1-b²)), v=(-sqrt(1-b²),0,b), b=.02, a=-.003, fixed tip
(3,0,0), beam radius1m and an infinite z-axis cylinder of radius2.0003m. Its
strict active rim has the independent circle gap

`g(a)=3-(sqrt(1-b²)+a*b)/sqrt(1+a²)-2.0003`.

The cap penalty energy change `ke*(g(a)²-g(0)²)/2`, ke=1e5N/m, is a fixed
negative value. The curve derivative norm is at least1; its x component remains
positive. Full tube gaps remain inside the declared1e-3radius budget. Thus neither
regularity nor the geometric penetration budget excludes the variation.

## Observed bounded check

The one test integrates production structural virtual work over load amplitude
using an independent3-point Gauss rule. It compares that energy and production
rim gap/work with the separate expressions above; no coupled solve is run.

| h (m) | Structural energy (J) | Cap energy change (J) |
|---|---:|---:|
| .02 | 9.6154251e-9 | -4.36854215e-4 |
| .01 | 4.8077126e-9 | -4.36854215e-4 |
| .005 | 2.4038563e-9 | -4.36854215e-4 |

Source check1passed,2.232s,160628736B peak, JIT0/pools1,180s/953MiB cap.
Raw `C:/ANYworkspaceWork/contact_coupled_tool_staging_20261004/rim_energy_trace01`
retains inputs, output, runtime/import identities and resources. [Summary](summary.json)
binds its exact source/test/raw bytes. Existing installed package remains unchanged;
this additional test is source-only and is not counted among its73predicates.
Read-only scrutiny confirms the formula, production-work mapping and raw pass
with zero runtime/import errors. The terminal bubble can be embedded in a fixed
beam without changing neighbouring cells. The reference pose is already
penetrating: manager initialization, crossing and coupled equilibrium are not
executed or claimed. No replacement surface or general instability is admitted.

## Consequence and limits

Endpoint slope is not controlled as a trace by this H1-type structural energy.
This demonstrates an admissible sequence with vanishing cost for a nonvanishing
cap-orientation change. It does not prove divergence of every finite rim solve
or invalidate the guided single-cell code/work benchmark. It does prevent those
finite checks from establishing general free-rim continuum acceptance. C1
interpolation alone would not supply the missing energetic control.

Position-only sphere branches do not have this particular slope-trace defect.
Other tangent-dependent plane/sphere rim branches require the same mathematical
scrutiny; this executable discriminator covers the cylinder/B3 fixture only.

Keep the historical centreline-tube prototype and named discrete evidence scoped.
No stiffness retuning, added artificial bending or changed acceptance tolerance.
Bring forward the already required swept round material-section profile: its
orientation must use structural section coordinates, with complete work maps,
couples, surface velocity and its own declared geometry. Do not change an old
profile's cap law silently. Material-section trace control is a prerequisite to
check, not a pre-established qualification. Full D3/C0–C9 remains required.
