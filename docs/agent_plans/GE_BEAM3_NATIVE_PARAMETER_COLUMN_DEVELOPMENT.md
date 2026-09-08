# Native generalized continuation load-column development

Base: ea5d57beea0652be67e37596708799e59bea409f.

Displacement/arc-length continuation needs the exact load derivative after
internal stationary elimination. Using only the nodal force vector omits the
cell rotation response to line forces and spatial couples. At fixed accepted
origin and external nodal pose, let b=-d(line work gradient)/dlambda-G_prime.
Solve J_ii y_i_prime=-b_i, then c=b_e+J_ei y_i_prime. Pull back the rotational
rows through the accepted-origin Exp Jacobian and subtract proportional nodal
spatial couples once per global node. Do not symmetrize J or use J_ie.T in
place of J_ei. This follows implicit differentiation of the existing retained
stationary equations; no finite differences enter production evaluation.

Add an independently callable private analytic column for issued native trials.
Bind exact model, trial token, issued state, complete state set and derivative
patterns; reject foreign/stale/mutated inputs and discard on failure. Never
advance an accepted material origin. Do not change existing element, shared
solver, state, recovery or load mechanics. No aliases/defaults/publication.

Before freezing, compare against separately re-solved parameter perturbations
at fixed external pose and accepted origin for straight elastic, curved plastic
and connected plastic fixtures. Use steps 2e-4, 1e-4 and 5e-5 and normalized
directional tolerance 1e-7. A closed Rodrigues formula supplies independent
nodal work mapping. Check active state and derivative input mutations.
Also check a committed plastic origin followed by unloading and a zero
derivative direction. Preserve the accepted origin and require exact zero.
Run the full rehearsal before two fresh-directory frozen replicas. Preserve
raw outputs and deterministic hashes. Keep inventories separate. All test
children are limited to 600 seconds, 24 GiB, one numerical thread and 120
seconds CPU inactivity; at most three children and 1800 seconds per wave.
No automatic worker retry; preserve failures and do not weaken tolerances.

This prerequisite does not close displacement/arc-length integration,
postbuckling, independent review or full qualification. Subsequent continuation
must use a genuine bordered solve, permit signed/nonmonotone load parameters,
preserve accepted-origin history and authenticate path/restart controls.
Existing force programmes remain unchanged and retain their current bounds.

## Preserved initial rehearsal incident

The first 12-node rehearsal had 10 passes and two test-observation failures:
the plastic-coverage assertion read a stale live trial view after perturbation
assemblies replaced its token. All three derivative-error assertions passed
before that assertion. Preserve the failed logs and initial three-source
snapshot externally. The correction copies the base trial before perturbing;
it changes no production code, formula, fixture, load or tolerance. The revised
inventory also adds accepted-origin/zero-direction coverage and records the
foreign-store rejection rather than returning without its diagnostic file.
