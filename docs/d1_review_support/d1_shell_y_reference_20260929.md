# Transverse structural reference for saved shell pressure work — development

**Question.** At the saved 16×8 near-rim Q4/S3 pose, do additional source
structural motions in the transverse direction detect work from the *same*
153 physical Q1 pressure functions? The existing x-only references detect
additional work but are not saturated. The weakest active modes lie near the
partial-contact rim. No coupled equilibrium or pressure basis was changed.

The offline-only builder inserts the midpoint of each existing y cell,
giving a 16×16 Q4 source structural mesh. It interpolates the saved six
component source pose, copies the fixed target coordinates, prolongs the
coarse pressure field to 289 fine source nodes and maps the original second
prescribed `ux` control to fine row 2. The fine builder's unused path program
would control row 1; this probe instead compares the same physical saved-pose
admissible subspace. Independent read-only mechanics scrutiny found no
indexing or pressure-work defect before execution.

| Check | Measured result |
|---|---:|
| Source skin interpolation maximum | 2.48e−16 m |
| Pressure support relative L2 | 7.13e−16 |
| Normalized gap maximum difference | 3.15e−17 m |
| Prolongated pressure work relative Frobenius | 7.71e−9 |
| Minimum scaled coarse/fine structural energy eigenvalue | 0.001669 / 0.000894 |
| Fine response relative residual | 1.11e−14 |
| Active same-fine-energy squared response ratio, minimum | **0.732010** |
| Active same-fine-energy squared response ratio, maximum | 0.999997 |
| Active coarse/fine metric bridge | unity within about 2e−13 |
| Minimum scaled eigenvalue of fine minus restricted compliance | −6.14e−16 |
| Bounded run | 30.24 s / 228.47 MB sampled peak |

The work transfer is inside the predeclared 1e−8 guard, albeit closer to it
than the x-only checks. The structural energy metrics are positive, the
response solves are accurate, and the same-metric projector is positive
semidefinite to numerical precision. The 48 settled active pressure modes
therefore show additional detectable work under this one y-enriched source
structural reference. The earlier x2/x4 minima are 0.854752/0.794360;
these direction-specific references use different fine spaces, so their
numbers do not rank the importance of the two directions.

The full-supported fine compliance retains a null eigenvalue
(−4.29e−16 after diagonal scaling). The probe labels its result
`development_enriched_shell_reference_singular`, stops before writing a
separate `settled_active` section and exits 2. The active ratio above was
computed earlier in its `common_metric` section with an active positive-
definiteness guard. The resource wrapper's `completed` status means only
that the process ended before the cap; it is not a scientific pass. Independent
read-only review found the bounded active interpretation sound and advised
against rerunning solely to change output formatting.

[Raw result](d1_shell_common_metric_y2_20260929.json),
[console](d1_shell_common_metric_y2_log_20260929.txt) and
[resource record](d1_shell_common_metric_y2_resource_20260929.json) retain
the failed full-supported status. Run source: HEAD `f2d841b6` plus the
offline-only builder/probe changes; probe SHA-256
`ea7cb54e3b22992631f88a4e8dd46178f11cd15e106fdf6028d82946a5b2db14`.
The saved coupled field SHA-256 is
`8293e528837cc2a8a25444aa079944c9f8371f5a5b50280bb6dc91816d19b852`.

**Decision.** Stop separate axis sweeps. The result is a fixed-pose
pressure-work detection measurement, not pressure-space stability, reference
convergence, nonlinear two-body response or D1 acceptance. The next
pressure qualification design needs a common physical Q1 work map on both
deformable shells, independently enriched structural reference spaces in
both surface directions, a partial-front active-space rule and pressure-
space refinement. Preflight its cost and register the comparison before any
additional coupled mesh run.
