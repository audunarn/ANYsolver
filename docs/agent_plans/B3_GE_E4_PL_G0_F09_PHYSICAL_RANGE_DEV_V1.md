# F09 physical-range scaling development record

26 September 2026. This is a bounded Level-A follow-up to `07cd0031`, not
F09 admission, G0 acceptance, or a change to the public B2 route. It retains
the existing 120 s / 2 GiB preparatory envelope and does not invoke G1.

## Prospective decision

Question: does positive diagonal scaling of the mixed elbow's 12 free
translation/rotation coordinates recover the small applied-force signal over
a declared area and stiffness-unit sweep, while preserving moment equilibrium
and explicitly rejecting unrepresentable scalings?

Competing explanations are (a) a local default-pivot/factorization failure
that finite positive coordinate scaling can repair, (b) a rounded assembly
whose weak-force response is already lost, and (c) a range in which the
required scale or matrix is unrepresentable in binary64. Use the existing
two-member physical B2 elbow, exact rational solve of its assembled rounded
matrix, and the separate rational cut-wrench/force-method energy derivative.
For each case compare tip translations and rotations with both oracles and
separate free-force and free-moment residuals against their own applied
scales. Include an explicit range rejection. Scaling is a viable development
route only if the bounded finite cases agree with both oracles and close both
residual classes; a force-only residual or an exact-rounded/physical split
instead directs work to assembly or representability. Any failure remains
evidence, with no automatic expansion of this sweep.

The sweep and thresholds are declared in the dedicated probe. Results and
remaining limits will be added here after the focused execution.

## Result and decision

Source base: `07cd003126c1be9f60013e42948e9a56baf02535`. Probe:
`scripts/probe_b3_ge_e4_pl_g0_f09_physical_range.py`, SHA-256
`36caa2e9ec02940842d3cd7ed7bc7c9a711c6b4a4c84b8e8d031fd5235d2a21d`.
Raw record: `B3_GE_E4_PL_G0_F09_PHYSICAL_RANGE_DEV_V1.json`, SHA-256
`5343cfb9125f59acaae84e17882f48f5183c339cc0e41fa1f7df6f27321e133b`.
Command: `python -B -u scripts/probe_b3_ge_e4_pl_g0_f09_physical_range.py
--output <temporary evidence path>`; the resulting JSON was copied unchanged
into this record's directory. Python 3.14.2, NumPy 2.4.6, SciPy 1.17.1,
Windows. The final six-case calculation took 0.20 s; this is not a benchmark.

All six declared finite cases passed the diagnostic `1e-9` componentwise tip
and separate residual thresholds. The largest of scaled-vs-physical,
scaled-vs-exact-rounded, and exact-rounded-vs-physical componentwise tip
ratios was `1.12e-15`; the maximum free-force residual relative to the
largest applied force was `8.67e-16`, and the analogous free-moment ratio
was `7.76e-16`. The probe uses the private operator to assemble the rounded
graph, an exact rational solve of that rounded graph, and a separate exact
cut-wrench Castigliano derivative using the physical section compliance.
The latter does not reuse the element matrix. Area samples are `1e-4`,
`1e-8`, `2^-40`, and `2^-80` m² at E=1 Pa, plus `1e-8` and `2^-80` m² at
E=210 GPa, with forces/couples scaled by E. Thus the SI-paired responses
test a stiffness/load-unit rescaling while retaining the same geometry and
anisotropy. The diagnostic tip floor is 1 m or 1 rad, not an admitted
physical tolerance.

The transform is `D=diag(K_free)^(-1/2)` with distinct work-conjugate
translation and rotation units. Before factorization, the probe requires
finite positive diagonal, finite transform/matrix/load, no erased nonzero
coupling, and a representable unit diagonal. A zero diagonal is rejected.
An otherwise positive-definite two-row matrix with a minimum-subnormal
off-diagonal and `1e308` diagonals is also rejected when scaling erases that
coupling. These negatives demonstrate explicit representability handling;
they do not prove the current product has a complete typed admission rule.

Focused existing mechanics check: 27/27 passed in 3.05 s for the private
flexibility, definition, trace, and oriented-graph suites. The test runner
loaded the two private modules via a minimal package path, avoiding the
unrelated full package initializer; the initial full-package pytest import
did not reach test collection within 120 s and was stopped without claiming
a test result.

**Decision:** positive diagonal scaling is a feasible development route for
this bounded mixed graph across the declared numerical/SI stiffness samples.
It recovers both weak-force and moment signals without an artificial floor.
The fixed `Iy=Iz=J=1 m^4` with vanishing areas is intentionally a numerical
stress family, not a geometrically realizable section range. These six
samples do not freeze F09 physical admission, prove uniform conditioning,
cover generalized coupling or shell attachment, or close G0B. The next
production candidate needs a separately defined physical section range,
more graph/connection geometries, and product-level typed representability.
