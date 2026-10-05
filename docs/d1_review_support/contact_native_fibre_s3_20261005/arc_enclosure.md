# Conditional declared-arc root enclosure — development candidate

The full mapped gap gradient is affine in cos/sin at each axial station. Its
norm is now bounded on the declared material arc using the reviewed midpoint
formula, with additive uncancelled rounding and the existing whole-band axial
allowance. Wider arcs retain the circle enclosure. Moving-normal, offsets,
both-body maps and all tolerances remain intact.

An always-on prototype passed eight local checks but changed error diagnostics
and broke exact saved checkpoint replay. That failure is retained in
candidate05/arc_local_work. The integrated correction uses the tighter bound only
when the historical root error exhausts the budget. It reuses isolated bands and
stations without resetting the interval budget or changing passing evaluations.
Original accepted checkpoints therefore retain the original replay path.
Older code need not read future checkpoints that require the new refinement.

## Actual checks and result

Nine source controls pass10.100s; open checkpoint material recovery passes8.569s.
Ten unique installed controls pass17.014s/188420096B, including independent
partial-front work, directional derivatives, complete mixed tangent, scalar and
vector arc bounds, large moving-normal/offset maps, exact active replay and exact
open-chain recovery. Partial-front directional errors8.27e-10/1.45e-8 are below
1e-5. All525 production files match the wheel and all221 imported modules have
correct installed paths. WheelSHA
f67f64ceab7a6f5c0046238cee5c34e45ad8d6052798774e459a30bb71dd2fbc.

The new source2e7 coupled candidate still **fails** at iteration7, with zero
accepted targets,37 candidates and34 saved integration rejections. Thirty root
brackets use the refinement. Final tangent bound1.569736e-6 remains above1e-6;
energy5.064e-23J and force1.099e-15N are not limiting. Job47.185s/181383168B stays
inside120s/953MiB. No convergence or whole-route speedup claim follows; this
failed route costs more than the earlier early rejection. No unchanged retry or
4e7 solve was launched. See [summary](arc_enclosure_summary.json); all raw inputs,
logs, checkpoints, runtime and failure traces remain in
C:/ANYworkspaceWork/contact_native_fibre_s3_20261005/candidate05.

## Next discriminating correction

The tangent-error bound currently sums norms of true and approximate positive
leading integrals. If both scaled leading matrices A,B satisfy0<=A,B<=M I,
then -M I<=A-B<=M I, so ||A-B||2<=M, not2M. Complete mapped coordinates and
positive diagonal scaling preserve PSD by congruence. The non-PSD gap-Hessian
and once-spatial remainder still needs the sum bound. The candidate is therefore
sqrt(active)*k*area*width*angular_width*(g²+2depth*h), retaining rounding.

Before adopting, verify the common area/gradient/measure bound covers every true
axial point and the accepted positive16-point quadrature, including grazing
fallback angular masses. Supporting review finds the matrix inequality valid;
this is not independent engineering acceptance. Freeze the next correction and
its checks before any further coupled solve. Keep all mechanics/material inputs,
resource limits and the historical NONPASS records unchanged.
