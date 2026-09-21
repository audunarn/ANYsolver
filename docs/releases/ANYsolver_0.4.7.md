# ANYsolver 0.4.7: static, spectral and nonlinear performance

This release packages accepted improvements already merged into `main` after
0.4.6. It keeps the coordinated dependency bounds, qualified element
equations, physical tolerances and default formulations unchanged.

The representative complete static run improved from 6.7025 s to 1.6860 s
(3.98x), and a retained load-only run improved from 6.7025 s to 0.3376 s
(19.85x). The seven-pair retained medium-panel spectral gate improved from
5.4830 s to 4.8514 s (11.52%) with identical recorded modes and residuals.
The representative nonlinear gate improved its four non-easy cases by a 12.44%
median, with passing physical comparisons; the follower shell case alone was
0.96% slower in that gate. These results describe the declared workloads and
do not imply the same speedup for every model.

The nonlinear force-control solver can reuse guarded accepted internal forces
for reaction recovery and prepares fixed dead loads once. Trial promotion now
rechecks the recomputed residual. Diagnostics report accepted and failed work.
The runtime facade preserves constraints and nonlinear failure information when
forwarding locally edited models.

An optional `line_search="armijo"` is available for supported force-controlled
beam and shell solves. Its separate convergence promotion experiment was
**NO-GO**: it did not solve additional difficult cases or reduce failed work.
It remains opt-in and is not a recommended convergence improvement. The default
line-search policy is unchanged.

The bounded 0.4.7 gate checks the exact versioned wheel and source archive,
their runtime/source identity, an isolated installed import with production
dependency versions, the existing B3-GE opt-in boundary, and immutable accepted
performance evidence. CI separately covers the portable solver suite and
supported dependency integrations. This packaging gate does not rerun the
scientific performance campaigns.

Terminal on success:

`PROVISIONAL_GO_ANYSOLVER_0_4_7_BOUNDED_PERFORMANCE_RELEASE`

The terminal authorizes a separate publication decision for the exact 0.4.7
artifacts; it does not publish them automatically. Draft PR 57 and open PR 35
are not part of this release candidate.
