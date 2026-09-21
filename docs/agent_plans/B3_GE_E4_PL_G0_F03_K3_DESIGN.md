# F03-K3: physical P0 line-space comparison

21 September 2026. **Design before registration; no mechanics pass.**
K2P's P1 choices exhibit complementary adverse behavior under reciprocal
mesh ratios. K2L proves the coarse Q4 P1-beam rows eliminate its fitted
shell trace in one exact discrete case, while the shell-grid rows grow
with shell refinement. Test whether lower-dimensional exact P0 spaces
avoid that specific cause without creating unacceptable weak gaps,
oscillations or new response errors. This is a candidate comparison,
not production selection or F03/G0 acceptance.

Use the unchanged 26 K1 Q4/S3-V2D meshes, supported native retained
B3 and physical shell operators, poses, split integration and exact signed
KKT. Evaluate **P0-beam** (constant on every native beam half-cell) and
**P0-shell-grid** (constant on every clipped physical shell interval)
independently for each mesh. These are discontinuous multiplier
fields; the weak work is assembled exactly from their piecewise basis,
including segment boundaries. A derived *coarse-side hypothesis* chooses
the basis with fewer scalar cells at each mesh, breaking equal counts
toward beam-grid only when their knot sets coincide. It is reported
posthoc and cannot erase a failed constituent result. A genuine
biorthogonal dual mortar basis is not implied by either P0 choice.

Keep K2P's two unchanged continuum native lifted-y load densities,
`f0[1+.25cos(2πs)]` and `f0 sin(2πs)` N/m with `f0=1e6 N/m` and
`L0=1 m`; eight-point load integration on split segments and independent
twelve-point verification. Reuse the K2P physical stations, exact
full/condensed KKT, coordinate scales, support balance, weak and
pointwise gaps, shell energy, multiplier coefficients/jumps and parity
classification. Preserve K2P's `1e-10` forward-parity limit and other
frozen local numerical thresholds; a favorable backward residual never
waives it. Include 104 load slots unless a candidate is explicitly
preempted by a typed rank/mass/reference failure. Keep the K2P P1 data
immutable and compare only physically matching rows.

The P0 multiplier's derivative is zero inside a segment and its jump is
recorded; do not smooth it postsolve. Classify rank and load failures
atomically, without converting programming or ownership errors into
candidate nonconvergence. Record shells' physical energy and nine-station
traces, including `N_b=8,N_s=1` and `N_b=8,N_s=64`. The first checks
coarse suppression and nonzero shell work; the second checks shell-only
refinement and the P1 parity-open comparison. Three-level core trends
and the isolated reciprocal reach must remain distinct. No numerical
response is accepted against an external/analytical target in K3;
that independent reference remains mandatory.

Before one execution, freeze the clean source commit, unchanged K2P/K2L
predecessor evidence, exact two-space/26-mesh/two-load inventory, source
and dependency hashes, thread environment, a 1200 s external wall and
8 GiB sampled child-RSS limit, cold evidence path and full supervisor
grammar. Independently review the source/weak-form reuse and exact
candidate mapping before registration, then independently audit raw
loads, reactions, gaps, parity and trends after execution.

P0 could have a smaller multiplier dimension yet leave unrestrained
interface modes or poor work transfer. A small gap alone does not
validate moment transfer; a finite shell energy alone does not validate
the attachment. The actual native cell-yaw jump graph norm, finite
six-channel pose, shell director/shear/drilling and physical torque
mechanics still govern F03. No G1 production integration follows K3.
