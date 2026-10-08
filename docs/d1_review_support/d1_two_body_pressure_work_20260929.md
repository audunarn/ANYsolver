# D1 two-body pressure-work null preflight — development result

## Question and bound

Independent review found no pressure-space acceptance candidate from the
fixed-target scalar results alone. This check asks one narrower question at
the accepted slide (step 4) and recontact (step 7) states of the existing
four-Q4/two-deformable-S3 eight-step cycle: can a nonzero supported Q1 pressure
combination do exactly zero work on all free structural coordinates?

The optional mode of the existing cycle runner repeats that ordinary nonlinear
path, removes the two prescribed `ux` controls from the constraint transform,
and forms complete two-body work `B = diag(S) D(gbar) T` at each accepted pose.
It uses the contact-free consistent structural tangent in those coordinates.
An independent current-skin overlap integrator supplies pressure support,
weighted gap and Q1 Gram. The normal law, mesh, loads and solver are unchanged.

## Result

| Check | Slide, step 4 | Recontact, step 7 |
|---|---:|---:|
| Positive-pressure modes | 2/10 | 2/10 |
| Independent support relative difference | 2.43e−14 | 1.69e−15 |
| Independent gap maximum difference | 7.06e−13 m | 2.16e−13 m |
| Independent Gram relative difference | 5.16e−14 | 2.37e−15 |
| Full supported constrained-work rank | 10/10 | 10/10 |
| Smallest/largest row-scaled singular value | 0.00197893 | 0.00197893 |
| Structural tangent relative skew | 3.41e−17 | 3.41e−17 |
| Scaled structural energy minimum eigenvalue | 0.05284 | 0.05284 |

Full supported work has robust numerical row rank at these two saved poses,
with a declared `1e−10` relative singular-value rank threshold. Consequently,
no nonzero pressure vector in this ten-mode space, including one-sided
active/front perturbations, is a **numerically resolved** work null. The two
positive-pressure modes are independently ranked 2/2. A relaxed near-front
screen includes all ten supported modes and adds no independent conclusion.
The earlier sign-constrained LP implementation was removed because full-space
injectivity already answers the posed null question, and its unused
rank-deficient branch had an unresolved-status defect.

This is local finite-grid independence, not a mesh-uniform stability estimate.
The dimensional compliance/Gram eigenvalues in the raw output have no
registered acceptance threshold. The result does not verify a changing front,
pressure-field convergence, two-body spatial accuracy, or the required ≤2%
integrated-response gate. D1 remains unaccepted.

Independent review confirmed the limited rank interpretation and identified
that the first version reported oracle discrepancies without failing on them.
The final mode now rejects a changed support, gap, Gram, or structural metric
at explicit numerical thresholds before reporting its result. Its capped
replay took 20.53 seconds and sampled 337.03 MB process-tree RSS, below the
180-second/1-GB development cap. It imports the isolated worktree at source
commit `381dc8f3`. [Guarded raw result](d1_two_body_pressure_work_guarded_20260929.json),
[resource record](d1_two_body_pressure_work_guarded_resource_20260929.json) and
[log](d1_two_body_pressure_work_guarded_log_20260929.txt) retain the run. The
[pre-guard result](d1_two_body_pressure_work_final_20260929.json) and its
[resource record](d1_two_body_pressure_work_final_resource_20260929.json)
remain development history. The
[first probe](d1_two_body_pressure_cone_20260929.json), its
[resource record](d1_two_body_pressure_cone_resource_20260929.json) and
[log](d1_two_body_pressure_cone_log_20260929.txt) are retained as development
history. SHA-256: guarded runner
`103E866B7D46E4FABDA8FC405489D0FEB2FCB7753992AD1D7D850A4CF8CA026A`;
guarded raw `12174A62B1448CA986EED6AF5B72651A1A7E7EAD75B6ED0FD1404532DF3CE34E`.

**Decision:** A numerically resolved physical pressure-work null at these two
states is ruled out under the stated rank and oracle tolerances.
The next claim-bearing design still needs an independent nonlinear two-body
partial-front response reference and a prospectively frozen mesh/front pair
under the unchanged response, gap, integration, equilibrium and wrench gates.
Do not rerun a larger coupled mesh merely to extend this rank result.
