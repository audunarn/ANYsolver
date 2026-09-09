# Front-aware saved-energy inertia successor

Parent a6022eef1ee8af9ea42ea3a6c8d885c19e63f2a1. Preserve all prior failures,
factor captures, raw Hessian asymmetry and their original adjudication. No
mechanical capture, material, state, reference, recovery or public route changes.

Use the exact signed N24 factor packets and explicit energy-form interpretation
already bound in GE_BEAM3_SPATIAL_ENERGY_INERTIA_SUCCESSOR.md. Do not claim raw
exact tangent symmetry. No planar partition or coupling removal.

The prior selector picked a minimum-degree coordinate and sometimes eliminated
its more-connected neighbour. The successor searches admissible pivots and
minimizes their actual Schur-update front, with deterministic size/index ties.
A scalar pivot requires every multiplier magnitude <=2. A two-coordinate
pivot requires both components of every external multiplier magnitude <=2,
computed through the determinant without division during admission. No pivot
modification, dropping, weakened threshold or fallback after a failed process.

Background: HSL MA57 separates sparsity ordering from numerical pivot selection
and uses scalar/two-coordinate pivots for symmetric indefinite systems.
https://www.hsl.rl.ac.uk/specs/ma57.pdf
This is an independently implemented small standard-library checker, not MA57,
an interval certificate or independent authorship review. No HSL code/dependency.

Keep <=512 coordinates, max front96, <=2million Schur updates, growth<=1e12,
pivot floor scale*1e-50, full reverse-reconstruction relative<=1e-60, Decimal80/100
and internal120-second limit. Include actual pivot indices in diagnostics.
Test known signed congruences, badly scaled chains through438 coordinates,
small dense cross-checks, hub avoidance, two-coordinate pivots, tiny nonzero
coupling, singularity, asymmetry, nonfinite values, cancellation and fill bounds.

Freeze before positive80 smoke using the original saved factor packet. If it
passes, check positive100 and both negative precisions, then repeat all four in
fresh processes. Require byte-identical same-precision replicas and agreeing
sign counts/pivot indices between precisions. All launched workers must be
terminal before aggregate creation. A negative direction is an honest energetic
instability of that endpoint, not an automatically rejected formulation.

One thread per child, max3 concurrent, 600seconds/24GiB per process tree,
1800seconds per wave, unchanged120second inactivity watchdog, no retries.
Preserve raw logs and input/output hashes externally; no partial canonical
aggregate. Completion of this diagnostic does not close general postbuckling,
independent review, full parity or beam-shell qualification.
NO_GO_PRODUCTION_RESTRICTION_UNCHANGED.
