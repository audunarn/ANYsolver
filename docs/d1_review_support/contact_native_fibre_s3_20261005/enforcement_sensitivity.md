# Physical-fibre curved/S3 enforcement discriminator — NONPASS

Prospective question: do the unchanged plastic fixture's integrated forces,
moments, tip and target displacements change by at most 2% from 1e7 to 2e7 Pa/m,
while retaining the existing 30um gap and equilibrium/integration gates?
The actual 1e7 checkpoint was reused; no coarse coupled solve was replayed.

## Actual result

The source coarse preflight passed (5.910s, 180359168B). Independent analytic
angular minimization with 65/129 axial samples and bracket refinement agreed at
-15.012400676um. The production whole-patch lower bound is -15.013083978um.
This sampling control supplements that enclosure; it does not certify a global
minimum. Restored checkpoint bytes were unchanged.

The installed 2e7 solve **failed** before accepting any target: Newton iteration
7 exhausted backtracking with nine geometry rejections. The last rejection was
`curved axial front bracket work uncertainty exceeds integration budget`.
Across the 34 saved geometry failures, energy uncertainty was at most
1.623e-20J and force uncertainty at most 1.110e-15N, but the scaled tangent
bound was 1.0102e-6 to 1.6004e-6, exceeding the unchanged 1e-6 limit.
No reaction/displacement comparison or enforcement-convergence result exists.
The failed test and complete diagnostics are retained, not counted as a pass.

The job finished in 4.937s, peak181395456B, within 120s/953MiB. Its 220 imported
modules came from the intended installed package; import-path errors were empty.
Unchanged production source is 5c724261, wheel SHA
50cff5fe9e52b68d25cd65d5f6dc46a946596db0d8f5e5d6ebff49db8a2adfc0.
See [summary](enforcement_summary.json). Raw logs, runtime, input hashes, full
rejection traces and the failed checkpoint remain at
C:/ANYworkspaceWork/contact_native_fibre_s3_20261005/candidate04.

## Disposition and next decision

Classification: geometry/integration admission, not evidence that the penalty
response itself fails to converge. Do not run 4e7 or repeat unchanged 2e7.
The root band retains a representation-uncertainty floor; merely increasing
root iterations cannot eliminate it. Examine whether complete mapped-gradient
bounds unnecessarily cover the whole circle rather than the declared angular
arc, and whether a rigorous restricted-arc bound materially resolves the issue.
Any proposed bound needs an independent enclosure check and local work/tangent
controls before another coupled solve. Otherwise address projection precision
or the verified uncertainty derivation; do not relax the tolerance or law.
Full C0–C9 and independent native/material acceptance remain incomplete.

## Supporting review of the proposed correction

The existing representative-station bound is ||a||+||B||2 for
G(alpha)=a+B(cos(alpha),sin(alpha)). For midpoint m and half-width delta<=pi/2,
a valid declared-arc bound is
||a+B u|| + sin(delta)||B v|| + (1-cos(delta))||B u||,
where u=(cos m,sin m), v=(-sin m,cos m). Add the existing whole-band axial
allowance and outward additive rounding based on uncancelled magnitudes; retain
the minimum with previous valid bounds. Wider arcs need suitable trigonometric
extrema bounds or the existing whole-circle fallback. Do not infer an arc from
the active-width union measure. Test asymmetric arcs, endpoints/interior,
complete-circle fallback, cancellation and all moving-normal/offset columns.
The scalar counterexample G=1+cos(alpha), alpha=pi±.3 gives whole-circle bound2
versus exact arc maximum1-cos(.3), illustrating the conservatism only.
This is same-family supporting scrutiny, not independent engineering acceptance.
